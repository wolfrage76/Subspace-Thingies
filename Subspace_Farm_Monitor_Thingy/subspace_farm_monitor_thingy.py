#BitcoinBart was here

import subprocess
from pathlib import Path
from datetime import datetime 
import os
import yaml
import time
import sys

with open("config.yaml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

if config['NODE_EXECUTABLE_FOLDER']:
    os.chdir(config['NODE_EXECUTABLE_FOLDER']) # Where your node executable file is located
elif config['NODE_FOLDER']:
    os.chdir(config['NODE_FOLDER']) # In case someone has an old config

#################

reward_phrase = 'reward_signing: Successfully signed reward hash' # This is dumb. Need to handle better.


def send(msg=None):
    #### Discord

    if config['SEND_DISCORD'] and config['DISCORD_WEBHOOK'] and msg:

        import requests
        data = {"content": msg}
        response = requests.post(config['DISCORD_WEBHOOK'], json=data)
        success_list = [204]
        if response.status_code not in success_list:
            print('Error sending Discord: ' + str(response.status_code))

    ##### Pushover

    if config['SEND_PUSHOVER'] and config['PUSHOVER_APP_TOKEN'] and config['PUSHOVER_USER_KEY'] and msg:
        import http.client, urllib
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
                     urllib.parse.urlencode({
                         "token": config['PUSHOVER_APP_TOKEN'],
                         "user": config['PUSHOVER_USER_KEY'],
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
    
        while True:
            #send('Starting farmer monitor...')
            try:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    **kwargs,
                )
                
                #output,error = process.communicate()
                
                
                while True:
                    try:
                        line = process.stdout.readline()
                        
                        
                        # TODO convert to a list of filters vs singlar
                        
                        if not line and process.poll() is not None: 
                            break
                        
                        elif "(os error " in line.decode():
                            process.kill()
                            print(line.decode())
                            print('retrying in 30 seconds')
                            time.sleep(30)
                            break
                            
                        elif reward_phrase in line.decode():
                            print('\n\n************************************* WINNER! *************************************\n\n')
                            # TODO save to csv block, farm, time, total (pdragon)
                            
                            send('WINNER! You were rewarded!')
                        elif 'Initial plotting complete' in line.decode():
                            print('\n\n************************************* Plot Complete! *************************************\n\n')
                            # TODO Save to csv data as above
                            send('Plot complete: ' + line.decode().split()[2] + ' 100%!')
                            
                        elif 'failed to associate send_message response to the sender' in line.decode() and config['MUTE_HICKORY']:
                            continue
                        
                        elif "INFO single_disk_farm{disk_farm_index=" in line.decode() and "subspace_farmer::single_disk_farm::plotting: Plotting sector" in line.decode():
                            get_plot_stats(line.decode())
                        # TODO Print chart of above data points
                    
                        if  datetime_valid(local_time(line.decode())):
                            print(local_time(line.decode()))
                            with open("farmlog.txt", "a+") as file:
                                file.write(local_time(line.decode()) + '\n')
                        else: 
                            print(line.decode())
                            with open("farmlog.txt", "a+") as file:
                                file.write(line.decode() + '\n')
                    except OSError as e:
                        print("OSError > " + e.errno)
                        print("OSError > " + e.strerror)
                        print("OSError > " + e.filename)
                    except:
                        print("Error > " + str(sys.exc_info()[0]))
                        
                        print('Exception: Retrying in 5 minutes ') # Set correct after testing
                        time.sleep(10)
            except OSError as e:
                print("OSError > " + e.errno)
                print("OSError > " + e.strerror)
                print("OSError > " + e.filename)
            except:
                print("Error > " + str(sys.exc_info()[0]))
                
                print('Exception: Retrying in 5 minutes ') # Set correct after testing
                time.sleep(10)
   
        

# RUN COMMAND - run specific file with arguments to capture output.

cmd = config['COMMANDLINE']

run_command(cmd.split(),
    
    cwd=Path(__file__).parent.absolute())
