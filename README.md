Domoticz LG Thinq (with WideQ) plugin.
=====

:warning: **New users of LG ThinQ**: This library only works with v2 of the LG ThinQ API. You can check how many devices this library will return when you execute the `ls` command.

A library for interacting with the "LG ThinQ" system, which can control heat pumps and such. The API has been reverse-engineered from LG's mobile app.

To try out the API, there is a simple command-line tool included here, called `example.py`.
To use it, provide it with a country and language code via the `-c` and `-l` flags, respectively:

    $ python3 example.py -c US -l en-US

LG accounts seem to be associated with specific countries, so be sure to use the one with which you originally created your account.
For Polish, for example, you'd use `-c PL -l en-US`.

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
 
   Copy and go to given address with your browser. Log in, copy new address from your browser and paste it to console window. If there is no error, you will get `wideq_state.json` file. Also, your LG ThinQ devices should be listed below, which will be looking like:
   
       ed123456-f3c5-1616-9ec2-abcdef123456: Klima (AC RAC_056905_WW / thinq2)
   
   which `ed123456-f3c5-1616-9ec2-abcdef123456` is Device ID (yours will be different). Note down your AC's Device ID to notepad.

3. Move your `wideq_state.json` file to domoticz folder.

       $ mv ./wideq_state.json ../../
	
4. Restart your domoticz.

       $ sudo systemctl restart domoticz.service

5. Open **Hardware** tab and you should be now able to add new LG ThinQ device to your domoticz. Put your country and language codes and device ID. Click **Add** and new domoticz devices should be created. That's it!

Development
-----------

This project is based on `wideq` project that has been developed by [Adrian Sampson][adrian] and modified for v2 by [no2chem] in his [fork]. I have made domoticz plugin then which uses most of their work for LG's server connection.

To-do
-----
- devices are updated with a heartbeat (every 60 seconds). If you change your AC's parameters with IR remote or mobile app, changes are not updated imidiately in your domoticz. Not applicable for domoticz control.

Credits
-------
Many thanks for [Adrian Sampson][adrian] and [no2chem] for his [fork] with V2 version.
The license is [MIT][].

[adrian]: https://github.com/sampsyo
[no2chem]: https://github.com/no2chem
[fork]: https://github.com/no2chem/wideq
[mit]: https://opensource.org/licenses/MIT