# Subspace-Thingies

## My tools and utils for the Subspace Network.

NOTE: Live mode is NOT working for some reason.  For the moment, please use the logging mode instead.  Working on it though!

[[![image](https://github.com/wolfrage76/Subspace-Thingies/assets/75458290/aa034718-dfa9-41ea-bc8d-9420ba58ae7a)](https://github.com/irbujam/ss_log_event_monitor)](https://github.com/irbujam/ss_log_event_monitor)


### Farm Monitor Thingy

* Can launch the Farmer and capture it live, OR configured to monitor a farmer log

* Has a smaller display option without logs, if preferred

* Output to a log and screen

* Filters the log

* Notifications to Discord or Pushover (more coming!) of events

* It converts log timestamp to your local timezone

* Monitors your wallet for balance changes

* If streaming live Farmer, can auto restart if there's an error (i.e. if the node dropped)

More features coming!

This has BASIC retrys. Let me know if they don't work, and what the error was.
Ping me on the Subspace Discord (Wolfrage) if you have any questions. No DMs though -- DMs are the Devil's handjob.

Installation:
I'm high and writing this on the fly, so hopefully you'll be able to get by, my guy.

Reqs: Tested on Windows -- Linux should work but not tested.
*Latest-ish Python
*A working Node
*A working Farmer

(You should usually setup a VENV for a python app but whatever)

1. Run: `pip install -r requirements.txt`
2. Copy: `config.yaml.example` to `config.yaml`
3. Edit: `config.yaml` (Details below)
4. Run: `python Subspace_Farm_Monitor_Thingy.py`
5. Copy: your Farmer Executable to this script location
6. ***Enjoy your SSD empire***

## Configuration: config.yaml
`IS_LIVE: True`         - If set to `False` then it will read from your Farmer Log (details below if you need to set it up)
           -            - If set `True` then it will launch your Farmer and process the stream live. 
                         **NO** quotes around True or False
`SHOW_LOGGING: True` # If False, it will hide the Log scroll and only show farms for smaller screen space
                         
`TOGGLE_ENCODING:  False`  - If Disk list doesn't appear when IS_LIVE is set False, set this to True instead.

`FARMER_LOG: "c:\\Users\\wolfrage\\subspace\\farmlog.txt"` - States what Farmer Log to read if IS_LIVE is set to True.  Equired if IS_LIVE is False.
                       -Windows uses double \'s'

`NODE_EXECUTABLE_FOLDER: 'z:\\dev'` - Where your node executable file is located

`NODE_LOG_FILE:` `"c:\\Users\\wolfrage\\subspace\\nodelog.txt"` - States your Node log file to monitor - required for Node data 
                        -Windows uses double \'s'                       

`NODE_IP: "127.0.0.1"`  - Your nodes internal IP (127.0.0.1, 192.168.1.69, whatever)

`NODE_PORT: "9944"`     - Port the node is using -- 9944 is default

`WALLET:  "xxxxxxxxxx"` - Wallet address to monitor for balance changes

`SEND_DISCORD: False`   - Send notifications to Discord?

`SEND_PUSHOVER: False`  - Send notifications to Pushover?

`DISCORD_WEBHOOK:`      - Webhook for the Discord channel you want notifications to reach
                                 Format is "https://discord.com/api/webhooks/xxxxxx/xxxxxxxxxxxxx"
                             
                             
`PUSHOVER_APP_TOKEN:`     - APP Token from Pushover.com  Format: "xxxxxxxxxxxxxx"

`PUSHOVER_USER_KEY:`      - User Key from Pushover.com Format: "yyyyyyyyyyyyy"


`WAIT_PERIOD: 300`        -Wallet check interval seconds.  No quotes around it.

`MUTE_HICKORY: True`      - Blocks an annoying msg :)


`COMMANDLINE:` '.\subspace-farmer-windows-x86_64-skylake-gemini-3h-2024-feb-01 farm --reward-address xxxxxxxxxxx --node-rpc-url ws://192.168.1.205:9944 path=z:\\dev-farm,size=3GiB path=z:\\dev-farm2,size=2GiB'

## Commandline Field Above - To use IS_LIVE: True  put your WHOLE launch command above. 

Need to configure a node or farmer log file?  Add this to the end of your launch command: `*> <FILENAME>.txt`

Farmer sample:```.\subspace-farmer-windows-x86_64-skylake-gemini-3h-2024-feb-01 farm --reward-address xxxxxxxxxxx  path=z:\\dev-farm2,size=2GiB *> farmerlog.txt```

Node sample: ``` .\subspace-node-windows-x86_64-skylake-gemini-3h-2024-feb-01 run --chain gemini-3h --blocks-pruning 256 --state-pruning archive-canonical --base-path z:\subspace-node --farmer --name "BitcoinBart" --allow-private-ips  --rpc-methods unsafe --rpc-cors all --rpc-listen-on 127.0.0.1:9944 *> -file nodelog.txt	```


**_ Don't judge my code, you uncouth heathens! Figuring stuff out first, then I'll make it nice and pretty. Well, pretty-ish. Whatever. I'm having fun. _**
