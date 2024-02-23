import subprocess
from pathlib import Path
from datetime import datetime, timezone
import dateutil.parser
import yaml
import time
import threading
import utilities.conf as c
import utilities.websocket_client as websocket_client
from rich import print

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

c.node_log_file = config.get('NODE_LOG_FILE', '')
c.show_logging = config.get('SHOW_LOGGING', False)
c.hour_24 = config.get('HOUR_24', False)
c.farmer_name = config.get('FARMER_NAME', '')
c.front_end_ip = config.get('FRONT_END_IP')
c.front_end_port = config.get('FRONT_END_PORT', "9944")

reward_phrase = 'reward_signing: Successfully signed reward hash'

c.startTime = time.time()

def socket_client_thread():
    while True:
        websocket_client.main()
        time.sleep(30)
    
socketclientthread = threading.Thread(target=socket_client_thread, name='SocketClient', daemon=True)

socketclientthread.start()


#from datetime import datetime, timedelta

# Assuming c.sector_times is a dictionary where each key is a disk identifier and each value is a list of timedelta objects representing operation times for each sector
# Example: c.sector_times = {'disk1': [timedelta(seconds=30), timedelta(seconds=45)], 'disk2': [timedelta(seconds=25), timedelta(seconds=35)]}

def calculate_average_sector_time(disk):
    """
    Calculate the average sector operation time for a given disk.
    """
    sector_times = c.sector_times.get(disk, [])
    if not sector_times:
        return None  # Or some default value indicating no data
    
    total_time = sum(sector_times, timedelta())
    average_time = total_time / len(sector_times)
    return average_time

# Example usage:
# average_time = calculate_average_sector_time('disk1')
# print(f"Average sector time for disk1: {average_time}")


def local_time(string):
    my_string = ''
    string2 = string.split(' ')
    convert = string2[0]
    
    if datetime_valid(convert):    
        datestamp = datetime.fromisoformat(str(convert)).astimezone(tz=None)
        if c.hour_24:
            string2[0] = datestamp.strftime("%m-%d %H:%M:%S|")    
        else:
            string2[0] = datestamp.strftime("%m-%d %I:%M %p|").replace(' PM',' pm').replace(' AM', ' am')

        for piece in string2:
            my_string += '{} '.format(piece)
        my_string = my_string
    else:
        my_string=string
    return(my_string)

def datetime_valid(dt_str):
    try:
        datetime.fromisoformat(dt_str)
    except:
        return False
    return True

