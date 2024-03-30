import subprocess
import psutil
from pathlib import Path
from datetime import timezone
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

# Initialize state
c.system_stats = {}#{'ram': str(round(psutil.virtual_memory().used / (1024.0 ** 3))) + 'gb ' + str(psutil.virtual_memory(
#).percent) + '%', 'cpu': str(psutil.cpu_percent()), 'load': str(round(psutil.getloadavg()[1], 2))}
system_stats = c.system_stats

disk_farms = c.disk_farms
reward_count = c.reward_count
farm_rewards = c.farm_rewards
farm_skips = c.farm_skips
event_times = c.event_times
drive_directory = c.drive_directory
errors = c.errors
total_error_count = c.total_error_count
curr_farm = c.curr_farm

indexconst = "{farm_index="


with open("config.yaml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)


c.show_logging = config.get('SHOW_LOGGING', False)
c.hour_24 = config.get('HOUR_24', False)
c.farmer_name = config.get('FARMER_NAME', 'WolfrageRocks')
c.front_end_ip = config.get('FRONT_END_IP', "127.0.0.1")
c.front_end_port = config.get('FRONT_END_PORT', "8016")
farmer_ip = config.get('FARMER_IP', "127.0.0.1")
farmer_port = config.get('FARMER_PORT', "8016")

reward_phrase = 'reward_signing: Successfully signed reward hash'

c.startTime = time.time()

def process_farmer_metrics(metrics, farm_id_mapping):
    metrics_dict = {}
    wanted = ['subspace_farmer_sectors_total_sectors', 'subspace_farmer_sector_plot_count', 'subspace_farmer_sector_notplotted_count', 'subspace_farmer_sector_index','subspace_farmer_sector_plotting_time_seconds_count', 'subspace_farmer_sector_plotting_time_seconds_sum', 'subspace_farmer_sectors_total_sectors_Plotted', 'subspace_farmer_sectors_total_sectors_Expired', 'subspace_farmer_sectors_total_sectors_AboutToExpire']

    for metric in metrics:
        if metric.startswith('subspace_farmer_') and 'farm_id="' in metric:
            parts = metric.split()
            metric_name = parts[0].split('{')[0]
            if '_bucket' in metric_name or  'proving' in metric_name or  'audit' in metric_name:
            #if metric_name.find('_bucket') == -1:
                continue
            
            if metric_name not in wanted:
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

def get_farmer_metrics(farmer_ip, farmer_port):
    url = f"http://{farmer_ip}:{farmer_port}/metrics"
    try:
        response = requests.get(url)
        response.raise_for_status()
        metrics = response.text.split('\n')
        return metrics
    except requests.exceptions.RequestException as e:
        print(f"Error fetching farmer metrics: {e}")
        return []
    
    
def update_farm_metrics(farm_id_mapping):
    
    metrics = get_farmer_metrics(farmer_ip, farmer_port)
    processed_metrics = process_farmer_metrics(metrics, farm_id_mapping)
    all_metrics = c.farm_metrics
    for disk_index, metrics in processed_metrics.items():
        if disk_index in c.disk_farms:
            
            all_metrics[disk_index] = metrics
    c.farm_metrics = all_metrics


def socket_client_thread():
    while True:
        websocket_client.main()
        time.sleep(15)
        #print("FIX THIS TIMER!")

def update_metrics_periodically(interval=10):
    while True:
        update_farm_metrics(c.farm_id_mapping)
        time.sleep(interval)

metrics_thread = threading.Thread(target=update_metrics_periodically, daemon=True)
metrics_thread.start()

socketclientthread = threading.Thread(
    target=socket_client_thread, name='SocketClient', daemon=True)

socketclientthread.start()


def datetime_valid(dt_str):
    try:
        # Explicitly handle the 'Z' UTC designation
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1] + '+00:00'
        parse(dt_str)
        return True
    except ValueError:
        return False

def local_time(string):
    string2 = string.split(' ')
    convert = string2[0]

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
                "%m-%d %I:%M %p|").replace(' PM', 'pm').replace(' AM', 'am')

        # Return the formatted timestamp followed by the rest of the original string, excluding the original timestamp
        return formatted_timestamp + ' ' + ' '.join(string2[1:])
    else:
        return string  # If the timestamp is invalid, return the original string


