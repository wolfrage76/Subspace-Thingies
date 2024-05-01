import psutil
from pathlib import Path
from datetime import timedelta, timezone, datetime
import dateutil.parser
import yaml
import time
import threading
import utilities.conf as c
import utilities.websocket_client as websocket_client
from rich import print
import re
from dateutil.parser import parse
import requests
from rich.console import Console
import http.client
import urllib
import os


# Initialize state
#c.dropped_drives = []
last_notification_time = {}
notification_count = {}
last_notification_time = {}
notification_count = {}
c.system_stats = {}
system_stats = c.system_stats

disk_farms = c.disk_farms
reward_count = c.reward_count
farm_rewards = c.farm_rewards
farm_recent_rewards = c.farm_recent_rewards
farm_skips = c.farm_skips
farm_recent_skips = c.farm_recent_skips
drive_directory = c.drive_directory
errors = c.errors
total_error_count = c.total_error_count
curr_farm = c.curr_farm


indexconst = "{farm_index="


with open("config.yaml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)


c.hour_24 = config.get('HOUR_24', False)
c.farmer_name = config.get('FARMER_NAME', 'WolfrageRocks')
c.front_end_ip = config.get('FRONT_END_IP', "127.0.0.1")
c.front_end_port = config.get('FRONT_END_PORT', "8016")
farmer_ip = config.get('FARMER_IP', "127.0.0.1")
farmer_port = config.get('FARMER_PORT', "8181")

reward_phrase = 'reward_signing: Successfully signed reward hash'

dt = datetime.now(timezone.utc) 
  
utc_time = dt.replace(tzinfo=timezone.utc) 
utc_timestamp = utc_time.timestamp() #
c.startTime = utc_timestamp
monitorstartTime = utc_timestamp


def process_farmer_metrics(metrics, farm_id_mapping):
    metrics_dict = {}
    wanted = ['process_start_time_seconds','subspace_farmer_sectors_total_sectors', 'subspace_farmer_sector_plot_count', 'subspace_farmer_sector_notplotted_count', 'subspace_farmer_sector_index','subspace_farmer_sector_plotting_time_seconds_count', 'subspace_farmer_sector_plotting_time_seconds_sum', 'subspace_farmer_sectors_total_sectors_Plotted', 'subspace_farmer_sectors_total_sectors_Expired', 
    'subspace_farmer_sectors_total_sectors_AboutToExpire', 'subspace_farmer_auditing_time_seconds_sum', 'subspace_farmer_auditing_time_seconds_count', 'subspace_farmer_proving_time_seconds_sum', 'subspace_farmer_proving_time_seconds_count',]

    for metric in metrics:
        if metric.startswith('subspace_farmer_') and 'farm_id="' in metric:
            parts = metric.split()
            metric_name = parts[0].split('{')[0]
            if '_bucket' in metric_name or metric_name not in wanted:
                continue

            value = parts[-1]
            labels = parts[0].split('{')[1].split('}')[0]
            labels_dict = {label.split('=')[0]: label.split('=')[1].strip('"') for label in labels.split(',')}
            farm_id = labels_dict.get('farm_id')
            
            # Find the disk index corresponding to this farm_id
            disk_index = None
            for index, fid in farm_id_mapping.items():       
                if fid == farm_id:
                    disk_index = index
                    break
            
            if disk_index is not None:
                if disk_index not in metrics_dict:
                    metrics_dict[disk_index] = {}
                # Handle metrics with the 'state' label
                if 'state' in labels_dict:
                    state = labels_dict['state']
                    metric_key = f"{metric_name}_{state}"
                else:
                    metric_key = metric_name
                metrics_dict[disk_index][metric_key] = {'value': value, 'labels': labels_dict}
                
    return metrics_dict



'''subspace_farmer_sectors_total_sectors: Total sectors in the farmer.
subspace_farmer_sector_index: Current sector index being plotted.
subspace_farmer_sector_plot_count: Total plots completed.
subspace_farmer_sector_notplotted_count: Total plots remaining.
subspace_farmer_sector_expired_count: Total plots expired.
subspace_farmer_sector_abouttoexpire_count: Total plots about to expire.
subspace_farmer_auditing_time_seconds_count: Auditing time for the farmer.
subspace_farmer_sector_plotting_time_seconds: Time taken for plotting sectors.
subspace_farmer_proving_time_seconds: Time taken for proving sectors.
subspace_farmer_proving_success_count: Count of successful proofs.
subspace_farmer_proving_timeout_count: Count of proofs that timed out.
subspace_farmer_proving_rejected_count: Count of rejected proofs.'''

def get_farmer_metrics(farmer_ip, farmer_port, wait=60):
    url = f"http://{farmer_ip}:{farmer_port}/metrics"
    max_logs = 3  # Maximum number of log files to keep
    metricslog = []
    try:
        response = requests.get(url)
        response.raise_for_status()
        c.connected_farmer = True
        metrics = response.text.split('\n')
        metricslog = [line for line in response.text.split('\n') ] # if "bucket" not in line]

        if config.get('METRIC_LOGGING', False):
            # Writing filtered metrics to a new log file in the current directory
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log_filename = f"metrics_log_{timestamp}.txt"
            with open(log_filename, 'w') as log_file:
                log_file.write("\n".join(metricslog))

            # Identifying log files based on naming convention for cleanup
            log_files = [f for f in os.listdir(".") if re.match(r'^metrics_log_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.txt$', f)]
            log_files.sort(key=os.path.getmtime, reverse=True)

            # Deleting old log files, ensuring only logs are targeted
            for log_file in log_files[max_logs:]:
                os.remove(log_file)

        return metrics
    except requests.exceptions.RequestException as e:
        c.startTime = 0 # parsed_datetime = datetime.fromisoformat(lt.replace('Z', '+00:00')).timestamp()
        c.connected_farmer = False
        #print(f"Error fetching farmer metrics (30 second retry): {e}")
        time.sleep(wait)
        return [] 
    
    
def update_farm_metrics(farm_id_mapping):
    
    metrics = get_farmer_metrics(farmer_ip, farmer_port)
    processed_metrics = process_farmer_metrics(metrics, farm_id_mapping)
    all_metrics = c.farm_metrics
    for disk_index, metrics in processed_metrics.items():
        if disk_index in c.disk_farms:
            audit_sum =  float(c.farm_metrics.get(disk_index,{}).get('subspace_farmer_auditing_time_seconds_sum',{}).get('value', 0))
            audit_count = float(c.farm_metrics.get(disk_index,{}).get('subspace_farmer_auditing_time_seconds_count',{}).get('value', 0))
            
            prove_sum = float(c.farm_metrics.get(disk_index,{}).get('subspace_farmer_proving_time_seconds_sum',{}).get('value', 0))
            prove_count = float(c.farm_metrics.get(disk_index,{}).get('subspace_farmer_proving_time_seconds_count',{}).get('value', 0))
            
            if prove_count == 0 or prove_sum == 0:
                c.proves[disk_index] =  0
            else:
                c.proves[disk_index] = prove_sum / prove_count
                
            if audit_count == 0 or audit_sum == 0:
                c.audits[disk_index] =  0
            else:
                c.audits[disk_index] = 1000 * (audit_sum / audit_count)
            
            all_metrics[disk_index] = metrics
           
    c.farm_metrics = all_metrics


def socket_client_thread():
    
    while True:
        websocket_client.main()
        time.sleep(15)
        #print("FIX THIS TIMER!")

def update_metrics_periodically(interval=10):
    while True:
        c.rewards_per_hr = 0
        for disk_index in disk_farms:
            one_day_ago = datetime.now().timestamp() - 86400
            c.farm_recent_rewards[disk_index] = len([r for r in c.farm_reward_times[disk_index] if r > one_day_ago])
            c.farm_recent_skips[disk_index] = len([r for r in c.farm_skip_times[disk_index] if r > one_day_ago]) 
            c.rewards_per_hr += calculate_rewards_per_hour(c.farm_reward_times[disk_index])
            
        update_farm_metrics(c.farm_id_mapping)
        time.sleep(interval)

metrics_thread = threading.Thread(target=update_metrics_periodically, daemon=True)
metrics_thread.start()

socketclientthread = threading.Thread(
    target=socket_client_thread, name='SocketClient', daemon=True)

socketclientthread.start()

def reset_notification_count(farm):
    notification_count[farm] = 0
    
def stop_error_notification(farm):
    current_time = time.time()
    min_cooldown = 300  # Minimum cooldown period in seconds (5 minutes)

    if farm in last_notification_time:
        elapsed_time = current_time - last_notification_time[farm]
        # Calculate current cooldown
        current_cooldown = min_cooldown * (2 ** notification_count[farm])

        if elapsed_time < current_cooldown:
            return  # Skip sending notification if within the cooldown period

        # Increase the count for consecutive notifications
        notification_count[farm] += 1
    else:
        # First notification
        notification_count[farm] = 0

    last_notification_time[farm] = current_time
    # Send the notification
    send(config['FARMER_NAME'] + '| ERROR - Drive Dropped Off: ' + farm)

    # Reset the notification count if no further errors in 2x the last cooldown
    reset_cooldown = min_cooldown * (2 ** (notification_count[farm] + 1))
    threading.Timer(reset_cooldown, reset_notification_count, [farm]).start()
    
    
    
def datetime_valid(dt_str):
    try:
        # Explicitly handle the 'Z' UTC designation
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1] + '+00:00'
        parse(dt_str)
        return True
    except ValueError:
        return False

