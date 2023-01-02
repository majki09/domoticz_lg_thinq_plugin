Domoticz LG ThinQ (with WideQ) plugin.
=====

![alt text](https://raw.githubusercontent.com/majki09/domoticz_lg_thinq_plugin/main/domoticz.jpg "LG ThinQ plugin in domoticz")

:warning: **New users of LG ThinQ**: This library only works with v2 of the LG ThinQ API. You can check if your device is compatible when you execute the `example.py`. To use it, provide it with a country and language code via the `-c` and `-l` flags, respectively:

    $ python3 example.py -c US -l en-US

LG accounts seem to be associated with specific countries, so be sure to use the one with which you originally created your account. For Polish, for example, you'd use `-c PL -l en-US`.

On first run, the script will ask you to log in with your LG account.
Logging in with Google does not seem to work, but other methods (plain email & password, Facebook, and Amazon) do. 

By default, the example just lists the devices associated with your account.

Installation
------------

1. Clone plugin to your domoticz

       cd /home/pi/domoticz/plugins
       git clone https://github.com/majki09/domoticz_lg_thinq_plugin.git
       cd ./domoticz_lg_thinq_plugin

2. Login and get your token. Put your own country and language codes.

       $ python3 example.py -c US -l en-US
 
   Copy and go to given address with your browser. Log in, copy new address from your browser and paste it to console window. 

:warning: In case your device is not compatible, you will NOT get `wideq_state.json` and you will get following message:

       thinq1 devices: 1
       WARNING! Following devices are V1 LG API and will likely NOT work with this domoticz plugin!

       ab123456-c3c5-8181-9ec2-abcdef123456: LG thinq1 device (AC AWHP_5555_WW / thinq1)

       thinq2 devices: 0

       --------------------------------------------------------------------------------
       You don't have any thinq2 (LG API V2) device. This plugin will not work for you.
       wideq_state.json file will NOT be generated.
       --------------------------------------------------------------------------------

Proceed only if you have at least one *thinq2* compatible device listed, which can look like this:
   
       thinq2 devices: 1
       ed123456-f3c5-1616-9ec2-abcdef123456: Klima (AC RAC_056905_WW / thinq2)
   
   which `ed123456-f3c5-1616-9ec2-abcdef123456` is Device ID (yours will be different). Note down your AC's Device ID to notepad. You will get your `wideq_state.json` file in plugin folder.
	
3. Restart your domoticz.

       $ sudo systemctl restart domoticz.service

4. Open **Hardware** tab and you should be now able to add new LG ThinQ device to your domoticz. Put your country and language codes and device ID. Click **Add** and new domoticz devices should be created. That's it!

Docker
------
Just install like any other plugin - manual: https://www.domoticz.com/wiki/Docker#Python_Plugins. The rest is pretty the same. To avoid loosing your `wideq_state.json` file (e.g. when recreating the container) just keep it under */userdata* folder - that's it!

Development
-----------
The API has been reverse-engineered from LG's mobile app.
This project is based on `wideq` project that has been developed by [Adrian Sampson][adrian] and modified for v2 by [no2chem] in his [fork]. I have made domoticz plugin then which uses most of their work for LG's server connection.

To-do
-----
- devices are updated with a heartbeat (every 60 seconds). If you change your AC's parameters with IR remote or mobile app, changes are not updated imidiately in your domoticz. Not applicable for domoticz control.
- force status updates more often - for now statuses like internal temp. or set-point are updated only while turning on the device.

Credits
-------
Many thanks for 
- [Adrian Sampson][adrian] and [no2chem] for his [fork] with V2 version,
- [superprzemo] for his wideq_state file with heat-pump.

The license is [MIT].

[adrian]: https://github.com/sampsyo
[no2chem]: https://github.com/no2chem
[fork]: https://github.com/no2chem/wideq
[mit]: https://opensource.org/licenses/MIT
[superprzemo]: https://github.com/superprzemo