def parse_log_line(line_plain, curr_farm, reward_count, farm_rewards, event_times,  drive_directory, farm_skips, system_stats, farm_id_mapping, ):

  
    trigger = False
    parsed_data = {
        'line_plain': '',  # Default value
        'curr_farm': curr_farm,
        'reward_count': reward_count,
        'farm_rewards': farm_rewards,
        'event_times': event_times,
        'drive_directory': drive_directory,
        'farm_skips': farm_skips,
        'system_stats': system_stats,
    }

    # Assuming the first part of the line is the timestamp
    line_timestamp_str = line_plain.split()[0]

    if datetime_valid(line_timestamp_str):
        line_timestamp = dateutil.parser.parse(
            line_timestamp_str).astimezone(timezone.utc).timestamp()
    else:
        line_timestamp = None

    if "ERROR" in line_plain:
        c.errors.pop(0)
        c.errors.append(local_time(line_plain.replace(
            '\n', '').replace(' ERROR', '[b red]')))

    if "WARN" in line_plain:
        c.warnings.pop(0)
        c.warnings.append(local_time(line_plain.replace(
            '\n', '').replace(' WARN', '[b yellow]')))
    
    if 'hickory' in line_plain and config['MUTE_HICKORY']:
        pass
    
    elif 'subspace_farmer::commands::farm: Farmer cache worker exited.' in line_plain:
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
    elif 'WARN quinn_udp: sendmsg error:' in line_plain:
        pass
    elif "enchmarking faster proving method" in line_plain:
        pass
    if ("Single disk farm" in line_plain or 'subspace_farmer::commands::farm: Farm' in line_plain) and 'cache worker exited' not in line_plain:

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
        farm = line_plain[line_plain.find(
            indexconst) + len(indexconst):line_plain.find("}")]
        prove_type = 'CC'
        c.prove_method[farm] = prove_type
        
    elif "found fastest_mode=" in line_plain:
        farm = line_plain[line_plain.find(
            indexconst) + len(indexconst):line_plain.find("}")]
        prove_type = line_plain.split('fastest_mode=')[1]
        c.prove_method[farm] = prove_type
       # if c.prove_method[farm]
    
    elif "lotting sector" in line_plain and ("Subscribing to archived segments" not in line_plain and "failed to send sector index for initial plotting error=send failed because receiver is" not in line_plain):
        farm = line_plain[line_plain.find(
            indexconst) + len(indexconst):line_plain.find("}")]

        #c.sector_times = calculate_plot_time(farm, farm_id_mapping)
        #if 'Replotting' in line_plain.lower():
            
            

        if farm:
            c.curr_farm = farm
            #farmer_metrics(farm_id_mapping)
            
            if "eplotting complete" in line_plain or "nitial plotting complete" in line_plain:
                #c.curr_sector_disk[farm] = 0

                c.replotting[farm] = True
            else:
                plot_size = line_plain[line_plain.find(
                    "(")+1:line_plain.find("%")]
                if plot_size:
                    event_times[farm] = line_plain.split()[0]

        # websocket_client.main()
        trigger = True
    #elif 'Allocated space: ' in line_plain and c.curr_farm:
       # allocated_space = line_plain[line_plain.find(
      #      'Allocated space:'):line_plain.find("(")-1]
       # plot_space[c.curr_farm] = allocated_space.replace('Allocated space:','')
    
    elif 'Directory:' in line_plain and c.curr_farm:
       # directory =  line_plain.split('Directory: ')[1] #line_plain[line_plain.find(":") + 2:]
        drive_directory[c.curr_farm] = line_plain.split('Directory: ')[1] #directory
        c.curr_farm = None

    elif 'roving for solution skipped due to farming time limit' in line_plain:
        farm_skips = c.farm_skips
        farm = line_plain[line_plain.find(
            indexconst) + len(indexconst):line_plain.find("}:")]
        if farm:
            if farm not in farm_skips:
                farm_skips[farm] = 0
            farm_skips[farm] += 1
            c.farm_skips[farm] = farm_skips[farm]
    elif reward_phrase in line_plain:
        reward_count += 1
        c.reward_count = reward_count
        farm = line_plain[line_plain.find(
            indexconst) + len(indexconst):line_plain.find("}:")]
        if farm:
            if farm not in farm_rewards:
                farm_rewards[farm] = 0
            farm_rewards[farm] += 1
            c.farm_rewards[farm] = farm_rewards[farm]
        trigger = True

        if line_timestamp and line_timestamp > c.startTime:
            send(config['FARMER_NAME'] +
                 '| WINNER! You received a Vote reward!')

    if 'nitial plotting complete' in line_plain:
        if line_timestamp and line_timestamp > c.startTime:
            send(config['FARMER_NAME'] + '| Plot complete: ' +
                 line_plain[line_plain.find(
                     indexconst) + len(indexconst):line_plain.find("}:")] + ' 100%!')
        trigger = True
    
    #farmer_metrics(farm_id_mapping)
    
    if trigger:
        # websocket_client.main()
        trigger = False
 
    parsed_data['line_plain'] = local_time(line_plain)
    return parsed_data


def read_log_file():
    log_file_path = Path(config['FARMER_LOG'])
    farm_id_mapping = {}  # Initialize the farm_id_mapping dictionary
    if config['TOGGLE_ENCODING']:
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
                parsed_data = parse_log_line(line_plain, curr_farm, reward_count, farm_rewards,
                                             event_times, drive_directory,
                                              farm_skips,
                                             system_stats, farm_id_mapping,)  # Pass the farm_id_mapping
                vmem = str(psutil.virtual_memory().percent)
                c.system_stats = {'ram': str(round(psutil.virtual_memory().used / (1024.0 ** 3))) + 'gb ' + vmem + '%', 'cpu': str(psutil.cpu_percent()), 'load': str(round(psutil.getloadavg()[1], 2))}
                #system_stats = c.system_stats
                # Print the processed line to console
                print(parsed_data['line_plain'].replace('\n', ' '))
            except UnicodeDecodeError as e:
                print(f"Decode error encountered (Toggle TOGGLE_ENCODING in the config.yaml file): {e}")
            except KeyboardInterrupt:
                print('Fine, be that way!')
                quit()
            except Exception as e:
                print(f"An error occurred: {e}")
                
                console = Console()
                console.print_exception(show_locals=True)

            if config['IS_LIVE']:
                # Open the output file with utf-8 encoding to ensure Unicode support
                with open("farmlog.txt", "a+", encoding='utf-8') as file2:
                    file2.write(parsed_data['line_plain'] ) # + '\n')



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
        threading.Thread(target=read_log_file, daemon=True,
                         name='Read_log').start()
    


# RUN COMMAND - run specific file with arguments to capture output.
if config['COMMANDLINE'] and config['IS_LIVE']:
    cmd = config['COMMANDLINE']
else:
    cmd = ""
while True:
    run_command(cmd.split(), cwd=Path(__file__).parent.absolute())