def convert_to_utc_with_offset_zulu(date_time_str, utc_offset=0):
    #local_dt = datetime()
    # Validate input types
    if not isinstance(date_time_str, str):
       return date_time_str # raise ValueError("date_time_str must be a string")
    if not isinstance(utc_offset, int):
        utc_offset = 0
        #return date_time_str # raise ValueError("utc_offset must be an integer")
    try:
        # Parse the date-time string
        if config.get("U_GPU_PLOTTER", 'False'):
            local_dt = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S.%f")
        else:
            local_dt = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError as e:
        #raise ValueError("Error parsing date_time_str: ensure it's in 'dd-mm-yy HH:MM:SS.mmm' format") from e
        #pass
        return date_time_str
    
    # Calculate the offset as a timedelta
    offset = timedelta(hours=utc_offset)
    
    # Apply the offset to get UTC time
    utc_dt = local_dt - offset
    
    # Return the UTC datetime in Zulu time format
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + 'Z'

def local_time(string):
    string2 = string.split(' ')
    convert = string2[0]
    
    if config.get('U_GPU_PLOTTER', False):
        convert = string2[0] + ' ' + string2[1]
        convert = convert_to_utc_with_offset_zulu(convert, config.get('timezone_offset', 0)) + '+00:00'
        

    
    if datetime_valid(convert):
        # Handle 'Z' for UTC time explicitly
        if convert.endswith('Z'):
            convert = convert[:-1] + '+00:00'
        datestamp = parse(convert)

        # Convert to local timezone
        local_tz = dateutil.tz.tzlocal()
        datestamp = datestamp.astimezone(tz=local_tz)
  
        if c.hour_24:
            formatted_timestamp = datestamp.strftime("%m-%d %H:%M:%S|")
        else:
            formatted_timestamp = datestamp.strftime(
                "%m-%d %I:%M:%S %p|").replace(' PM', 'pm').replace(' AM', 'am')

        # Return the formatted timestamp followed by the rest of the original string, excluding the original timestamp
        return formatted_timestamp + ' ' + ' '.join(string2[1:])
    else:
        return string  # If the timestamp is invalid, return the original string

