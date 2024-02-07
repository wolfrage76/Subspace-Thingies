import time
import utilities.conf as c
import sys
from datetime import datetime

### Init ###
last_claimed = 0

############
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
        if c.hour_24:
            string2[0] = datestamp.strftime("%m-%d %H:%M:%S|")    
        else:
            string2[0] = datestamp.strftime("%m-%d %I:%M %p|").replace(' PM','pm').replace(' AM', 'am')
        
        for piece in string2:

            my_string += '{} '.format(piece)
        my_string = my_string
    else:
        my_string=string
    return(my_string)

def main():
    while True:

                    try:
                        
                      with open(c.node_log_file, 'r', encoding = "utf-16") as file:
                        while True:
                            
                            line = file.readline()
                            line_plain = line.encode('ascii', 'ignore').decode()                             
                            
                            if line == "\r\n" or line == "\n" or line == "":
                                continue
                            elif "peers), best: " in line_plain:
                                c.peers = line_plain.split()[5][+1:]
                                c.best_block = line_plain.split()[8]
                                c.finalized = line_plain.split()[11]
                                c.ul = line_plain.split()[13]
                                c.dl = line_plain.split()[14]
                                
                            elif "INFO Consensus: substrate:" in line_plain and "Imported" in line_plain:
                                 test = line_plain.split()
                                 c.imported = line_plain.split()[5].replace('#\x1b[1;37m','').replace('\x1b[0m','')
                                 line_plain =  line_plain.replace('#\x1b[1;37m','').replace('\x1b[0m','').format(line_plain)
                                 
                            elif "Claimed block at slot" in line_plain:
                                last_claimed = line_plain[7]
                            elif "Pre-sealed block for proposal at" in line_plain:
                                if line_plain.split()[7] == last_claimed:
                                    c.rewards += c.farm_rewards
                                    farm = line_plain[line_plain.find("{disk_farm_index=") + len("{disk_farm_index="):line_plain.find("}:")]
                                    c.farm_rewards[farm] += c.farm_rewards[farm]
                                else:
                                    last_claimed = 0
                            
                            c.last_node_logs.pop(0)
                            c.last_node_logs.append(local_time(line_plain)) #.replace('\n','').replace(' INFO', '[white]').replace(' WARN','[yellow]').replace('ERROR','[red]')))                     
                    except:
                        print("Node Error > " + str(sys.exc_info()[0]))
                        print('Exception: Retrying in 5 minutes ') # Set correct after testing
                        time.sleep(5)  #  before I tweak exceptions