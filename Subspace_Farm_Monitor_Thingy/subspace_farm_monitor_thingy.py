#BitcoinBart was here

import subprocess
from pathlib import Path
from datetime import datetime
from os import chdir
import yaml
import time
import sys
import threading
import os

from rich import print
import conf as c

import wallet
import view
import node_monitor


global disk_farms, reward_count, event_times, farm_rewards, farm_plot_size, curr_sector, errors, total_error_count,curr_farm, plot_space, drive_directory

# Initialize state
disk_farms = c.disk_farms
reward_count = c.reward_count
farm_rewards = c.farm_rewards

event_times = c.event_times
plot_space = c.plot_space
drive_directory = c.drive_directory
farm_plot_size = c.farm_plot_size
curr_sector_disk = c.curr_sector_disk
errors = c.errors
total_error_count = c.total_error_count
curr_farm = c.curr_farm
no_more_drives = c.no_more_drives


with open("config.yaml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

#################
c.wallet = config['WALLET']
c.node_log_file = config['NODE_LOG_FILE']
#if config['NODE_EXECUTABLE_FOLDER']:
   # os.chdir(config['NODE_FOLDER']) # Where your node executable file is located
    
reward_phrase = 'reward_signing: Successfully signed reward hash' # This is dumb. Need to handle better.

c.startTime = time.time()

def wallet_thread():
    wallet.WalletMon()

def console_thread():
 view.main()

def node_thread():
 node_monitor.main()
 
 
consoleguithread = threading.Thread(target=console_thread, name='Console', daemon=True)
walletthread = threading.Thread(target=wallet_thread, name='Wallet', daemon=True)
nodethread = threading.Thread(target=node_thread, name='Node', daemon=True)

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
        string2[0] = datestamp.strftime("%m-%d-%Y %H:%M:%S|")

        for piece in string2:

            my_string += '{} '.format(piece)
        my_string = my_string
    else:
        my_string=string
    return(my_string)

def make_csv(str):  #setup .csv to import into other stuff
    pass

    
def run_command(command, **kwargs):
    
    
    consoleguithread.start() # View
    walletthread.start()
    nodethread.start()
    send('Starting farmer monitor...')
           
    while True:
            try:
                if config['IS_LIVE']:
            
                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        **kwargs,
                    )
                else:
                   pass
               
                if not config['IS_LIVE']:
                            file = open(config['FARMER_LOG'], 'r') # These 3 work
                
                while True:              
                    try:
    #                      
               
                            if config['IS_LIVE'] == False:
                                line = file.readline()
                                line_plain = line                              
                            else:
                                line = process.stdout.readline()
                                line_plain = line.decode()
                            
                            if line_plain == "\r\n" or line_plain == "\n" or line_plain == "":
                                continue
                            
                            
                            c.last_logs.pop(0)
                            c.last_logs.append(local_time(line_plain.replace('\n','').replace(' INFO', '[white]').replace('subspace_farmer::single_disk_farm::plotting:','')).replace(' WARN','[yellow]'))
                            
                            if not line and process.poll() is not None and config['IS_LIVE']: 
                                break
                            
                            
                            elif line == '' or line == '\r\n' or line == '\n':
                                continue
                            elif "(os error " in line_plain:
                                process.kill()
                                print(line_plain)
                                print('retrying in 30 seconds')
                                time.sleep(30)
                                break
                            elif "Single disk farm" in line_plain:
                            
                                check_header = True
                                
                                farm = line_plain[line_plain.find("Single disk farm ") +len("Single disk farm "):line_plain.find(":")]
                                if farm not in disk_farms:
                                    
                                    disk_farms.add(farm)
                                    
                                curr_farm = farm
                                c.curr_farm = curr_farm    
                            #elif 'Finished collecting already plotted pieces successfully' in line_plain:
                            elif "plotting" in line_plain and not "Subscribing to archived segments" in line_plain :
                                farm =   line_plain[line_plain.find("{disk_farm_index=") + len("{disk_farm_index="):line_plain.find("}")]
                                if farm:
                                    curr_farm = farm
                                    if "Replotting complete" in line_plain or "Initial plotting complete" in line_plain:
                                        farm_plot_size[farm] = "100"
                                    else:
                                        plot_size = line_plain[line_plain.find("(")+1:line_plain.find("%")]
                                        if plot_size:
                                            farm_plot_size[farm] = line_plain[line_plain.find("(")+1:line_plain.find("%")]
                                            curr_sector_disk[farm] = line_plain[line_plain.find("sector_index=")+ len("sector_index="):line_plain.find("\n")]
                                            event_times[farm] = line_plain.split()[0]
                            
                            elif 'Allocated space: ' in line_plain and curr_farm:
                                allocated_space = line_plain[line_plain.find(":") + 2:line_plain.find("(")-1]
                                
                                plot_space[curr_farm] = allocated_space
                            
                                #continue
                            elif 'Directory:' in line_plain and curr_farm:
                                directory = line_plain[line_plain.find(":") + 2:]
                                drive_directory[curr_farm] = directory
                                curr_farm = None
                                #    #farms.append({'sdf': sdf, 'allocated_space': allocated_space, 'directory': directory})
                        
                            elif reward_phrase in line_plain:
                                c.reward_count += 1
                                farm = line_plain[line_plain.find("{disk_farm_index=") + len("{disk_farm_index="):line_plain.find("}:")]
                                
                                if farm:
                                    farm_rewards[ line_plain[line_plain.find("{disk_farm_index=") + len("{disk_farm_index="):line_plain.find("}:")]] += 1
                                    
                                print('\n****************** Vote Winner! ******************\n')
                                # TODO save to csv block, time (pdragon)
                                
                                send('WINNER! You were rewarded for Vote!')
                            elif 'Initial plotting complete' in line_plain:
                                print('\n\n************************************* Plot Complete! *************************************\n\n')
                                
                                # TODO Save to csv data as above - update Recent Events in footer
                                send('Plot complete: ' + line_plain.split()[2] + ' 100%!')
                                #continue
                                                    
                            elif 'failed to associate send_message response to the sender' in line_plain and config['MUTE_HICKORY']:
                                pass

                            elif 'WARN quinn_udp: sendmsg error:' in line_plain :
                                continue
                                        
                            
                            with open("farmlog.txt", "a+") as file2:
                                file2.write(local_time(line_plain)+'\n')
                            
                    except OSError as e:
                        print("OSError > " + e.errno)
                        print("OSError > " + e.strerror)
                        print("OSError > " + e.filename)
                    except:

                        print("Error > " + str(sys.exc_info()[0]))
                        
                        print('Exception: Retrying in 5 minutes ') # Set correct after testing
                        time.sleep(300)
            except OSError as e:
                    print("OSError > " + str(e.errno))
                    print("OSError > " + e.strerror)
                    print("OSError > " + e.filename)
            except:
                print("Error > " + str(sys.exc_info()[0]))
                
                print('Exception: Retrying in 5 minutes ') # Set correct after testing
                time.sleep(300)

        

# RUN COMMAND - run specific file with arguments to capture output.

cmd = config['COMMANDLINE']

run_command(cmd.split(),
    
    cwd=Path(__file__).parent.absolute())
