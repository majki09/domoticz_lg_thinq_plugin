#!/usr/bin/env python3

import wideq
import json
import time
import argparse
import sys
import re
import os.path
import logging

STATE_FILE_NAME = "wideq_state.json"
LOGGER = logging.getLogger("wideq.example")

# determine the wideq_state file location
# non-docker location
try:
    loc_to_try = ".//plugins//domoticz_lg_thinq_plugin//" + STATE_FILE_NAME
    with open(loc_to_try, 'r'):
        STATE_FILE = loc_to_try
        LOGGER.info("wideq_state file loaded from non-docker location.")
except IOError:
    # Synology NAS location
    try:
        loc_to_try = ".//var//plugins//domoticz_lg_thinq_plugin//" + STATE_FILE_NAME
        with open(loc_to_try, 'r'):
            STATE_FILE = loc_to_try
            LOGGER.info("wideq_state file loaded from Synology NAS location.")
    except IOError:
        # docker location
        try:
            loc_to_try = ".//userdata//plugins//domoticz_lg_thinq_plugin//" + STATE_FILE_NAME
            with open(loc_to_try, 'r'):
                STATE_FILE = loc_to_try
                LOGGER.info("wideq_state file loaded from docker location.")
        except IOError:
            STATE_FILE = STATE_FILE_NAME
            LOGGER.error("wideq_state file not found. Trying to load default STATE_FILE: " + STATE_FILE_NAME)

LOGGER.info("wideq_state will be loaded from: " + STATE_FILE)


def authenticate(gateway):
    """Interactively authenticate the user via a browser to get an OAuth
    session.
    """

    login_url = gateway.oauth_url()
    print("Log in here:")
    print(login_url)
    print("Then paste the URL where the browser is redirected:")
    callback_url = input()
    return wideq.Auth.from_url(gateway, callback_url)


def ls(client):
    """List the user's devices."""

    thinq1_devices = [dev for dev in client.devices if dev.platform_type == "thinq1"]
    thinq2_devices = [dev for dev in client.devices if dev.platform_type == "thinq2"]

    if len(thinq1_devices) > 0:
        print("\nthinq1 devices: {}".format(len(thinq1_devices)))
        print("WARNING! Following devices are V1 LG API and will likely NOT work with this domoticz plugin!\n")
        for device in thinq1_devices:
            print("{0.id}: {0.name} ({0.type.name} {0.model_id} / {0.platform_type})".format(device))

    print("\nthinq2 devices: {}".format(len(thinq2_devices)))
    if len(thinq2_devices) > 0:
        for device in thinq2_devices:
            print("{0.id}: {0.name} ({0.type.name} {0.model_id} / {0.platform_type})".format(device))
    else:
        print("\n--------------------------------------------------------------------------------")
        print("You don't have any thinq2 (LG API V2) device. This plugin will not work for you.")
        print("wideq_state.json file will NOT be generated.")
        print("--------------------------------------------------------------------------------")


def info(client, device_id):
    """Dump info on a device."""

    device = client.get_device(device_id)
    # pprint(vars(device), indent=4, width=1)
    return device.data


def gen_mon(client, device_id):
    """Monitor any other device but AC device,
    displaying generic information about its status.
    """

    device = client.get_device(device_id)
    model = client.model_info(device)

    with wideq.Monitor(client.session, device_id) as mon:
        try:
            while True:
                time.sleep(1)
                print("Polling...")
                data = mon.poll()
                if data:
                    try:
                        res = model.decode_monitor(data)
                        print(res)
                    except ValueError:
                        print("status data: {!r}".format(data))
                """
                else:
                        for key, value in res.items():
                            try:
                                desc = model.value(key)
                            except KeyError:
                                print("- {}: {}".format(key, value))
                            if isinstance(desc, wideq.EnumValue):
                                print(
                                    "- {}: {}".format(
                                        key, desc.options.get(value, value)
                                    )
                                )
                            elif isinstance(desc, wideq.RangeValue):
                                print('- {0}: {1} ({2.min}-{2.max})'.format(
                                    key, value, desc,
                                )) """

        except KeyboardInterrupt:
            pass


