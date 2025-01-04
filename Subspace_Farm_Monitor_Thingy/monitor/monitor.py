from pathlib import Path
from datetime import timedelta, timezone, datetime
import dateutil.parser
from dateutil.parser import parse  # Importing parse function
import yaml
import time
import threading
import utilities.conf as c
import utilities.websocket_client as websocket_client
from rich import print
import re
import requests
from rich.console import Console
import http.client
import urllib
import os

# Initialize state
ErrorLogging = False
last_notification_time = {}
notification_count = {}
c.system_stats = {}
system_stats = {}


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

c.hddtemps = config.get('HDDTEMPS', False)
c.hour_24 = config.get('HOUR_24', False)
c.farmer_name = config.get('FARMER_NAME', 'WolfrageRocks')
c.front_end_ip = config.get('FRONT_END_IP', "127.0.0.1")
c.front_end_port = config.get('FRONT_END_PORT', "8016")
farmer_ip = config.get('FARMER_IP', "127.0.0.1")
farmer_port = config.get('FARMER_PORT', "8181")
cluster_enabled = config.get('CLUSTER_ENABLED' ,False)
c.gpuStats = config.get('GPUSTATS', True)

reward_phrase = 'reward_signing: Successfully signed reward hash'
recommendTxt = '\n\t\t[blink][b yellow]Recommendation: [white]'

dt = datetime.now(timezone.utc)
utc_time = dt.replace(tzinfo=timezone.utc)
utc_timestamp = utc_time.timestamp()
c.startTime = utc_timestamp
monitorstartTime = utc_timestamp


def process_farmer_metrics(metrics, farm_id_mapping):
    """
    Process farmer metrics and return a dictionary of metrics per disk index.
    """
    metrics_dict = {}
    wanted = [
        'subspace_farmer_farm_sectors_total_Sectors',
        'subspace_farmer_plotter_sector_plotting_time_seconds',
        'subspace_farmer_plotter_sector_plotted_counter_Sectors',
        'process_start_time_seconds',
        'subspace_farmer_sectors_total_sectors',
        'subspace_farmer_sector_plot_count',
        'subspace_farmer_sector_notplotted_count',
        'subspace_farmer_sector_index',
        'subspace_farmer_farm_sector_plotting_time_seconds_count',
        'subspace_farmer_farm_sector_plotting_time_seconds_sum',
        'subspace_farmer_farm_auditing_time_seconds_sum',
        'subspace_farmer_farm_auditing_time_seconds_count',
        'subspace_farmer_farm_proving_time_seconds_count',
        'subspace_farmer_farm_proving_time_seconds_sum',
        'subspace_farmer_sectors_total_sectors_Plotting',
        'subspace_farmer_sector_expired_count',
        'subspace_farmer_farm_sectors_total_Sectors_Expired',
        'subspace_farmer_farm_sectors_total_Sectors_AboutToExpire',
        'subspace_farmer_farm_sectors_total_Sectors_Plotted',
        'subspace_farmer_farm_sectors_total_Sectors_NotPlotted'
    ]
    
    total_plotting_time_sum = 0
    total_plotting_time_count = 0
    test1 = []
    test2 = []
    
    for metric in metrics:
        if 'subspace_farmer_farm_sector_plotting_time_seconds_sum' in metric:
            test1.append(float(metric.split()[-1]))
            total_plotting_time_sum += float(metric.split()[-1])
            
        elif 'subspace_farmer_farm_sector_plotting_time_seconds_count' in metric:
            test2.append(float(metric.split()[-1]))
            total_plotting_time_count += float(metric.split()[-1])
            
        elif metric.startswith('subspace_farmer_') and 'farm_id="' in metric:
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
    # Calculate global average sector plotting time
    if total_plotting_time_count > 0:
        c.global_time = total_plotting_time_sum / total_plotting_time_count
    else:
        c.global_time = 0  # If no plotting has occurred
    if ErrorLogging:
        print("metrics_dict")
    return metrics_dict
    
