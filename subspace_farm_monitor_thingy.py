#BitcoinBart was here

import subprocess
from pathlib import Path
from datetime import datetime 


discord_webhook = ''
pushover_app_token = ''
pushover_api = ''
send_discord = False
send_pushover = False
mute_hickory = True

#os.chdir('C:\\Users\\BitcoinBart\\subspace')
reward_phrase = 'reward_signing: Successfully signed reward hash'


def send(msg=None):
    #### Discord

    if send_discord and msg:

        import requests
        data = {"content": msg}
        response = requests.post(discord_webhook, json=data)
        success_list = [204]
        if response.status_code not in success_list:
            print('Error sending Discord: ' + str(response.status_code))

    ##### Pushover

    if send_pushover and pushover_app_token != '' and pushover_api != '' and msg:
        import http.client, urllib
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
                     urllib.parse.urlencode({
                         "token": pushover_app_token,
                         "user": pushover_api,
                         "message": msg,
                     }), {"Content-type": "application/x-www-form-urlencoded"})
        conn.getresponse()

def datetime_valid(dt_str):
    try:
        datetime.fromisoformat(dt_str)
    except:
        return False
    return True

def local_time(string):
    my_string = ''
    string2 = string.split()
    convert = string2[0]
    
    if datetime_valid(convert):    

        datestamp = datetime.fromisoformat(str(convert)).astimezone(tz=None)
        string2[0] = datestamp.strftime("%m-%d-%Y %H:%M:%S | ")

        for piece in string2:

            my_string += '{} '.format(piece)
        my_string = my_string
    else:
        my_string=string
    return(my_string)

def make_csv(str):
    pass

def pull_stats(input, start,end=None):
    if end != None:
        return input[input.index(start)+len(start):input.index(end)]
    else:
        return input[input.index(start)+len(start):]

def get_plot_stats(str):
    #print(str)
    #str="INFO single_disk_farm{disk_farm_index=1}: subspace_farmer::single_disk_farm::plotting: Plotting sector (76.74% complete) sector_index=330"
    str=str.split()
    
    index = pull_stats(str[2],"index=","}:")
    sector = pull_stats(str[8],"sector_index=")
    percent =  pull_stats(str[6],"(","%")    


def run_command(command, **kwargs):
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        **kwargs,
    )

    while True:
        line = process.stdout.readline()

        # TODO convert to a list of filters vs singlar
        
        if not line and process.poll() is not None:
            break
        
        
        elif reward_phrase in line.decode():
            print('\n\n************************************* WINNER! *************************************\n\n')
            # TODO save to csv block, farm, time, total (pdragon)
            
            send('WINNER! You were rewarded!')
        elif '100% complete' in line.decode():
            print('\n\n************************************* Plot Complete! *************************************\n\n')
            # TODO Save to csv data as above
            send('Plot complete: ' + line.decode().split()[2] + ' 100%!')
            
        elif 'hickory_proto::xfer::dns_exchange: failed to associate send_message response to the sender' in line.decode() and mute_hickory:
            continue
        
        elif "INFO single_disk_farm{disk_farm_index=" in line.decode() and "subspace_farmer::single_disk_farm::plotting: Plotting sector" in line.decode():
            get_plot_stats(line.decode())
        # TODO Print chart of above data points
        
        print(local_time(line.decode()))
        with open("farmlog.txt", "a+") as file:
            file.write(local_time(line.decode()) + '\n')
    
# RUN COMMAND - run specific file with arguments to capture output.
# Every argument must be added in quotes and comma separated for the key and value.
# i.e.: farm is its own, --reward address is its own, the value for the reward address is on its own, etc.

#Below is multi farms on Windows

# TODO Make the params easier to add
run_command(
    ['subspace-farmer-windows-x86_64-skylake-gemini-3g-2024-jan-24.exe', 'farm', '--reward-address',
     'YOUR_WALLET_ADDRESS_HERE', 'path=z:\\subspace-farm,size=900G',
     'path=x:\\subspace-farm,size=460G', 'path=y:\\subspace-farm,size=890G', '--farm-during-initial-plotting=true'],
    cwd=Path(__file__).parent.absolute())
