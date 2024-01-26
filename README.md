# Subspace-Thingies
My tools and utils for the Subspace Network.  

-Wallet Monitor Thingy:  Will run and monitor your wallet address for balance changes, and will send you notifications on the new balance and the change.
-Farm Monitor Thingy: Will launch the Farmer and capture its output to a log and to screen, filtering the log to notify you (log, screen, discord, etc) of events. It also converts log timestamp to your local timezone. More features coming. 


Ping me on the Subspace Discord (Wolfrage) if you have any questions.  No DMs though -- DMs are the Devil's handjob.

Known Issues:
Wallet monitor thingy will crash out if your node goes down.  I'll add handling when I get around to it.
There is no option to disable logging to file for the Farm monitor yet.  I'll get that added and maybe log rotation too, at some point.

*** Don't judge my code, you uncouth heathens!  Figuring stuff out first, then I'll make it nice and pretty. Well, pretty-ish. Whatever. I'm having fun. ***

I launch the farm monitor thingy via Task Scheduler in Windows on boot, which calls a powerscript shell that has a small delay in the script (so node comes up first on boot) and then calls 'python script.py'. Task scheduler has the option to hide the process too.  Linux users should already know how to change stuff to make it run so I'm not going to waste their time telling them that they can just setup a cron process using crontab -e to set an @reboot line calling the script.  Or I guess I am.

The Wallet Monitor Thingy I just run on a Pi and set the node address to my node's IP.  If it's on the same machine, you can use 127.0.0.1.  Should technically work with a public node endpoint too, I guess.

--Bitcoin Bart