def parse_log_line(line_plain, curr_farm, reward_count, farm_rewards, event_times, plot_space, drive_directory, farm_plot_size, curr_sector_disk):
    trigger = False
    parsed_data = {
        'line_plain': '',  # Default value
        'curr_farm': curr_farm,
        'reward_count': reward_count,
        'farm_rewards': farm_rewards,
        'event_times': event_times,
        'plot_space': plot_space,
        'drive_directory': drive_directory,
        'farm_plot_size': farm_plot_size,
        'curr_sector_disk': curr_sector_disk
    }
    
    line_timestamp_str = line_plain.split()[0]  # Assuming the first part of the line is the timestamp
    if datetime_valid(line_timestamp_str):
        line_timestamp = dateutil.parser.parse(line_timestamp_str).astimezone(timezone.utc).timestamp()
    else:
        line_timestamp = None
        
    if "ERROR" in line_plain:
        c.errors.pop(0)
        c.errors.append(local_time(line_plain.replace('\n','').replace(' ERROR','[b red]')))
        
    if "WARN" in line_plain:
        c.warnings.pop(0)
        c.warnings.append(local_time(line_plain.replace('\n','').replace(' WARN','[b yellow]')))
        
    if "INFO" in line_plain:
        c.warnings.pop(0)
        c.warnings.append(local_time(line_plain.replace('\n','').replace(' WARN','[b white]')))
        
    """ c.last_logs.pop(0)
    c.last_logs.append(local_time(line_plain.replace('single_disk_farm{disk_farm_index=', 'Farm: ').replace('}: ','').replace('sector_index=', 'Current Sector: ').replace('\n','').replace(' INFO', '[white]').replace('subspace_farmer::single_disk_farm::plotting:','')).replace(' WARN','[yellow]').replace('subspace_farmer::', '').replace ('single_disk_farm::farming:', ' '))
     """
    if "(os error " in line_plain:
        print(line_plain)
        print('retrying in 30 seconds')
        time.sleep(30)
        return parsed_data
    elif 'hickory' in line_plain and config['MUTE_HICKORY']:
        pass
    elif 'WARN quinn_udp: sendmsg error:' in line_plain:
        pass
    elif "Single disk farm" in line_plain:
        check_header = True
        farm = line_plain[line_plain.find("Single disk farm ") + len("Single disk farm "):line_plain.find(":")]
        if farm not in disk_farms:
            disk_farms.add(farm)
        curr_farm = farm
        c.curr_farm = curr_farm
    elif ("plotting" in line_plain or "Replotting" in line_plain) and not "Subscribing to archived segments" in line_plain:
        farm = line_plain[line_plain.find("{disk_farm_index=") + len("{disk_farm_index="):line_plain.find("}")]
        if 'Replotting' in line_plain:
            c.replotting[farm] = True
            c.sector_times[farm] == 0
        if farm:
            curr_farm = farm
            
            c.curr_farm = farm
            if "Replotting complete" in line_plain or "Initial plotting complete" in line_plain:
                farm_plot_size[farm] = "100"
            else:
                t = line_plain.split()[0]
                from dateutil.parser import parse
                from dateutil.relativedelta import relativedelta
                if c.sector_times[farm] == 0:
                    delta = 0
                else:
                    datetime_1 = parse(t)
                    datetime_2 = parse(c.sector_times[farm])
                    #datetime_2 = datetime_2.replace(tzinfo=tz.tzlocal())

                    # Now both datetime_1 and datetime_2 are in the user's local timezone
                    delta = relativedelta(datetime_1, datetime_2)
                    #delta = relativedelta(datetime_1, datetime_2)
                    c.deltas[farm] = str(delta.minutes) + ':' + str(delta.seconds).rjust(2, '0')
                c.sector_times[farm] = t
                plot_size = line_plain[line_plain.find("(")+1:line_plain.find("%")]
                if plot_size:
                    farm_plot_size[farm] = line_plain[line_plain.find("(")+1:line_plain.find("%")]
                    curr_sector_disk[farm] = line_plain[line_plain.find("sector_index=")+ len("sector_index="):]
                    event_times[farm] = line_plain.split()[0]
        #websocket_client.main()
        trigger = True
    elif 'Allocated space: ' in line_plain and c.curr_farm:
        allocated_space = line_plain[line_plain.find(":") + 2:line_plain.find("(")-1]
        plot_space[c.curr_farm] = allocated_space
    elif 'Directory:' in line_plain and c.curr_farm:
        directory = line_plain[line_plain.find(":") + 2:]
        drive_directory[c.curr_farm] = directory
        c.curr_farm = None
    elif reward_phrase in line_plain:
        reward_count += 1
        farm = line_plain[line_plain.find("{disk_farm_index=") + len("{disk_farm_index="):line_plain.find("}:")]
        if farm:
            if farm not in farm_rewards:
                farm_rewards[farm] = 0
            farm_rewards[farm] += 1
        trigger = True
        if line_timestamp and line_timestamp > c.startTime:
            send(config['FARMER_NAME'] + '| WINNER! You were rewarded for Vote!')
    if 'Initial plotting complete' in line_plain:
        if line_timestamp and line_timestamp > c.startTime:
            send(config['FARMER_NAME'] + '| Plot complete: ' + line_plain.split()[2] + ' 100%!')
        trigger = True
        
    if trigger:
        #websocket_client.main()
        trigger = False
    
    parsed_data['line_plain'] = local_time(line_plain)
    return parsed_data



def read_log_file():
    log_file_path = Path(config['FARMER_LOG'])
    with log_file_path.open('r') as log_file:
        while True:
            line = log_file.readline()
            if not line:
                time.sleep(0.1)  # Wait for new lines
                continue
            line_plain = line.strip()
            if not line_plain:
                continue
            parsed_data = parse_log_line(line_plain, curr_farm, reward_count, farm_rewards, event_times, plot_space, drive_directory, farm_plot_size, curr_sector_disk)
            print(parsed_data['line_plain'])  # Print the line to console
            if config['IS_LIVE']:
                with open("farmlog.txt", "a+") as file2:
                    file2.write(parsed_data['line_plain'] + '\n')  # Write the line to farmlog.txt

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

read_log_file()

def run_command(command, **kwargs):
    if config['IS_LIVE']:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            **kwargs,
        )
        for line in iter(process.stdout.readline, b''):
            line_plain = line.decode().strip()
            if not line_plain:
                continue
            parse_log_line(line_plain)
    else:
        threading.Thread(target=read_log_file, daemon=True, name='Read_log').start()

# RUN COMMAND - run specific file with arguments to capture output.
cmd = config['COMMANDLINE']

while True:
    run_command(cmd.split(), cwd=Path(__file__).parent.absolute())