def calculate_rewards_per_hour(farm_rewards):
    dt = datetime.now(timezone.utc) 
  
    utc_time = dt.replace(tzinfo=timezone.utc) 
    utc_timestamp = utc_time.timestamp() 
    one_day_ago = utc_timestamp - 86400
    
    #one_day_ago = datetime.now(timezone.utc).timestamp() - 86400  # 24 hours ago
    
    recent_rewards = [r for r in farm_rewards if r > one_day_ago] 
    #print(str(one_day_ago) + " \n" + str(farm_rewards) + ' \n' + str(recent_rewards))
    
    return len(recent_rewards) / 24  

def rewards_per_day_per_tib(farm_rewards, farm, total_plotted_tib):
    one_day_ago = datetime.now().timestamp() - 86400  # 24 hours ago
    recent_rewards = [r for r in farm_rewards.get(farm, []) if r > one_day_ago]
    total_rewards_last_24_hours = len(recent_rewards)
    return total_rewards_last_24_hours / total_plotted_tib  # don't forget /0


def parse_log_line(line_plain, curr_farm, reward_count, farm_rewards, farm_recent_rewards, drive_directory, farm_skips, farm_recent_skips, system_stats, farm_id_mapping, ):


  
    trigger = False
    parsed_data = {
        'line_plain': '',  # Default value
        'curr_farm': curr_farm,
        'reward_count': reward_count,
        'farm_rewards': farm_rewards,
        'farm_recent_rewards': farm_recent_rewards,
        'drive_directory': drive_directory,
        'farm_skips': farm_skips,
        'farm_recent_skips': farm_recent_skips,
        'system_stats': system_stats,
    }

    # Assuming the first part of the line is the timestamp
    
    if config.get("U_GPU_PLOTTER", False):
        line_timestamp_str = line_plain.split()[0] + ' ' + line_plain.split()[1]
        
    else:
        line_timestamp_str = line_plain.split()[0]
    
    
    if 'groups detected l3_cache_groups=' in line_plain:
        c.l3_concurrency = int(line_plain.split('groups detected l3_cache_groups=')[1])
    
    if datetime_valid(line_timestamp_str):
        line_timestamp = dateutil.parser.parse(
            line_timestamp_str).astimezone(timezone.utc).timestamp()
        parsed_datetime = line_timestamp # datetime.fromisoformat(line_plain.split('Z')[0].replace('Z', '+00:00')).replace(tzinfo=timezone.utc).timestamp()
        
    else:
        line_timestamp = None
    if 'Finished collecting already plotted pieces' in line_plain:   # checking for farmer startup

        c.startTime = line_timestamp
        farm_id_mapping = {}
        drive_directory = {}
        curr_farm = None
       
        c.l3_timestamps.clear()
        for x in range(c.l3_concurrency * 2):
            c.l3_timestamps = c.l3_timestamps + [ line_timestamp ]
        c.dropped_drives = []
        
        
    farm = line_plain[line_plain.find(
            indexconst) + len(indexconst):line_plain.find("}")]


    if "ERROR" in line_plain:
        c.errors.pop(0)
        c.errors.append(local_time(line_plain.replace(
            '\n', '').replace(' ERROR', '[b red]')))

    if "WARN" in line_plain:
        c.warnings.pop(0)
        c.warnings.append(local_time(line_plain.replace(
            '\n', '').replace(' WARN', '[b yellow]')))
    
    if 'exited' in line_plain:
        pass
    
    
    elif "ID: " in line_plain:
        
        farm_id = line_plain.split(' ID: ')[1]
        farm_index = line_plain[line_plain.find(indexconst) + len(indexconst):line_plain.find('}')]
        if farm_index and farm_id:
            farm_id_mapping[farm_index] = farm_id
            c.farm_id_mapping[farm_index] = farm_id
    elif 'DSN instance configured.' in line_plain:
        # c.resetting() # Reset some data when new restart detected in log
        pass
    
    elif "enchmarking faster proving method" in line_plain:
        pass
    elif 'Farm exited with error farm_index=' in line_plain and parsed_datetime > monitorstartTime:
        farm = line_plain.split('Farm exited with error farm_index=')[0]
        stop_error_notification(farm)
        
    elif 'Farm errored and stopped' in line_plain and parsed_datetime > monitorstartTime:
            farm = line_plain[line_plain.find(
            indexconst) + len(indexconst):line_plain.find("}")]
            
            c.dropped_drives.append(farm)
            stop_error_notification(farm)   
            #send(config['FARMER_NAME'] +
            #     '| Drive Dropped Off: ' + farm)
            
            
            
    elif 'subspace_farmer::commands::farm: Farm' in line_plain and 'cache worker exited' not in line_plain:

        farm = line_plain[line_plain.find(
            indexconst) + len(indexconst):line_plain.find("}")]
        
        if farm not in disk_farms:
            disk_farms.add(farm)
        curr_farm = farm
        c.curr_farm = curr_farm
        
    elif 'using whole sector elapsed' in line_plain:
        farm = line_plain[line_plain.find(
            indexconst) + len(indexconst):line_plain.find("}")]
        prove_type = 'WC'
        c.prove_method[farm] = prove_type
    elif 'ConcurrentChunks' in line_plain:
        
        prove_type = 'CC'
        c.prove_method[farm] = prove_type
        
    elif "found fastest_mode=" in line_plain:

        prove_type = line_plain.split('fastest_mode=')[1]
        c.prove_method[farm] = prove_type
       # if c.prove_method[farm]
    

    elif "lotting sector" in line_plain:  # as of apr-26-2 version, Replotting Complete should be ignored and Replotting 0.00% need to be counted.

        del(c.l3_timestamps[0])
        c.l3_timestamps = c.l3_timestamps + [ line_timestamp ]
        l3_sum = 0

        for x in range(c.l3_concurrency):
            l3_sum = l3_sum + c.l3_timestamps[x + c.l3_concurrency] - c.l3_timestamps[x]

        if c.l3_concurrency != 0:
            c.l3_farm_sector_time = l3_sum / (c.l3_concurrency * c.l3_concurrency)
        else:
            c.l3_farm_sector_time = 0
        
        # if " Plotting sector (0.00%" in line_plain:
        #    event_times[farm] = line_timestamp
        # if "Replotting sector (0.00%" not in line_plain:
        #    c.last_sector_time[farm] = line_timestamp - event_times[farm]
        # event_times[farm] = line_timestamp
        trigger = True

    elif 'Directory:' in line_plain and c.curr_farm:
       # directory =  line_plain.split('Directory: ')[1] #line_plain[line_plain.find(":") + 2:]
        drive_directory[c.curr_farm] = line_plain.split('Directory: ')[1] #directory
        c.curr_farm = None
    


    elif ("solution skipped due to farming time limit" in line_plain) or ("Solution was ignored" in line_plain):

        farm_skips = c.farm_skips
        
        parsed_datetime = line_timestamp # datetime.fromisoformat(line_plain.split('Z')[0].replace('Z', '+00:00')).replace(tzinfo=timezone.utc).timestamp()
        c.farm_skip_times[farm].append( parsed_datetime )
        # c.farm_skip_times.append(parsed_datetime )
        
        if farm:
            if farm not in farm_skips:
                farm_skips[farm] = 0
            farm_skips[farm] += 1
            c.farm_skips[farm] = farm_skips[farm]
    
    elif reward_phrase in line_plain:
        one_day_ago = datetime.now().timestamp() - 86400
        reward_count += 1
        c.reward_count = reward_count
        parsed_datetime = line_timestamp # datetime.fromisoformat(line_plain.split('Z')[0].replace('Z', '+00:00')).replace(tzinfo=timezone.utc).timestamp()
        #parsed_datetime = datetime.strptime(line_plain.split('Z')[0], "%Y-%m-%dT%H:%M:%S.%f")
        c.farm_reward_times[farm].append(parsed_datetime )
        
        farm = line_plain[line_plain.find(
            indexconst) + len(indexconst):line_plain.find("}:")]
        if farm:
            if farm not in farm_rewards:
                farm_rewards[farm] = 0
            farm_rewards[farm] += 1
            c.farm_rewards[farm] = farm_rewards[farm]
            
        #line_timestamp = dateutil.parser.parse(line_timestamp_str).astimezone(timezone.utc).timestamp()
        if parsed_datetime > monitorstartTime:
            send(config['FARMER_NAME'] +
                 '| WINNER! You received a Vote reward!')
        
        
        trigger = True
        vmem = str(psutil.virtual_memory().percent)
        c.system_stats = {'ram': str(round(psutil.virtual_memory().used / (1024.0 ** 3))) + 'gb ' + vmem + '%', 'cpu': str(psutil.cpu_percent()), 'load': str(round(psutil.getloadavg()[1], 2))}
        
    if 'nitial plotting complete' in line_plain:
        parsed_datetime = line_timestamp # datetime.fromisoformat(line_plain.split('Z')[0].replace('Z', '+00:00')).replace(tzinfo=timezone.utc).timestamp()
        line_timestamp = parsed_datetime
        if line_timestamp and line_timestamp > monitorstartTime:
            send(config['FARMER_NAME'] + '| Plot complete: ' +
                 line_plain[line_plain.find(
                     indexconst) + len(indexconst):line_plain.find("}:")] + ' 100%!')
        
    
    #farmer_metrics(farm_id_mapping)

    if trigger:
        # websocket_client.main()
        trigger = False
 
    parsed_data['line_plain'] = local_time(line_plain)
    return parsed_data


