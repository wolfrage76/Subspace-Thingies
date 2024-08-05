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
utc_timestamp = utc_time.timestamp()
c.startTime = utc_timestamp
monitorstartTime = utc_timestamp

def process_farmer_metrics(metrics, farm_id_mapping):
    metrics_dict = {}
    wanted = [
        'subspace_farmer_farm_sectors_total_Sectors',
        'process_start_time_seconds',
        'subspace_farmer_sectors_total_sectors',
        'subspace_farmer_sector_plot_count',
        'subspace_farmer_sector_notplotted_count',
        'subspace_farmer_sector_index',
        'subspace_farmer_farm_sector_plotting_time_seconds_count',
        'subspace_farmer_farm_sector_plotting_time_seconds_sum',
        'subspace_farmer_sectors_total_sectors_Plotted',
        'subspace_farmer_sectors_total_sectors_Expired',
        'subspace_farmer_sectors_total_sectors_AboutToExpire',
        'subspace_farmer_farm_auditing_time_seconds_sum',
        'subspace_farmer_farm_auditing_time_seconds_count',
        'subspace_farmer_farm_sector_plotting_time_seconds_count',
        'subspace_farmer_farm_proving_time_seconds_count',
        'subspace_farmer_farm_proving_time_seconds_sum',
        'subspace_farmer_sectors_total_sectors_Plotting',
        'subspace_farmer_sector_expired_count'
    ]
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

def get_farmer_metrics(farmer_ip, farmer_port, wait=60):
    url = f"http://{farmer_ip}:{farmer_port}/metrics"
    max_logs = 3
    metricslog = []
    try:
        response = requests.get(url)
        response.raise_for_status()
        c.connected_farmer = True
        metrics = response.text.split('\n')
        metricslog = [line for line in response.text.split('\n')]

        if config.get('METRIC_LOGGING', False):
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log_filename = f"metrics_log_{timestamp}.txt"
            with open(log_filename, 'w') as log_file:
                log_file.write("\n".join(metricslog))

            log_files = [f for f in os.listdir(".") if re.match(r'^metrics_log_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.txt$', f)]
            log_files.sort(key=os.path.getmtime, reverse=True)

            for log_file in log_files[max_logs:]:
                os.remove(log_file)

        return metrics
    except requests.exceptions.RequestException as e:
        c.startTime = 0
        c.connected_farmer = False
        time.sleep(wait)
        return [] 
    
def update_farm_metrics(farm_id_mapping):
    metrics = get_farmer_metrics(farmer_ip, farmer_port)
    processed_metrics = process_farmer_metrics(metrics, farm_id_mapping)
    all_metrics = c.farm_metrics
    for disk_index, metrics in processed_metrics.items():
        if disk_index in c.disk_farms:
            
            audit_sum = float(metrics.get('subspace_farmer_farm_auditing_time_seconds_sum', {}).get('value', 0))
            audit_count = float(metrics.get('subspace_farmer_farm_auditing_time_seconds_count', {}).get('value', 0))
            prove_sum = float(metrics.get('subspace_farmer_farm_proving_time_seconds_sum', {}).get('value', 0))
            prove_count = float(metrics.get('subspace_farmer_farm_proving_time_seconds_count', {}).get('value', 0))
            
            
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
    min_cooldown = 300

    if farm in last_notification_time:
        elapsed_time = current_time - last_notification_time[farm]
        current_cooldown = min_cooldown * (2 ** notification_count[farm])

        if elapsed_time < current_cooldown:
            return

        notification_count[farm] += 1
    else:
        notification_count[farm] = 0

    last_notification_time[farm] = current_time
    send(config['FARMER_NAME'] + '| ERROR - Drive Dropped Off: ' + farm)
    reset_cooldown = min_cooldown * (2 ** (notification_count[farm] + 1))
    threading.Timer(reset_cooldown, reset_notification_count, [farm]).start()
    
def datetime_valid(dt_str):
    dt_str = dt_str.replace('INFO','').strip()
    try:
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1] + '+00:00'
        parse(dt_str)
        return True
    except ValueError:
        return False

def convert_to_utc_with_offset_zulu(date_time_str, utc_offset=0):
    if not isinstance(date_time_str, str):
       return date_time_str
    if not isinstance(utc_offset, int):
        utc_offset = 0
    try:
        local_dt = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError as e:
        return date_time_str
    
    offset = timedelta(hours=utc_offset - 12)
    utc_dt = local_dt - offset
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + 'Z'