def ac_mon(ac):
    """Monitor an AC/HVAC device, showing higher-level information about
    its status such as its temperature and operation mode.
    """

    try:
        ac.monitor_start()
    except wideq.core.NotConnectedError:
        print("Device not available.")
        return

    try:
        while True:
            time.sleep(1)
            state = ac.poll()
            if state:
                print(
                    "state {1}; "
                    "{0.mode.name}; "
                    "cur {0.temp_cur_c}°C; "
                    "cfg {0.temp_cfg_c}°C; "
                    "fan speed {0.fan_speed.name}; "
                    "energy {0.energy_on_current}".format(
                        state, "on" if state.is_on else "off"
                    )
                )
            else:
                print("no state. Wait 1 more second.")

    except KeyboardInterrupt:
        pass
    finally:
        ac.monitor_stop()


def mon(client, device_id):
    """Monitor any device, displaying generic information about its
    status.
    """

    device_class = client.get_device_obj(device_id)
    if isinstance(device_class, wideq.ACDevice):
        ac_mon(device_class)
    else:
        gen_mon(client, device_id)


class UserError(Exception):
    """A user-visible command-line error."""

    def __init__(self, msg):
        self.msg = msg


def _force_device(client, device_id):
    """Look up a device in the client (using `get_device`), but raise
    UserError if the device is not found.
    """
    device = client.get_device(device_id)
    if not device:
        raise UserError('device "{}" not found'.format(device_id))
    if device.platform_type != "thinq2":
        raise AttributeError(
            'Sorry, device "{}" is V1 LG API and will NOT work with this domoticz plugin.'.format(device_id))
    return device


def set_temp(client, device_id, temp):
    """Set the configured temperature for an AC or refrigerator device."""

    device = client.get_device(device_id)

    if device.type == wideq.client.DeviceType.AC:
        ac = wideq.ACDevice(client, _force_device(client, device_id))
        ac.set_fahrenheit(int(temp))
    elif device.type == wideq.client.DeviceType.REFRIGERATOR:
        refrigerator = wideq.RefrigeratorDevice(
            client, _force_device(client, device_id)
        )
        refrigerator.set_temp_refrigerator_c(int(temp))
    else:
        raise UserError(
            "set-temp only suported for AC or refrigerator devices"
        )


def set_temp_freezer(client, device_id, temp):
    """Set the configured freezer temperature for a refrigerator device."""

    device = client.get_device(device_id)

    if device.type == wideq.client.DeviceType.REFRIGERATOR:
        refrigerator = wideq.RefrigeratorDevice(
            client, _force_device(client, device_id)
        )
        refrigerator.set_temp_freezer_c(int(temp))
    else:
        raise UserError(
            "set-temp-freezer only supported for refrigerator devices"
        )


def set_temp_hot_water(client, device_id, temp):
    """Set the configured hot-water temperature for a heat pump device."""

    device = client.get_device(device_id)

    if device.type == wideq.client.DeviceType.AC:
        awhp = wideq.ACDevice(client, _force_device(client, device_id))
        awhp.set_hot_water(int(temp))


def turn(client, device_id, on_off):
    """Turn on/off an AC device."""

    ac = wideq.ACDevice(client, _force_device(client, device_id))
    ac.set_on(on_off == "on")


def ac_config(client, device_id):
    ac = wideq.ACDevice(client, _force_device(client, device_id))
    print(f"supported_operations: {ac.supported_operations}")
    print(f"supported_on_operation: {ac.supported_on_operation}")
    print(f"get_filter_state: {ac.get_filter_state()}")
    print(f"get_mfilter_state: {ac.get_mfilter_state()}")
    print(f"get_energy_target: {ac.get_energy_target()}")
    print(f"get_power: {ac.get_power(), 'watts'}")
    print(f"get_outdoor_power: {ac.get_outdoor_power(), 'watts'}")
    print(f"get_volume: {ac.get_volume()}")
    print(f"get_light: {ac.get_light()}")
    print(f"get_zones: {ac.get_zones()}")


EXAMPLE_COMMANDS = {
    "ls": ls,
    "mon": mon,
    "set-temp": set_temp,
    "set-temp-freezer": set_temp_freezer,
    "set-temp-hot-water": set_temp_hot_water,
    "turn": turn,
    "ac-config": ac_config,
    "info": info,
}


