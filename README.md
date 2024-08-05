# Subspace-Thingies

## My tools and utils for the Subspace Network.
Currently there is the Farm monitor, and a standalone Wallet monitor (instructions at bottom)
The wallet monitor is also built into the Farm Monitor
![image](https://github.com/wolfrage76/Subspace-Thingies/assets/75458290/b6152d9f-be70-483c-9279-ec6b8c8a6083)
### Wallet Monitor Thingy ###
Standalone wallet monitor - Do *not* use with The Farmer Monitor Thingy as it is already built into it.
This will query your node for wallet balance changes, and notify you via discord (more notifications soon!)

- Rename `config.yaml.example` to `config.yaml` and then edit the configuration
- Run `pip install -r requirements.txt`
- Run `python wallet_monitor_thingy.py`


### Farm Monitor Thingy

- Supports remote farmers
- Notifications to Discord or Pushover (more coming!) of events
- Monitors your wallet for balance changes
- Lots more!

More features coming!

Ping me on the Subspace Discord (Wolfrage) if you have any questions. No DMs though -- DMs are the Devil's handjob.

Installation:
 - You must add `--rpc-listen-on <LocalIP>:<Port>` to your NODE launch command - port 9944 is default
 - You must add `--prometheus-listen-on <localIP>:<Port>` to your FARMER launch command - port 8181 is default
 - If you need to create a farmer log file, add this to the end of your launch command: ` |tee -a <FILENAME>.txt`


FOR BOTH SIDES:
1. Edit `config.yaml.example` and save it as `config.yaml` 
2. Copy `config.yaml` to both monitor and viewer folders
3. Run: `pip install -r requirements.txt`


THEN FOR FARMER SIDE:
1. Save monitor folder to the farmer
3. Run: `monitor.py` to launch


THEN FOR VIEWER:
1. Copy the Viewer folder to a machine you can connect to the console for
2. In the folder Run: `pip install -r requirements.txt`
3. Run: `python view.py` to launch

The UI will not fully update until a machine cycles and sends its data over.  If the drive list is empty after awhile, or if you get Unicode Errors, edit config.yaml and toggle the "TOGGLE_ENCODING" setting.
