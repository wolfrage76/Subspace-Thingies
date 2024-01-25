#BitcoinBart was here

import subprocess
import os
from pathlib import Path

discord_webhook = ''
pushover_app_token = ''
pushover_api = ''
send_discord = True
send_pushover = False

os.chdir('C:\\Users\\bitcoinbart\\subspace')
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


def run_command(command, **kwargs):
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        **kwargs,
    )

    while True:
        line = process.stdout.readline()

        if not line and process.poll() is not None:
            break
        elif reward_phrase in line.decode():
            print('\n\n************************************* WINNER! *************************************\n\n')

            send('WINNER! You were rewarded!')
        elif '100% complete' in line.decode():
            print('\n\n************************************* Plot Complete! *************************************\n\n')
            send('Plot complete: ' + line.decode().split()[2] + ' 100%!')

        print(line.decode(), end='')
        with open("farmlog.txt", "a+") as file:
            file.write(line.decode() + '\n')

# RUN COMMAND - run specific file with arguments to capture output.
# Every argument must be added in quotes and comma separated for the key and value.
# i.e.: farm is its own, --reward address is its own, the value for the reward address is, etc.

#Below is muti farms on Windows

run_command(
    ['subspace-farmer-windows-x86_64-skylake-gemini-3g-2024-jan-24.exe', 'farm', '--reward-address',
     'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', 'path=f:\\subspace-farm,size=900G',
     'path=i:\\subspace-farm,size=460G', 'path=k:\\subspace-farm,size=890G', '--farm-during-initial-plotting=true'],
    cwd=Path(__file__).parent.absolute())