def example_command(client, cmd, args):
    func = EXAMPLE_COMMANDS.get(cmd)
    if not func:
        LOGGER.error(
            "Invalid command: '%s'.\n" "Use one of: %s",
            cmd,
            ", ".join(EXAMPLE_COMMANDS),
        )
        return
    return func(client, *args)


def example(country: str,
            language: str,
            verbose: bool,
            device_id="",
            cmd="",
            state=None,
            args=None):
    if args is None:
        args = []
    if state is None:
        state = {"gateway": {}, "auth": {}}
    if verbose:
        wideq.set_log_level(logging.DEBUG)

    # Load the current state for the example.
    if state["gateway"] != {} and state["auth"] != {}:
        # if state data comes from Domoticz Configuration
        LOGGER.info("State data loaded from Domoticz Configuration.")
    else:
        # if state data comes from wideq_state.json
        try:
            with open(STATE_FILE) as f:
                LOGGER.info("State data loaded from " + os.path.abspath(STATE_FILE) + "'")
                state = json.load(f)
        except IOError:
            LOGGER.error("No state file found (tried: '" + os.path.abspath(STATE_FILE) + "')")
            state = {}
            # raise IOError
        except json.decoder.JSONDecodeError:
            LOGGER.error("Broken wideq_state.json file?")
            raise IOError

    client = wideq.Client.load(state)
    if country:
        client._country = country
    if language:
        client._language = language

    # Log in, if we don't already have an authentication.
    if not client._auth:
        client._auth = authenticate(client.gateway)

    # Loop to retry if session has expired.
    while True:
        try:
            ac = None
            if len(device_id) > 0:
                ac = wideq.ACDevice(client, _force_device(client, device_id))
            else:
                resp = example_command(client, cmd, args)
            break

        except wideq.NotLoggedInError:
            LOGGER.info("Session expired.")
            client.refresh()

        except UserError as exc:
            LOGGER.error(exc.msg)
            # sys.exit(1)
            raise UserWarning

        except AttributeError as exc:
            LOGGER.error(exc.args[0])
            # sys.exit(2)
            raise AttributeError

    thinq2_devices = [dev for dev in client.devices if dev.platform_type == "thinq2"]
    if len(thinq2_devices) > 0:
        # Save the updated state.
        state = client.dump()
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
            LOGGER.info("Wrote state file '%s'", os.path.abspath(STATE_FILE))

    dict_for_domoticz = {"gateway":state["gateway"], "auth":state["auth"]}

    return ac, dict_for_domoticz


def main() -> None:
    """The main command-line entry point."""
    parser = argparse.ArgumentParser(
        description="Interact with the LG SmartThinQ API."
    )
    parser.add_argument(
        "cmd",
        metavar="CMD",
        nargs="?",
        default="ls",
        help=f'one of: {", ".join(EXAMPLE_COMMANDS)}',
    )
    parser.add_argument(
        "args", metavar="ARGS", nargs="*", help="subcommand arguments"
    )

    parser.add_argument(
        "--country",
        "-c",
        help=f"country code for account (default: {wideq.DEFAULT_COUNTRY})",
        default=wideq.DEFAULT_COUNTRY,
    )
    parser.add_argument(
        "--language",
        "-l",
        help=f"language code for the API (default: {wideq.DEFAULT_LANGUAGE})",
        default=wideq.DEFAULT_LANGUAGE,
    )
    parser.add_argument(
        "--verbose",
        "-v",
        help="verbose mode to help debugging",
        action="store_true",
        default=False,
    )

    args = parser.parse_args()
    country_regex = re.compile(r"^[A-Z]{2,3}$")
    if not country_regex.match(args.country):
        LOGGER.error(
            "Country must be two or three letters"
            " all upper case (e.g. US, NO, KR) got: '%s'",
            args.country,
        )
        exit(1)
    language_regex = re.compile(r"^[a-z]{2,3}-[A-Z]{2,3}$")
    if not language_regex.match(args.language):
        LOGGER.error(
            "Language must be a combination of language"
            " and country (e.g. en-US, no-NO, kr-KR)"
            " got: '%s'",
            args.language,
        )
        exit(1)
    ret = example(args.country, args.language, args.verbose, cmd=args.cmd, args=args.args)


if __name__ == "__main__":
    main()