def local_time(string):
    string2 = string.split(' ')
    convert = string2[0]
    
    if config.get('U_GPU_PLOTTER', False):
        string2 = string.split('  ')[1].strip()
        convert = string.split('  ')[0].strip()
        convert = convert_to_utc_with_offset_zulu(convert, config.get('TIMEZONE_OFFSET', 0)) + '+00:00'
        convert = convert.replace('INFO','').strip()
        
    if datetime_valid(convert):
        if convert.endswith('Z'):
            convert = convert[:-1] + '+00:00'
        datestamp = parse(convert)

        local_tz = dateutil.tz.tzlocal()
        datestamp = datestamp.astimezone(tz=local_tz)
  
        if c.hour_24:
            formatted_timestamp = datestamp.strftime("%m-%d %H:%M:%S|")
        else:
            formatted_timestamp = datestamp.strftime(
                "%m-%d %I:%M:%S %p|").replace(' PM', 'pm').replace(' AM', 'am')

        if config.get('U_GPU_PLOTTER', False):
            return formatted_timestamp + ' ' + string.replace(string.split('  ')[0],'')
        else:
            return formatted_timestamp + ' ' + ' '.join(string2).replace(string.split('  ')[0],'')
    else:
        return string

def calculate_rewards_per_hour(farm_rewards):
    dt = datetime.now(timezone.utc)
    utc_time = dt.replace(tzinfo=timezone.utc)
    utc_timestamp = utc_time.timestamp()
    one_day_ago = utc_timestamp - 86400
    recent_rewards = [r for r in farm_rewards if r > one_day_ago]
    return len(recent_rewards) / 24  

def rewards_per_day_per_tib(farm_rewards, farm, total_plotted_tib):
    one_day_ago = datetime.now().timestamp() - 86400
    recent_rewards = [r for r in farm_rewards.get(farm, []) if r > one_day_ago]
    total_rewards_last_24_hours = len(recent_rewards)
    return total_rewards_last_24_hours / total_plotted_tib

