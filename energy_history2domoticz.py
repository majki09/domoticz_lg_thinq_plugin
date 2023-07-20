#!/usr/bin/env python3
import wideq
import json
import argparse
import datetime
import re
import requests
import os.path
import logging
from time import sleep

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


class UserError(Exception):
    """A user-visible command-line error."""

    def __init__(self, msg):
        self.msg = msg


def api_call(client: wideq.Client,
             device_id: str,
             start_date: str,
             end_date: str):
    # Loop to retry if session has expired.
    while True:
        try:
            LOGGER.info(f"Getting energy history data from range {start_date} - {end_date} from LG server...")
            energy_history = client.session.get_energy_history(device_id=device_id,
                                                               type="day",
                                                               start_date=start_date,
                                                               end_date=end_date)
            break

        except wideq.NotLoggedInError:
            LOGGER.info("Session expired.")
            client.refresh()

        except wideq.core.APIError as exc:
            LOGGER.error(f"API ERROR: {exc.code}, {exc.message}")
            exit(3)

    if len(energy_history) == 0:
        LOGGER.error("No data from LG server has been fetched.")
        exit(4)
    else:
        LOGGER.info(f"Energy history data from range {start_date} - {end_date} successfully fetched from LG server.")

    return energy_history


def get_energy_history(country: str,
                       language: str,
                       verbose: bool,
                       device_id="",
                       domoticz_url="",
                       idx="",
                       start_date="",
                       end_date=""):
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

    energy_history = []
    dates_chunks = dates_to_chunks(start_date, end_date)

    for chunk in dates_chunks:
        energy_history.extend(api_call(client,
                                       device_id,
                                       start_date=datetime.date.isoformat(chunk["start"]),
                                       end_date=datetime.date.isoformat(chunk["end"])))

    return upload_data(url=domoticz_url, idx=idx, data=energy_history)


def count_days(start_date: str, end_date: str):
    start = datetime.date.fromisoformat(start_date)
    end = datetime.date.fromisoformat(end_date)
    number_of_days = end - start

    return number_of_days.days


def dates_to_chunks(start_date: str, end_date: str):
    """
    Check if number of days between start and end not exceed 31.
    This is limitation of LG API.
    """
    number_of_days = count_days(start_date, end_date)
    dates_set = []

    if number_of_days > 30:
        # need to split for multiple API calls
        days_to_readout = 30
        days_left = number_of_days
        start = datetime.date.fromisoformat(start_date)
        while days_left > 0:
            if days_left < days_to_readout:
                days_to_readout = days_left

            days_left -= (days_to_readout + 1)
            end = start + datetime.timedelta(days_to_readout)
            dates_set.append({"start": start, "end": end})
            start = end + datetime.timedelta(1)
    else:
        start = datetime.date.fromisoformat(start_date)
        end = datetime.date.fromisoformat(end_date)
        dates_set.append({"start": start, "end": end})

    return dates_set


def build_svalue(date: str, value: str):
    counter = "-1"
    usage = value
    date = date

    return f"{counter};{usage};{date}"


def upload_data(url: str, idx: str, data: list):
    for index, day in enumerate(data):
        try:
            index += 1  # let's count from 1, rather than from 0
            svalue = build_svalue(date=day["usedDate"], value=day["energyData"])
            send_ret = send_to_domoticz(domoticz_url=url,
                                        idx=idx,
                                        svalue=svalue)
            LOGGER.info(f'{index}/{len(data)} {index / len(data) * 100:.0f}%\tSending {day["usedDate"]} '
                        f'({day["energyData"]})\t{"OK" if send_ret == 200 else "FAILED!"}')
            sleep(1)

        except Exception as exc:
            LOGGER.error(f"ERROR: {exc}")
            return False
    return True


def send_to_domoticz(domoticz_url: str, idx: str, svalue: str):
    try:
        # url = "http://{}:{}/json.htm".format(domoticz_address, domoticz_port)
        url = domoticz_url + "/json.htm"
        # headers = {'content-type': 'application/json', 'Authorization': domoticz_auth}
        headers = {'content-type': 'application/json'}
        postdata = {'type': 'command', 'param': 'udevice', 'idx': idx, 'nvalue': 0, 'svalue': svalue}
        resp = requests.get(url=url, headers=headers, params=postdata)

        LOGGER.debug("resp.status_code=\t{}".format(resp.status_code))

        return resp.status_code
    except Exception as ex:
        print(ex)
        exit(1)


def main() -> None:
    """The main command-line entry point."""
    parser = argparse.ArgumentParser(
        description="Interact with the LG SmartThinQ API."
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
        "--domoticz_url",
        "-u",
        help=f"domoticz URL, e.g.: http://domoticz.local:8090",
    )
    parser.add_argument(
        "--device_id",
        "-d",
        help=f"LG device ID",
    )
    parser.add_argument(
        "--idx",
        "-i",
        help=f"Domoticz device IDX number",
    )
    parser.add_argument(
        "--start_date",
        "-s",
        help=f"start date e.g.: 2022-01-01",
    )
    parser.add_argument(
        "--end_date",
        "-e",
        help=f"end date e.g.: 2022-12-31",
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
    device_id_regex = re.compile(r"^.{8}-.{4}-.{4}-.{4}-.{12}$")
    if not device_id_regex.match(args.device_id):
        LOGGER.error(
            "Invalid 'device ID'. Example:\n"
            " 'ed123456-f3c5-1616-9ec2-abcdef123456' and you put \n"
            " '%s'",
            args.device_id,
        )
        exit(1)
    idx_regex = re.compile(r"^\d{1,4}$")
    if not idx_regex.match(args.idx):
        LOGGER.error(
            "Invalid IDX. Have to be a number and you put \n"
            " '%s'",
            args.idx,
        )
        exit(1)
    dates_regex = re.compile(r"^\d{4}-[01]\d-[0-3]\d$")
    if not dates_regex.match(args.start_date) or not dates_regex.match(args.end_date):
        LOGGER.error(
            "Invalid start or end date. Have to be a ISO format (eg. 2022-01-01) and you put \n"
            " start: '%s' and end: '%s'",
            args.start_date, args.end_date,
        )
        exit(1)
    domoticz_url_regex = re.compile(r"^https?://.+(:\d{2,5})?$")
    if not domoticz_url_regex.match(args.domoticz_url):
        LOGGER.error(
            "Invalid domoticz URL. Example:\n"
            " 'http://domoticz.local:8090' and you put:\n"
            " '%s'",
            args.domoticz_url,
        )
        exit(1)

    get_energy_history(country=args.country,
                       language=args.language,
                       verbose=args.verbose,
                       device_id=args.device_id,
                       domoticz_url=args.domoticz_url,
                       idx=args.idx,
                       start_date=args.start_date,
                       end_date=args.end_date)


if __name__ == "__main__":
    main()
