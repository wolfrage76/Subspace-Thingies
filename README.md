# Subspace-Thingies

## My tools and utils for the Subspace Network.

![image](https://github.com/wolfrage76/Subspace-Thingies/assets/75458290/c97a59a4-d58d-4306-8863-d7d895896857)


### Wallet Monitor Thingy ###
Standalone wallet monitor - Do *not* use with The Farmer Monitor Thingy as it is already built into it.
This will query your node for wallet balance changes, and notify you via discord (more notifications soon!)

Rename `config.yaml.example` to `config.yaml` and then edit the configuration
Run `pip install -r requirements.txt`
Run `python wallet_monitor_thingy.py`


### Farm Monitor Thingy

- Supports remote farmers
- Backend script goes on Farmer machine, separate remote viewing UI anywhere else
- Notifications to Discord or Pushover (more coming!) of events
- It converts log timestamp to your local timezone
- Monitors your wallet for balance changes
- Lots more!

More features coming!

Ping me on the Subspace Discord (Wolfrage) if you have any questions. No DMs though -- DMs are the Devil's handjob.

Installation:
I'm high and writing this on the fly, so hopefully you'll be able to get by, my guy.

(You should usually setup a VENV for a python app but whatever)

* FOR FARMER SIDE:
1. Copy contents of For-Farmer to a location on a Farmer machine
2. In the folder Run: `pip install -r requirements.txt`
3. Inside the folder copy `config.yaml.example` to `config.yaml` and then Edit it
   Or run `python setup.py` and copy the resulting `config.yaml` into the folder
4. Run: `python Subspace_Farm_Monitor_Thingy.py` to launch


* FOR VIEWER:
1. Copy contents of Viewer to a machine you can connect to the consolde for (and has drive access to Node log, preferably)
2. In the folder Run: `pip install -r requirements.txt`
3. Inside the folder you can copy `config.yaml.example` to `config.yaml` and then Edit it (or use the same from the Farmer-Side)
   Or run `python setup.py` and copy the resulting `config.yaml` into the folder
4. Run: `python view.py` to launch

The UI will not fully update until a machine cycles and sends its data over.  If the drive list is empty after awhile, or if you get Unicode Errors, edit config.yaml and toggle the "TOGGLE_ENCODING" setting.


* Need to configure a node or farmer log file? Add this to the end of your launch command (there are other ways though): `*> <FILENAME>.txt`

Farmer sample:`.\subspace-farmer-windows-x86_64-skylake-gemini-3h-2024-feb-01 farm --reward-address xxxxxxxxxxx  path=z:\\dev-farm2,size=2GiB *> farmerlog.txt`

Node sample: ` .\subspace-node-windows-x86_64-skylake-gemini-3h-2024-feb-01 run --chain gemini-3h --blocks-pruning 256 --state-pruning archive-canonical --base-path z:\subspace-node --farmer --name "BitcoinBart" *> -file nodelog.txt	`

**_ Don't judge my code, you uncouth heathens! Figuring stuff out first, then I'll make it nice and pretty. Well, pretty-ish. Whatever. I'm having fun. _**