def get_farmer_metrics(farmer_ip, farmer_port, wait=60):

    """
    Retrieve farmer metrics from the farmer service.
    """
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
        if ErrorLogging:
            print('Metrics\n\n')
        return metrics
    except requests.exceptions.RequestException as e:
        c.startTime = 0
        c.connected_farmer = False
        time.sleep(wait)
        return [] 
    
    

    
def update_farm_metrics(farm_id_mapping):
    
    """
    Update farm metrics and store them in the global configuration.
    """
    metrics = get_farmer_metrics(farmer_ip, farmer_port)
    processed_metrics = process_farmer_metrics(metrics, farm_id_mapping)
    all_metrics = c.farm_metrics
    for disk_index, metrics in processed_metrics.items():
        if disk_index in c.disk_farms:
            audit_sum = float(metrics.get('subspace_farmer_farm_auditing_time_seconds_sum', {}).get('value', 0))
            audit_count = float(metrics.get('subspace_farmer_farm_auditing_time_seconds_count', {}).get('value', 0))
            prove_sum = float(metrics.get('subspace_farmer_farm_proving_time_seconds_sum', {}).get('value', 0))
            prove_count = float(metrics.get('subspace_farmer_farm_proving_time_seconds_count', {}).get('value', 0))
            
            c.proves[disk_index] = prove_sum / prove_count if prove_count > 0 else 0
            c.audits[disk_index] = 1000 * (audit_sum / audit_count) if audit_count > 0 else 0
            
            all_metrics[disk_index] = metrics

    c.farm_metrics = all_metrics
    if ErrorLogging:
        print('All Metrics')

def socket_client_thread():
    """
    Periodically attempt to reconnect the WebSocket client.
    """
    
    
    while True:
        websocket_client.main()
        
        if ErrorLogging:
            print('Websocket thread\n\n')
            
        time.sleep(15)

def update_metrics_periodically(interval=10):
    """
    Periodically update farm metrics and reward information.
    
    """
    
    
    
    if ErrorLogging:
            print('Update metrics periodically\n\n')
    while True:
        c.rewards_per_hr = 0
        for disk_index in disk_farms:
            one_day_ago = datetime.now().timestamp() - 86400
            c.farm_recent_rewards[disk_index] = len([r for r in c.farm_reward_times[disk_index] if r > one_day_ago])
            c.farm_recent_skips[disk_index] = len([r for r in c.farm_skip_times[disk_index] if r > one_day_ago]) 
            c.rewards_per_hr += calculate_rewards_per_hour(c.farm_reward_times[disk_index])
            
        update_farm_metrics(c.farm_id_mapping)
        # save_data_to_file()
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
    """
    Validate the datetime string format.
    """
    dt_str = dt_str.replace('INFO', '').strip()
    try:
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1] + '+00:00'
        parse(dt_str)
        return True
    except ValueError:
        return False