def read_log_file():
    log_file_path = Path(config['FARMER_LOG'])
    farm_id_mapping = {}  # Initialize the farm_id_mapping dictionary
    if config.get('TOGGLE_ENCODING', True):
        enc = 'utf-8'
    else:
        enc = 'utf-16'
    with log_file_path.open('r', encoding=enc) as log_file:
        while True:
            try:
                line = log_file.readline()
                if not line:
                    time.sleep(0.1)  # Wait for new lines
                    continue
                line_plain = line.encode('ascii', 'ignore').decode().strip()
                ansi_escape = re.compile(
                    r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                line_plain = ansi_escape.sub('', line_plain)
                # Now line_plain is a Unicode string that can be directly processed
                if line_plain == '\n' or line_plain == '':
                    continue
                # Continue with your parsing and processing logic
                parsed_data = parse_log_line(line_plain, curr_farm, reward_count, farm_rewards, farm_recent_rewards,
                                            drive_directory, farm_skips, farm_recent_skips,
                                             system_stats, farm_id_mapping)  # Pass the farm_id_mapping
                vmem = str(psutil.virtual_memory().percent)
                c.system_stats = {'ram': str(round(psutil.virtual_memory().used / (1024.0 ** 3))) + 'gb ' + vmem + '%', 'cpu': str(psutil.cpu_percent()), 'load': str(round(psutil.getloadavg()[1], 2))}
                
                print(parsed_data['line_plain'].replace('\n', ' '))
            except UnicodeDecodeError as e:
                print(f"Decode error encountered (Toggle TOGGLE_ENCODING in the config.yaml file!): {e}")
                time.sleep(10)
            except KeyboardInterrupt:
                print('Fine, be that way, quitter!')
                quit()
            except Exception as e:
                print(f"An error occurred: {e}")
                
                console = Console()
                console.print_exception(show_locals=True)
                time.sleep(10)



def send(msg=None):
    # Discord

    if config['SEND_DISCORD'] and config['DISCORD_WEBHOOK'] and msg:

        data = {"content": msg}
        response = requests.post(config['DISCORD_WEBHOOK'], json=data)
        success_list = [204]
        if response.status_code not in success_list:
            print('Error sending Discord: ' + str(response.status_code))

    # Pushover

    if config['SEND_PUSHOVER'] and config['PUSHOVER_APP_TOKEN'] and config['PUSHOVER_USER_KEY'] and msg:

        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
                     urllib.parse.urlencode({
                         "token": config['PUSHOVER_APP_TOKEN'],
                         "user": config['PUSHOVER_USER_KEY'],
                         "message": msg,
                     }), {"Content-type": "application/x-www-form-urlencoded"})
        conn.getresponse()



read_log_file()

threading.Thread(target=read_log_file, daemon=True, name='Read_log').start()