def parse_log_line(line_plain, curr_farm, reward_count, farm_rewards, farm_recent_rewards, drive_directory, farm_skips, farm_recent_skips, system_stats, farm_id_mapping):
    trigger = False
    parsed_data = {
        'line_plain': '', 
        'curr_farm': curr_farm,
        'reward_count': reward_count,
        'farm_rewards': farm_rewards,
        'farm_recent_rewards': farm_recent_rewards,
        'drive_directory': drive_directory,
        'farm_skips': farm_skips,
        'farm_recent_skips': farm_recent_skips,
        'system_stats': system_stats,
    }

    if config.get("U_GPU_PLOTTER", False):
        line_timestamp_str = line_plain.split()[0] + ' ' + line_plain.split()[1]
    else:
        line_timestamp_str = line_plain.split()[0]
    
    farm = line_plain[line_plain.find(
            indexconst) + len(indexconst):line_plain.find("}")]
     
    if 'groups detected l3_cache_groups=' in line_plain:
        c.l3_concurrency = int(line_plain.split('groups detected l3_cache_groups=')[1])
    
    if datetime_valid(line_timestamp_str):
        line_timestamp_str = line_timestamp_str.replace('INFO','').strip()
        line_timestamp = dateutil.parser.parse(
            line_timestamp_str).astimezone(timezone.utc).timestamp()
        parsed_datetime = line_timestamp 
    else:
        line_timestamp = None
        
    if 'Finished collecting already plotted pieces' in line_plain:
        c.startTime = line_timestamp
        farm_id_mapping = {}
        drive_directory = {}
        curr_farm = None
       
        c.l3_timestamps.clear()
        for x in range(c.l3_concurrency * 2):
            c.l3_timestamps.append(line_timestamp)
        c.dropped_drives = []
    
    if "ERROR" in line_plain:
        c.errors.pop(0)
        c.errors.append(local_time(line_plain.replace(
            '\n', '').replace(' ERROR', '[b red]')))

    if "WARN" in line_plain:
        c.warnings.pop(0)
        c.warnings.append(local_time(line_plain.replace(
            '\n', '').replace(' WARN', '[b yellow]')))
    
    elif 'arm errored and stopped' in line_plain and parsed_datetime > monitorstartTime:
        if '}' in line_plain:    
            farm = line_plain[line_plain.find(indexconst) + len(indexconst):line_plain.find("}")]
        elif 'farm_index=' in line_plain: 
            farm = line_plain.split('farm_index=')[1].split('error=')[0]
        else:
            farm = line_plain.split('farm=')[1].split('error=')[0]
    
        c.dropped_drives.append(farm)
        stop_error_notification(farm)   
   
    elif 'buffer of stream grows beyond limit' in line_plain:
        pass
    elif 'is likely already in use' in line_plain:
        pass
    elif 'Failed to subscribe' in line_plain:
        pass
    elif "ID: " in line_plain:
        farm_id = line_plain.split(' ID: ')[1]
        farm_index = line_plain[line_plain.find(indexconst) + len(indexconst):line_plain.find('}')]
        if farm_index and farm_id:
            farm_id_mapping[farm_index] = farm_id
            c.farm_id_mapping[farm_index] = farm_id
    elif 'DSN instance configured.' in line_plain:
        pass
    
    elif "enchmarking faster proving method" in line_plain:
        pass
    elif 'Farm exited with error farm_index=' in line_plain and parsed_datetime > monitorstartTime:
        farm = line_plain.split('Farm exited with error farm_index=')[0]
        c.dropped_drives.append(farm)
        stop_error_notification(farm)  
        
    elif 'subspace_farmer::commands::farm: Farm' in line_plain and 'cache worker exited' not in line_plain and 'error' not in line_plain:
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
        farm = line_plain[line_plain.find(
            indexconst) + len(indexconst):line_plain.find("}")]
        prove_type = line_plain.split('fastest_mode=')[1]
        c.prove_method[farm] = prove_type
    
    elif "lotting sector" in line_plain:
        if len(c.l3_timestamps) >= c.l3_concurrency:
            del(c.l3_timestamps[0])
        c.l3_timestamps.append(line_timestamp)
        l3_sum = 0

        for x in range(c.l3_concurrency):
            l3_sum += c.l3_timestamps[x + c.l3_concurrency] - c.l3_timestamps[x]

        if c.l3_concurrency != 0:
            c.l3_farm_sector_time = l3_sum / (c.l3_concurrency * c.l3_concurrency)
        else:
            c.l3_farm_sector_time = 0
        
        trigger = True

    elif 'Directory:' in line_plain and c.curr_farm:
        drive_directory[c.curr_farm] = line_plain.split('Directory: ')[1]
        c.curr_farm = None

    elif ("solution skipped due to farming time limit" in line_plain) or ("Solution was ignored" in line_plain):
        farm = line_plain[line_plain.find(
            indexconst) + len(indexconst):line_plain.find("}")]
        farm_skips = c.farm_skips
        parsed_datetime = line_timestamp
        c.farm_skip_times[farm].append(parsed_datetime)
        
        if farm:
            if farm not in farm_skips:
                farm_skips[farm] = 0
            farm_skips[farm] += 1
            c.farm_skips[farm] = farm_skips[farm]
    
    elif reward_phrase in line_plain:
        farm = line_plain[line_plain.find(indexconst) + len(indexconst):line_plain.find("}:")]
        one_day_ago = datetime.now().timestamp() - 86400
        reward_count += 1
        c.reward_count = reward_count
        parsed_datetime = line_timestamp
        c.farm_reward_times[farm].append(parsed_datetime)
        
        if farm:
            if farm not in farm_rewards:
                farm_rewards[farm] = 0
            farm_rewards[farm] += 1
            c.farm_rewards[farm] = farm_rewards[farm]
        
        if parsed_datetime > monitorstartTime:
            send(config['FARMER_NAME'] +
                 '| WINNER! You received a Vote reward!')
        
        trigger = True
        vmem = str(psutil.virtual_memory().percent)
        c.system_stats = {'ram': str(round(psutil.virtual_memory().used / (1024.0 ** 3))) + 'gb ' + vmem + '%', 'cpu': str(psutil.cpu_percent()), 'load': str(round(psutil.getloadavg()[1], 2))}
        
    if 'nitial plotting complete' in line_plain:
        parsed_datetime = line_timestamp
        line_timestamp = parsed_datetime
        if line_timestamp and line_timestamp > monitorstartTime:
            send(config['FARMER_NAME'] + '| Plot complete: ' +
                 line_plain[line_plain.find(
                     indexconst) + len(indexconst):line_plain.find("}:")] + ' 100%!')
        
    if trigger:
        trigger = False
 
    parsed_data['line_plain'] = local_time(line_plain)
    return parsed_data

def read_log_file():
    log_file_path = Path(config['FARMER_LOG'])
    farm_id_mapping = {}
    if config.get('TOGGLE_ENCODING', True):
        enc = 'utf-8'
    else:
        enc = 'utf-16'
    with log_file_path.open('r', encoding=enc) as log_file:
        while True:
            try:
                line = log_file.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                line_plain = line.encode('ascii', 'ignore').decode().strip()
                ansi_escape = re.compile(
                    r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                line_plain = ansi_escape.sub('', line_plain)
                if line_plain == '\n' or line_plain == '':
                    continue
                parsed_data = parse_log_line(line_plain, curr_farm, reward_count, farm_rewards, farm_recent_rewards,
                                            drive_directory, farm_skips, farm_recent_skips,
                                             system_stats, farm_id_mapping)
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
    if config['SEND_DISCORD'] and config['DISCORD_WEBHOOK'] and msg:
        data = {"content": msg}
        response = requests.post(config['DISCORD_WEBHOOK'], json=data)
        success_list = [204]
        if response.status_code not in success_list:
            print('Error sending Discord: ' + str(response.status_code))

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