def convert_to_utc_with_offset_zulu(datetime_string, utc_offset=0):
    """
    Convert a local datetime string to UTC with a Zulu suffix.
    """
    if not isinstance(datetime_string, str):
        return datetime_string
    if not isinstance(utc_offset, int):
        utc_offset = 0

    try:
        local_datetime = datetime.strptime(datetime_string, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return datetime_string
    
    offset_delta = timedelta(hours=utc_offset - 12)
    utc_datetime = local_datetime - offset_delta
    
    return utc_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + 'Z'

def local_time(string):
    """
    Convert a log line's timestamp to local time and apply formatting.
    """
    string2 = string.split(' ', 1)
    convert = string2[0]
    if not datetime_valid(convert):
        return string

    setColor = '[red]' if 'ERROR' in string else '[dark_orange]' if 'WARN' in string else ''

    datestamp = parse(convert)
    local_tz = dateutil.tz.tzlocal()
    datestamp = datestamp.astimezone(tz=local_tz)

    formatted_timestamp = datestamp.strftime("%m-%d %H:%M:%S|" + setColor)
    if not c.hour_24:
        formatted_timestamp = formatted_timestamp.replace(' PM', 'pm').replace(' AM', 'am')

    return formatted_timestamp + ' ' + string2[1]

def calculate_rewards_per_hour(farm_rewards):
    """
    Calculate the average rewards per hour over the past 24 hours.
    """
    one_day_ago = datetime.now(timezone.utc).timestamp() - 86400
    recent_rewards = [r for r in farm_rewards if r > one_day_ago]
    return len(recent_rewards) / 24  

def rewards_per_day_per_tib(farm_rewards, farm, total_plotted_tib):
    """
    Calculate rewards per day per TiB of plotted space.
    """
    one_day_ago = datetime.now().timestamp() - 86400
    recent_rewards = [r for r in farm_rewards.get(farm, []) if r > one_day_ago]
    total_rewards_last_24_hours = len(recent_rewards)
    return total_rewards_last_24_hours / total_plotted_tib

def parse_log_line(line_plain, current_farm, reward_count, farm_rewards, farm_recent_rewards, drive_directory, farm_skips, farm_recent_skips, system_stats, farm_id_mapping):
    """
    Parse a single log line and update various metrics and states.
    """
    triggered = False
    parsed_data = {
        'line_plain': '', 
        'current_farm': current_farm,
        'reward_count': reward_count,
        'farm_rewards': farm_rewards,
        'farm_recent_rewards': farm_recent_rewards,
        'drive_directory': drive_directory,
        'farm_skips': farm_skips,
        'farm_recent_skips': farm_recent_skips,
        'system_stats': system_stats,
    }

    
    line_timestamp_str = line_plain.split()[0]
    
    farm_index = line_plain[line_plain.find(indexconst) + len(indexconst):line_plain.find("}")]

    if 'groups detected l3_cache_groups=' in line_plain:
        c.l3_concurrency = int(line_plain.split('groups detected l3_cache_groups=')[1])
    
    if datetime_valid(line_timestamp_str):
        line_timestamp_str = line_timestamp_str.replace('INFO', '').strip()
        line_timestamp = dateutil.parser.parse(line_timestamp_str).astimezone(timezone.utc).timestamp()
        parsed_datetime = line_timestamp 
    else:
        line_timestamp = None
        
    if 'Finished collecting already plotted pieces' in line_plain:
        c.startTime = line_timestamp
        farm_id_mapping.clear()
        drive_directory.clear()
        current_farm = None
        c.l3_timestamps.clear()
        c.l3_timestamps.extend([line_timestamp] * (c.l3_concurrency * 2))
        c.dropped_drives = []
    
    if "ERROR" in line_plain:
        c.errors.pop(0)
        c.errors.append(local_time(line_plain.replace('\n', '')))

    elif "WARN" in line_plain:
        c.warnings.pop(0)
        c.warnings.append(local_time(line_plain.replace('\n', '')))
    
    if 'arm errored and stopped' in line_plain and parsed_datetime > monitorstartTime:
        farm_index = extract_farm_index(line_plain)
        c.dropped_drives.append(farm_index)
        stop_error_notification(farm_index)   
        
    elif 'buffer of stream grows beyond limit' in line_plain or 'Failed to subscribe' in line_plain or 'DSN instance configured.' in line_plain or "enchmarking faster proving method" in line_plain:
        pass

    elif 'is likely already in use' in line_plain:
        line_plain += f" {recommendTxt}Check that your Farmer is not running, and that you aren't currently scrubbing that drive\n"
    
    elif 'Invalid scalar' in line_plain:
        line_plain += f" {recommendTxt}Run 'subspace-farmer scrub /path/to/farm' \n"
    
    elif "ID: " in line_plain:
        farm_id = line_plain.split(' ID: ')[1]
        if farm_index and farm_id:
            farm_id_mapping[farm_index] = farm_id
            c.farm_id_mapping[farm_index] = farm_id
    
    elif 'Farm exited with error farm_index=' in line_plain and parsed_datetime > monitorstartTime:
        farm_index = line_plain.split('Farm exited with error farm_index=')[0]
        c.dropped_drives.append(farm_index)
        stop_error_notification(farm_index)  
        
    elif ('subspace_farmer::commands::farm: Farm' in line_plain or 'subspace_farmer::commands::cluster::farmer: Farm' in line_plain) and ('cache worker exited' not in line_plain and 'error' not in line_plain):
        if farm_index not in disk_farms:
            disk_farms.add(farm_index)
        current_farm = farm_index
        c.current_farm = current_farm
        
    elif 'using whole sector elapsed' in line_plain:
        c.prove_method[farm_index] = 'WC'
        line_plain += f"{recommendTxt}Benchmark your drives, use decent quality SSDs"
    
    elif 'ConcurrentChunks' in line_plain:
        c.prove_method[farm_index] = 'CC'
        
    elif "found fastest_mode=" in line_plain:
        prove_type = line_plain.split('fastest_mode=')[1]
        c.prove_method[farm_index] = prove_type
    
    elif "lotting sector" in line_plain:
        update_sector_time(line_timestamp)
        triggered = True

    elif 'Directory:' in line_plain and c.current_farm:
        drive_directory[c.current_farm] = line_plain.split('Directory: ')[1]
        c.current_farm = None

    elif ("solution skipped due to farming time limit" in line_plain) or ("Solution was ignored" in line_plain):
        farm_skips = update_farm_skips(line_plain, line_timestamp, farm_skips)
        line_plain += f"{recommendTxt}Run 'subspace-farmer benchmark {{audit|prove}} /path/to/farm/'"
    
    elif reward_phrase in line_plain:
        reward_count += 1
        c.reward_count = reward_count
        update_farm_rewards(line_plain, line_timestamp, farm_rewards)
        if parsed_datetime > monitorstartTime:
            send(f"{config['FARMER_NAME']}| WINNER! You received a Vote reward!")
        triggered = True
        
        
    if 'nitial plotting complete' in line_plain:
        if line_timestamp and line_timestamp > monitorstartTime:
            send(f"{config['FARMER_NAME']}| Plot complete: {farm_index} 100%!")

    if triggered:
        triggered = False

    parsed_data['line_plain'] = local_time(line_plain).replace('  ', ' ')
        
    return parsed_data

def extract_farm_index(line_plain):
    if '}' in line_plain:    
        return line_plain[line_plain.find(indexconst) + len(indexconst):line_plain.find("}")]
    elif 'farm_index=' in line_plain: 
        return line_plain.split('farm_index=')[1].split('error=')[0]
    else:
        return line_plain.split('farm=')[1].split('error=')[0]

def update_sector_time(line_timestamp):
    c.l3_timestamps.append(line_timestamp)
    if len(c.l3_timestamps) > 50:
        c.l3_timestamps.pop(0)

    if c.l3_concurrency <= 1:
        if len(c.l3_timestamps) > 1:
            time_diffs = [t - s for s, t in zip(c.l3_timestamps, c.l3_timestamps[1:])]
            c.l3_farm_sector_time = sum(time_diffs) / len(time_diffs)
        else:
            c.l3_farm_sector_time = 0
    else:
        if len(c.l3_timestamps) >= c.l3_concurrency:
            l3_sum = sum(c.l3_timestamps[i + c.l3_concurrency] - c.l3_timestamps[i] for i in range(len(c.l3_timestamps) - c.l3_concurrency))
            c.l3_farm_sector_time = l3_sum / (c.l3_concurrency * c.l3_concurrency)

def update_farm_skips(line_plain, line_timestamp, farm_skips):
    farm_index = line_plain.rsplit(indexconst, 1)[-1].rsplit('}', 1)[0]
    c.farm_skip_times.setdefault(farm_index, []).append(line_timestamp)
    farm_skips.setdefault(farm_index, 0)
    farm_skips[farm_index] += 1
    c.farm_skips[farm_index] = farm_skips[farm_index]
    return farm_skips

def update_farm_rewards(line_plain, line_timestamp, farm_rewards):
    farm_index_start = line_plain.find(indexconst) + len(indexconst)
    farm_index_end = line_plain.find("}:")
    if farm_index_start == -1 or farm_index_end == -1:
        return

    farm_index = line_plain[farm_index_start:farm_index_end]
    c.farm_reward_times.setdefault(farm_index, []).append(line_timestamp)

    current_rewards = farm_rewards.get(farm_index, 0)
    farm_rewards[farm_index] = current_rewards + 1
    c.farm_rewards[farm_index] = farm_rewards[farm_index]



def reopen_log_file(log_file_path, enc):
    """
    Reopen the log file if it has been rotated out.
    """
    while True:
        try:
            with log_file_path.open('r', encoding=enc) as log_file:
                while True:
                    line = log_file.readline()
                    if not line:
                        time.sleep(0.2)
                        continue
                    yield line
            if ErrorLogging:
                print('Reopen Log\n\n')
        except FileNotFoundError:
            print("Log file not found. Waiting for it to be recreated...")
            time.sleep(10)

def read_log_file():
    """
    Continuously read and process the log file, handling rotation.
    """
    log_file_path = Path(config['FARMER_LOG'])
    farm_id_mapping = {}
    enc = 'utf-8' if config.get('TOGGLE_ENCODING', True) else 'utf-16'

    for line in reopen_log_file(log_file_path, enc):
        try:
            line_plain = line.encode('ascii', 'ignore').decode().strip()
            ansi_escape = re.compile(
                r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            line_plain = ansi_escape.sub('', line_plain)
            if line_plain == '\n' or line_plain == '':
                continue
            parsed_data = parse_log_line(line_plain, curr_farm, reward_count, farm_rewards, farm_recent_rewards,
                                        drive_directory, farm_skips, farm_recent_skips,
                                        system_stats, farm_id_mapping)
            
            
            
                
            print(parsed_data['line_plain'] + '\r')
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
            time.sleep(5)

def send(msg=None):
    """
    Send a notification message via configured methods (Discord, Pushover).
    """
    if not msg:
        return

    if config.get('SEND_DISCORD') and config.get('DISCORD_WEBHOOK'):
        try:
            response = requests.post(
                config['DISCORD_WEBHOOK'], json={"content": msg}, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f'Error sending Discord: {e}')

    if config.get('SEND_PUSHOVER') and config.get('PUSHOVER_APP_TOKEN') and config.get('PUSHOVER_USER_KEY'):
        try:
            conn = http.client.HTTPSConnection("api.pushover.net", timeout=10)
            conn.request("POST", "/1/messages.json",
                        urllib.parse.urlencode({
                            "token": config['PUSHOVER_APP_TOKEN'],
                            "user": config['PUSHOVER_USER_KEY'],
                            "message": msg,
                        }), {"Content-type": "application/x-www-form-urlencoded"})
            conn.getresponse().read()
        except Exception as e:
            print(f'Error sending Pushover: {e}')

def save_data_to_file():
    """
    Save current state data to a file.
    """
    data = {
        'system_stats': c.system_stats,
        'disk_farms': c.disk_farms,
        'reward_count': c.reward_count,
        'farm_rewards': c.farm_rewards,
        'farm_recent_rewards': c.farm_recent_rewards,
        'farm_skips': c.farm_skips,
        'farm_recent_skips': c.farm_recent_skips,
        'drive_directory': c.drive_directory,
        'errors': c.errors,
        'total_error_count': c.total_error_count,
        'curr_farm': c.curr_farm,
        'farm_metrics': c.farm_metrics,
        'audits': c.audits,
        'proves': c.proves
    }


read_log_file()
threading.Thread(target=read_log_file, daemon=True, name='Read_log').start()