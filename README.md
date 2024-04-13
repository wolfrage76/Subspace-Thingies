# Subspace-Thingies

## My tools and utils for the Subspace Network.

![image](https://github.com/wolfrage76/Subspace-Thingies/assets/75458290/d0b172b6-6041-48ae-949b-22727d5f7dd9)

### Wallet Monitor Thingy ###
Standalone wallet monitor - Do *not* use with The Farmer Monitor Thingy as it is already built into it.
This will query your node for wallet balance changes, and notify you via discord (more notifications soon!)

Rename `config.yaml.example` to `config.yaml` and then edit the configuration
Run `pip install -r requirements.txt`
Run `python wallet_monitor_thingy.py`


### Farm Monitor Thingy

- Supports remote farmers
- Notifications to Discord or Pushover (more coming!) of events
- Monitors your wallet for balance changes
- Lots more!

More features coming!

Ping me on the Subspace Discord (Wolfrage) if you have any questions. No DMs though -- DMs are the Devil's handjob.

Installation:
 You must add `--rpc-listen-on <LocalIP>:<Port>` to your NODE launch command - port 9944 is default
 You must add `--prometheus-listen-on <localIP>:<Port>` to your FARMER launch command - port 8181 is default
 To create a farmer log file, add this to the end of your launch command: ` |tee -a <FILENAME>.txt`

* FOR FARMER SIDE:
1. Save monitor folder to the farmer
2. In the folder Run: `pip install -r requirements.txt`
3. Inside the folder copy `config.yaml.example` to `config.yaml` and then Edit it
4. Run: `python Subspace_Farm_Monitor_Thingy.py` to launch


* FOR VIEWER:
1. Copy the Viewer folder to a machine you can connect to the console for
2. In the folder Run: `pip install -r requirements.txt`
3. Copy the config.yaml file you created from monitor to viewer folder
4. Run: `python view.py` to launch

The UI will not fully update until a machine cycles and sends its data over.  If the drive list is empty after awhile, or if you get Unicode Errors, edit config.yaml and toggle the "TOGGLE_ENCODING" setting.

