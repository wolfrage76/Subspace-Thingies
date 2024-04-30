import psutil
import asyncio
import datetime
from rich import print
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
import time
import yaml
import utilities.conf as c
import utilities.wallet as wallet
import utilities.farmer_socket as w
import threading
from utilities.menu_keys import KBHit
import utilities.node_monitor as node_monitor
import requests
from rich.traceback import install
from collections import defaultdict
import http.client
import urllib
from rich.live import Live
import os


install()

console = Console()

sum_size = defaultdict(lambda: [])
sumpsd = defaultdict(lambda: [])
sumps = defaultdict(lambda: [])
sumipds = {}
farmer_uptime = 0
sum_plotted = defaultdict(lambda: 0.0)
sum_unplotted = defaultdict(lambda: 0.0)

c.startTime = time.time()
with open("config.yaml", encoding='utf-8') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

c.theme = config.get('THEME', 'default')
if c.theme == None:    
    theme_file = 'utilities/fallback_theme.yaml'
else:
    theme_file = 'themes/' + c.theme + ".yaml"
    
with open(theme_file) as f:
    c.theme_data = yaml.load(f, Loader=yaml.FullLoader)

#################

global lang

c.lang = c.translation[config.get('LANGUAGE', 'en')]
lang = c.lang
day = lang.get('day', 'Day')

#c.show_logging = not config.get('SHOW_LOGGING')
c.hour_24 = config.get('HOUR_24', False)
c.ui_port = config.get('FRONT_END_PORT', '8016')
c.toggle_encoding = config.get('TOGGLE_ENCODING', False)
c.wallet = config.get('WALLET', None)
c.last_sector_only = config.get('LAST_SECTOR_ONLY',True)

c.running = True

def clean_thread():
    asyncio.run(cleanup_stale_farms(120))
    
def utility_thread():
    asyncio.run(utility_run(600))

async def utility_run(timeout=900,):  # 900 seconds = 15 minutes

    while c.running & config.get('USE_BANNERS', True):
      try:  
        url = 'http://subspacethingy.ifhya.com/info'
        response = requests.get(url)
        data = response.json()
        c.banners = data.get('info', lang.get('defaultbanner', 'See more community built tools at:') + " http://subspace.ifhya.com")
        c.ver = data.get('latestver', 'Unknown')
   
      except Exception as e:
          pass
      await asyncio.sleep(timeout)


def wallet_thread():
    wallet.WalletMon()


def ui_thread():
    while c.running:
        create_main_layout()
        time.sleep(.2)


uithread = threading.Thread(
    target=ui_thread, name='UI', daemon=True)

walletthread = threading.Thread(
    target=wallet_thread, name='Wallet', daemon=True)


def node_thread():
    #node_monitor.main()
    asyncio.run(node_monitor.fetch_node_info())


nodethread = threading.Thread(target=node_thread, name='Node', daemon=True)


async def cleanup_stale_farms(timeout=600,):  # 900 seconds = 15 minutes. Is later divided in half for 2 checks

    while c.running:
        current_time =  time.time()
        #removed = str()
        warning = str()
        stale_farms = [farm for farm, data in c.remote_farms.items(
        ) if current_time - data['last_update'] > timeout]
        
        c.warning_farms = stale_farms
        if len(c.warning_farms) > 0:
            send( lang.get('farmers', 'Farmers') + " Warning: Inactivity detected for: \n" + warning) 
               
        # Check twice within the timeout period
        await asyncio.sleep(timeout / 2)


def send(msg=None):
    # Discord

    if config.get('SEND_DISCORD', False) and config.get('DISCORD_WEBHOOK', False) and msg:

        
        data = {"content": msg}
        response = requests.post(config.get('DISCORD_WEBHOOK', None), json=data)
        success_list = [204]
        if response.status_code not in success_list:
            print(lang.get('error_sending', 'Error sending to ##').replace('##', ' Discord \n') + str(response.status_code))

    # Pushover

    if config.get('SEND_PUSHOVER') and config.get('PUSHOVER_APP_TOKEN') and config.get('PUSHOVER_USER_KEY') and msg:
        
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
                     urllib.parse.urlencode({
                         "token": config.get('PUSHOVER_APP_TOKEN'),
                         "user": config.get('PUSHOVER_USER_KEY'),
                         "message": msg,
                     }), {"Content-type": "application/x-www-form-urlencoded"})
        conn.getresponse()


def create_progress_bar1(completed: float, width: int) -> Progress:
    status_color =  color_by_status(completed)
    progress = Progress(
        TextColumn(status_color + " [progress.percentage]" + status_color +
                   "{task.percentage:>3.1f}%"),
        SpinnerColumn(),
        BarColumn(),
    )

    task_id = progress.add_task(
        description="",  completed=completed)

    return progress


def create_progress_bar(completed: float, width: int) -> Progress:
    progress = Progress(
        SpinnerColumn(),
        BarColumn(),
        # TextColumn("[bold green]{task.completed}/{task.total}"),
        # TextColumn("ETA: {task.fields[eta]}"),
        # expand=True
    )

    task_id = progress.add_task(
        description="",  completed=completed)

    return progress

def make_layout() -> Layout:
    """Define the layout."""
    layout = Layout(name="root")

    layout.split(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=4),
    )

    layout["main"].split_row(
        Layout(name="side",),
        Layout(name="body", ratio=2, minimum_size=20, visible=False),
        Layout(name="bodysum", minimum_size=20),
    )

    layout["body"].split_column(
        Layout(name="body1",),
        Layout(name="body2",),
    )

    layout["side"].split(Layout(name="box1"))
    layout['side'].visible = (c.view_state == 1 or c.view_state == 2)
    layout["bodysum"].split(Layout(name="sum1"))
    layout['bodysum'].visible = (c.view_state == 1 or c.view_state ==3)
    

    return layout


def convert_to_tib(space_str,):
    unit_multipliers = {
        'G': 1 / 1024,
        'GB': 1 / 1024,
        'GiB': 1 / (2**10),
        'T': 1 / (2**10 / 10**3),
        'TB': 1 / (2**10 / 10**3),
        'TiB': 1,
    }

    # Split the input string into value and unit
    if space_str == '-----':
        return '0'
    space_value, unit = space_str.split()
    space_value = (float(space_value) )  # Edited to proper size

    # Identify the unit and convert to TiB
    if unit in unit_multipliers:
        value_to_return_float = round(((space_value * (100/(100 - config.get('CACHE_SIZE', 1)))) * unit_multipliers[unit]) * 0.9843111634, 2)
        return f"{value_to_return_float:.2f}"
    else:
        return '0'

def create_footer(layout):
    footer_txt = Table.grid(expand=True, )
    footer_txt.add_column(ratio=2)
    footer_txt.add_column(ratio=5,)
    footer_txt.add_column(ratio=1)

    ver = c.ver
    footer_txt.add_row(Align.left(color('FOOTER_TEXT') + lang.get('latest', 'Latest') + ': ' + ver), Align.center(color('FOOTER_TEXT') + c.banners))
    
    footer = Panel(footer_txt, title= color('FOOTER_TEXT')+ "- [bold]BitcoinBart Was Here [/bold]-", border_style=color('FOOTER_FRAME'),
                   subtitle=color('FOOTER_ACCENT') + '[' + color('FOOTER_MENU') + '🡰 ' + color('FOOTER_ACCENT') + '|' + color('FOOTER_MENU') + '🡲' + color('FOOTER_ACCENT')  +  ' ]: ' + 
                   color('FOOTER_MENU') + 'Switch Farm ' + color('FOOTER_ACCENT') + ' [' + color('FOOTER_MENU') + lang.get('spacebar', 'Space') +color('FOOTER_ACCENT') +']: ' + 
                   color('FOOTER_MENU') + lang.get('pause', 'Pause')+ color('FOOTER_ACCENT') + '  [' + color('FOOTER_MENU') + 
                   lang.get('tab', 'Tab')+ color('FOOTER_ACCENT') + ']: ' + color('FOOTER_MENU') + lang.get('toggle_data', 'Toggle Data') + ' ' + 
                   color('FOOTER_ACCENT') + ' [' + color('FOOTER_MENU') + '1' + color('FOOTER_ACCENT') + '|' + color('FOOTER_MENU') + '2' + color('FOOTER_ACCENT') + '|' + 
                   color('FOOTER_MENU') +  '3' +  color('FOOTER_ACCENT') + color('FOOTER_ACCENT') + ']: ' + color('FOOTER_MENU') + lang.get('change_display', 'Change Display') +  
                   color('FOOTER_ACCENT') + ' [' + color('FOOTER_MENU') + '+' + color('FOOTER_ACCENT') + '|' + color('FOOTER_MENU') + '0' + color('FOOTER_ACCENT') +  '|' + 
                   color('FOOTER_MENU') + '-' + color('FOOTER_ACCENT')  + ']: ' + color('FOOTER_MENU') + lang.get('cycle_theme', 'Cycle Theme')  + ' ' + color('FOOTER_ACCENT') + 
                   ' [' + color('FOOTER_MENU') + 'Q' + color('FOOTER_ACCENT') +  ']' + color('FOOTER_MENU') + lang.get('quit', 'uit'), subtitle_align='right',height=3)
 
    return footer


class Header:
    peers = str(c.peers)
    def __rich__(self) -> Panel:
        if c.wallet and  config.get('NODE_IP') and config.get('NODE_PORT'):
            balance_info = str(c.balance)
        else:
            balance_info = " "
        peers  = c.peers or 0
        peercnt = ''
        if peers >= 40:
            peercnt = color('HEADER_GOOD') + str(peers) + color('HEADER_TEXT')
        elif peers  >= 30:
            peercnt = color('HEADER_AVERAGE') + str(peers) + color('HEADER_TEXT')
        elif peers  >= 15:
            peercnt = color('HEADER_LOW')  + str(peers) + color('HEADER_TEXT')
        else:
            peercnt =  color('HEADER_BAD') + str(peers) + color('HEADER_TEXT')
        
        ul = c.ul  or '0'
        dl = c.dl or '0'
        
        grid = Table.grid(expand=True)
        grid.add_column(justify="left")
        grid.add_column(justify="center")
        grid.add_column(justify="center")
        grid.add_column(justify="center")
        grid.add_column(justify="right")
       
        if config.get('NODE_IP') and config.get('NODE_PORT'):
            peerCount = lang.get('peers', 'Peers')  + ": " + peercnt
            
            ulDl = '' #f'   ({ul}kb/s |  {dl}kb/s) '
            if c.is_syncing:
                sync = '[blink]:warning: ' + color('HEADER_TEXT')  + '[' + color('HEADER_BAD')  + lang.get('unsynced', 'Unsynced')  + color('HEADER_TEXT')  +  '] :warning:[/blink] - '
            else: 
                sync = color('HEADER_TEXT') + ':zap:[' + color('HEADER_GOOD') + lang.get('synced', 'Synced')  + color('HEADER_TEXT') + '] - '
                
            blocks = sync + color('HEADER_TEXT') + lang.get('block', 'Block') + f': #{c.best_block}'.ljust(9)
        else:
            peerCount = ''
            ulDl = 'Subspace Farm Monitor Thingy'
            sync =''
            blocks = ''
        
        pause = ''
        if c.paused:
            pause = '[blink]' + color('ERROR')  +lang.get('pause','pause') + color('HEADER_TEXT') 
            
        grid.add_row( color('HEADER_TEXT') + lang.get('uptime', 'Up') + ': ' + getUptime(),
                     (peerCount + ulDl).ljust(3)
                     , ' ' + pause + ' ', blocks, balance_info.rjust(9) + "  ",
                     )
        return Panel(grid, style=color('HEADERSTYLE'))


def getUptime(started=None):
    """
    Returns the number of seconds since the program started.
    """
    if started == 0:
        return '--:--:--'
    elif started:
        sec = time.time() - started
    else:
        sec = time.time() - c.startTime

    return str(datetime.timedelta(seconds=sec)).split('.')[0]


class Farmer(object):
    def __init__(self, farmer_name="Unknown", replotting=None, warnings=None, errors=None, startTime='', farm_rewards=None, farm_recent_rewards=None, farm_skips=None, farm_recent_skips=None, disk_farms=None, last_sector_time=None, l3_concurrency='', l3_farm_sector_time='',):
        if errors is None:
            errors = []
        if disk_farms is None:
            disk_farms = {}
        if farm_rewards is None:
            farm_rewards = {}
        if farm_recent_rewards is None:
            farm_recent_rewards = {}
        if farm_skips is None:
            farm_skips = {}
        if farm_recent_skips is None:
            farm_recent_skips = {}
        if last_sector_time is None:
            last_sector_time = {}
        if warnings is None:
            warnings = []
        if replotting is None:
            replotting = {}

        self.farmer_name = farmer_name
        self.replotting = replotting
        self.warnings = warnings
        self.errors = errors
        self.startTime = startTime
        self.farm_rewards = farm_rewards
        self.farm_recent_rewards = farm_recent_rewards
        self.farm_skips = farm_skips
        self.farm_recent_skips = farm_recent_skips
        self.disk_farms = disk_farms
        self.last_sector_time = last_sector_time
        self.l3_concurrency = l3_concurrency
        self.l3_farm_sector_time = l3_farm_sector_time


def make_farmer(farmer_name="Unknown", replotting={}, warnings=[], errors=[],  startTime='', farm_rewards={}, farm_recent_rewards={}, farm_skips={}, farm_recent_skips={}, last_sector_time={}, l3_concurrency='', l3_farm_sector_time='' ):

    frmr = Farmer()
    frmr.farmer_name = farmer_name
    frmr.replotting = replotting
    frmr.warnings = warnings
    frmr.errors = errors
    frmr.startTime = startTime
    frmr.farm_rewards = farm_rewards
    frmr.farm_recent_rewards = farm_recent_rewards
    frmr.farm_skips = farm_skips
    frmr.farm_recent_skips = farm_recent_skips
    frmr.last_sector_time = last_sector_time
    frmr.l3_concurrency = l3_concurrency
    frmr.l3_farm_sector_time = l3_farm_sector_time

    return frmr


# Creating WebSocket server

def start():
    asyncio.run(main())


def make_waiting_message() -> Panel:
    """Create a 'Waiting for data' message."""
    return Panel("Waiting for data...", style="yellow")


def socket_thread():
    w.start()


socketthread = threading.Thread(
    target=socket_thread, name='Socket', daemon=True)

def color(data=None, offline=False):
    specials = ['SUMMARY_FRAME', 'FARMER_FRAME', 'HEADER_BACKGROUND', 'FARMER_STATS_FRAME','FOOTER_FRAME', 'FARMER_STATS_FRAME', 'SUMMARY_GLOBAL_FRAME']
    
    
    if offline and data not in specials:
        return '[' + c.theme_data.get('ERROR', 'red') + ']'
    elif offline and data in specials:
        return c.theme_data.get('ERROR', 'red')
    elif data == None:
        return '[b white]'
    elif data == 'HEADERSTYLE':
        return c.theme_data.get('HEADER_TEXT') + ' on ' + c.theme_data.get('HEADER_BACKGROUND')
    elif data in specials:
        return c.theme_data.get(str(data), 'b white')
    else:
        return '[' + c.theme_data.get(str(data), 'b white') + ']'
    
    #return color_build

def color_by_status(percent, replot=False, offline=False):
    
    if offline:
        return color('ERROR', offline)
    colors = [color('STATUS_REPLOTTING'), color('STATUS_100'),color('STATUS_90'), color('STATUS_75'), color('STATUS_50'),color('STATUS_25'), color('STATUS_15') , color('STATUS_0')]
    if replot: 
        return colors[0]
    elif percent == 100:
        return colors[1]
    elif percent >= 90:
        return colors[2]
    elif percent >= 75:
        return colors[3]
    elif percent >= 50:
        return colors[4]
    elif percent >= 25:
        return colors[5]
    elif percent >= 15:
        return colors[6]
    else:
        return colors[7]    


def convert_to_percent(load_tuple):
    num_log_cpus = psutil.cpu_count()

    percent_lst = []

    for load in load_tuple:
        percent = (load / num_log_cpus) * 100
        percent_lst.append(percent)

    return tuple(percent_lst)


load_tuple = psutil.getloadavg()


def build_ui():
    layout = make_layout()

    layout["header"].update(Header())
    layout["body"].visible = False# (c.view_state == 1 or c.view_state ==3)
    layout["side"].visible = (c.view_state == 1 or c.view_state == 2)
    layout["box1"].update(Panel("", border_style=color('FARMER_FRAME'), title=color('FARMER_TILE') + "Waiting for Farmers...",
                                subtitle=color('STATUS_0') + "<25% | " + color('STATUS_25') + '>25% | ' + color('STATUS_75') +  '>75% | ' + color('STATUS_100') +  "100%" + ' | ' + color('STATUS_REPLOTTING') + 'Replotting'))
    
    layout["bodysum"].visible = (c.view_state == 1 or c.view_state == 3)
    layout["sum1"].update(Panel("", border_style=color('SUMMARY_FRAME'), title=color('SUMMARY_TILE') +"Waiting for Farmers...",
                                subtitle=color('STATUS_0') +"<25% | " + color('STATUS_25') + '>25% | ' + color('STATUS_75') +  '>75% | ' + color('STATUS_100') +  "100%"))
    footer_txt = Table.grid(expand=True)
    footer_txt.add_row(Align.left(lang.get('latest', 'Latest') + c.ver + ' '),  Align.center(c.banners))  

    layout["footer"].update(create_footer(layout))
    
    return layout


def format_time(minutes, seconds):
    return f"{str(minutes).zfill(2)}:{str(seconds).zfill(2)}"

def calculate_average_plotting_time_for_farmer(farmer_metrics):
    total_plotting_time = 0
    total_sector_count = 0

    for disk_metrics in farmer_metrics.values():
        tnp = float(disk_metrics.get('subspace_farmer_sectors_total_sectors_NotPlotted', {}).get('value', 0))
        tse = float(disk_metrics.get('subspace_farmer_sectors_total_sectors_Expired', {}).get('value', 0))
        tae = float(disk_metrics.get('subspace_farmer_sectors_total_sectors_AboutToExpire', {}).get('value', 0))
        
        if (tnp + tse + tae) > 0:    
            plotting_time_sum = float(disk_metrics.get('subspace_farmer_sector_plotting_time_seconds_sum', {}).get('value', 0))
            sector_count = float(disk_metrics.get('subspace_farmer_sector_plotting_time_seconds_count', {}).get('value', 0))
        else:
            plotting_time_sum = 0
            sector_count = 0

        total_plotting_time += plotting_time_sum
        total_sector_count += sector_count

    if total_sector_count > 0:
        average_plotting_time = total_plotting_time / total_sector_count
    else:
        average_plotting_time = 0

    return average_plotting_time


def seconds_to_mm_ss(seconds):
    
    minutes = seconds // 60
    seconds = seconds % 60
    return str(int(minutes)).zfill(2) + ':' + str(int(seconds)).zfill(2)

def hours_to_dh_m(hours):
    days = hours // 24
    hours %= 24
    minutes = (hours % 1) * 60

    if days > 0:
        return f"{int(days)}d {int(hours)}h"
    else:
        return f"{int(hours)}h {int(minutes)}m"
    


def create_summary_layout(layout):
    c.farm_names = c.farm_names or []
    c.remote_farms = c.remote_farms or {}
    c.farm_names = c.farm_names or []
    c.remote_farms = c.remote_farms or {}
    
    # Initialize variables for global stats
    global_drive_count = 0
    global_farm_plotted = 0.0
    global_farm_notplotted = 0.0
    global_farm_expired = 0.0
    global_farm_about_expire = 0.0
    global_total_rewards = 0
    global_skips = 0
    global_recenttotal_rewards = 0
    global_recentskips = 0
    global_hhr = 0
    global_hhr_formated = str()
    global_h_tibs = 0.0
    global_h_tib = ''
    global_hhr_sum = 0
    total_nocount = 0
    total_calc_avg = 0
    global_sec_day_total = 0.0
    global_sec_hr_total = 0.0
    global_last_sector_time = 0.0
    longest_eta = 0
    
    
    while c.running:
        
        progress_table2 = Table.grid(expand=True)
        progress_table2.add_column(width=12)
        global_table = Table.grid(expand=True)
        global_table.add_column(width=12)
        c.sum_size = {}
        c.sum_plotted = {}
        
        for farmer_index in range(len(c.farm_names)):
            drive_count = 0
            calc_avg = 0.0
            
            is_completed = []
            is_replotting = []
            farm_expired = 0.0
            farm_about_expire = 0.0
            farm_plotted = 0.0  # Initialize farm_plotted here
            farm_notplotted = 0.0  # Initialize farm_notplotted here
            farm_last_sector_time = 0.0
            total_sectors = defaultdict(float)  # Initialize total_sectors here
            try:
                progress_items = Table.grid(expand=False)
                progress_items.add_column(width=16)
                progress_items.add_column(width=14)
                progress_items.add_column(width=18)
                progress_items.add_column(width=14)
                progress_items.add_column(width=6)
                farmer_name = c.farm_names[farmer_index % len(c.farm_names)]
                farm_info = c.remote_farms.get(farmer_name, {})

                farmer_data = farm_info.get('data', {})
                if not farmer_data:
                    continue

                c.warnings = farmer_data.get('warnings', [])
                c.errors = farmer_data.get('errors', [])

                #total_completed = c.psTotal / c.psdTotalsss
                farm_plotted = 0.0
                farm_expired = 0
                farm_about_expire = 0
                total_sectors = defaultdict(float)
                farm_notplotted = 0.0
                drive_count = 0
                #and total_sectors.get('NotPlotted', 0) == 0
                for disk in farmer_data.get("disk_farms", []):
                    #farm_notplotted = 0
                    
                    total_sectors['Expired'] = 0
                    total_sectors['NotPlotted'] = 0
                    total_sectors['Plotted'] = 0
                    total_sectors['AboutToExpire'] = 0
                    
                    disk_metrics = farmer_data.get('farm_metrics', {}).get(disk, {})
                    
                    for state in ["Plotted", "Expired", "AboutToExpire", "NotPlotted"]:
                        key = f"subspace_farmer_sectors_total_sectors_{state}"
                        total_sectors[state] += float(disk_metrics.get(key, {}).get('value', 0))

                    farm_expired += total_sectors.get('Expired',0)
                    farm_plotted += total_sectors.get('Plotted',0)
                    farm_notplotted += total_sectors.get('NotPlotted',0)
                    farm_about_expire += total_sectors.get('AboutToExpire',0)


                    if total_sectors.get('Plotted',0) + total_sectors.get('NotPlotted',0) + total_sectors.get('Expired', 0) + total_sectors.get('AboutToExpire', 0) == 0:
                        continue
                 
                    if total_sectors.get('NotPlotted',0) == 0 and total_sectors.get('Expired', 0) == 0 and total_sectors.get('AboutToExpire', 0) == 0:
                        is_completed.append(disk)
                    else:
                        farm_last_sector_time += c.last_sector_time.get(farmer_name, {}).get(disk, 0) 
                    
                    if total_sectors.get('Expired', 0) > 0 or total_sectors.get('AboutToExpire', 0) > 0:
                        is_replotting.append(disk)
   
                    drive_count += 1


                total = sum(farmer_data.get('farm_rewards', {}).values())
                skips = sum(farmer_data.get('farm_skips').values())  
                recenttotal = sum(farmer_data.get('farm_recent_rewards', {}).values())
                recentskips = sum(farmer_data.get('farm_recent_skips').values())  

    
                nocount = (drive_count - (len(is_completed)))
                if nocount <=0:
                    calc_avg = 0
                else:
                    if c.last_sector_only == False:
                        calced = calculate_average_plotting_time_for_farmer(farmer_data.get('farm_metrics', {}))
                    else:
                        calced = farm_last_sector_time / nocount
                    calc_avg = calced / nocount

                calc_avg = farmer_data['l3_farm_sector_time']
                
                if (farm_notplotted + farm_expired + farm_about_expire) != 0 and farmer_data.get('farm_metrics') and calc_avg > 0:
                    sec_hr = 3600 / calc_avg
                    eta = (farm_notplotted + farm_expired + farm_about_expire) / sec_hr
                else:
                    sec_hr = 0
                    eta = 0
                
                if eta > longest_eta:
                    longest_eta = eta
                    
                sec_day = (sec_hr * 24)  * 0.9843111634 # GiB to actual sector size
                
                if (farm_notplotted + farm_plotted + farm_about_expire + farm_expired == 0)  :
                    sumipds = 0
                else:
                    sumipds = farm_plotted / (farm_notplotted + farm_plotted + farm_about_expire + farm_expired) * 100
                
                
                global_drive_count += drive_count
                global_farm_plotted += farm_plotted
                global_farm_notplotted += farm_notplotted
                global_farm_expired += farm_expired
                global_farm_about_expire += farm_about_expire
                global_total_rewards += total
                global_recenttotal_rewards += recenttotal
                global_skips += skips
                global_recentskips += recentskips
                global_sec_day_total += sec_day #* nocount  # Multiply by nocount to get total bytes/day for this farm
                global_sec_hr_total += sec_hr 
                total_nocount += nocount  # Accumulate non-completed drives for weighted average calculation
                total_calc_avg += calc_avg * nocount  # Weighted sum for average calculation

                #tibs = convert_to_tib(tibs + ' GiB')
                
                hits_day = c.rewards_per_hr.get(farmer_name, 0) * 24
                if farm_plotted == 0:
                    tibs = '0.0'
                else:
                    tibs = f'{hits_day / (farm_plotted * (1 / (2**10)) ):.2f}'
                global_hhr_sum += c.rewards_per_hr.get(farmer_name, 0)
                h_tib = '  ' + color('SUMMARY_ACCENT')  + lang.get('single_hits', 'H')  + '/TiB/' + day +  ': ' + color('SUMMARY_VALUE') + tibs
                if global_farm_plotted == 0:
                    global_h_tibs = '0.0'
                else:
                    global_h_tibs = f'{(global_recenttotal_rewards / (global_farm_plotted * (1 / (2**10))) ):.2f}'
                global_h_tib = '  ' + color('SUMMARY_ACCENT')  + lang.get('single_hits', 'H')  + '/TiB/' + day +  ': ' + color('SUMMARY_VALUE') + global_h_tibs

                hhr_formated = f'{c.rewards_per_hr.get(farmer_name, 0):.2f}'
               
                if farmer_name in c.warning_farms:
                    offline = True
                else:
                    offline = False
               
                hhr =  color('SUMMARY_ACCENT', offline) + ' ' + lang.get('single_hits', 'H') + color('SUMMARY_ACCENT', offline) +'/' + lang.get('hour', 'hr')+ ': ' + color('SUMMARY_VALUE', offline) + hhr_formated
                
                global_hhr_formated = f'{float(global_hhr_sum):.2f}'
                global_hhr =  ' '+ color('SUMMARY_ACCENT')   + lang.get('single_hits', 'H') + color('SUMMARY_ACCENT')  + '/' + lang.get('hour', 'hr')+ ': ' + color('SUMMARY_VALUE')   + global_hhr_formated
                

                progress_items.add_row( color('SUMMARY_VALUE', offline) + convert_to_tib(str(farm_plotted) + ' GB').rjust(5) + color('SUMMARY_ACCENT', offline) + '/' + color('SUMMARY_VALUE', offline)  + convert_to_tib(str(farm_notplotted + farm_plotted + farm_expired + farm_about_expire) + ' GB') + color('SUMMARY_ACCENT', offline) +' TiB ',color('SUMMARY_ACCENT', offline) + '('  + color('SUMMARY_VALUE', offline) +  '+' + str(convert_to_tib(str(sec_day)  + ' GB')) + color('SUMMARY_ACCENT', offline) + '/' + color('SUMMARY_VALUE', offline)+ day + ') ', color('SUMMARY_ACCENT', offline) +  lang.get('avgsector', '   Avg Sector') +': ' + color('SUMMARY_VALUE', offline)  + seconds_to_mm_ss(calc_avg) , color('SUMMARY_ACCENT', offline) + ' ETA: ' + color('SUMMARY_VALUE', offline) + hours_to_dh_m(eta) + ' ', create_progress_bar(sumipds, 5))

                progress_table2.add_row(Panel(
                progress_items, title_align='left', title=color('SUMMARY_TITLE', offline) + farmer_name + color('SUMMARY_ACCENT', offline) + ' (' + color_by_status(sumipds, False, offline) + str(drive_count)
                + 'x ' +  lang.get('plots', 'Plots') + ' - ' + str(round(sumipds, 1)) + '%' + color('SUMMARY_ACCENT', offline) + ')' , border_style=color('FARMER_FRAME', offline), subtitle_align='right', subtitle= color('SUMMARY_REWARDS', offline) 
                + lang.get('single_hits', 'H') + color('SUMMARY_ACCENT', offline) + '/' + color('SUMMARY_MISSES', offline) +lang.get('single_misses', 'M') + color('SUMMARY_ACCENT', offline) +  ': ' 
                + color('SUMMARY_REWARDS', offline) + str(recenttotal) + color('SUMMARY_ACCENT', offline) +'/' + color('SUMMARY_MISSES', offline) + str(recentskips) + ' ' + color('SUMMARY_ACCENT', offline) + hhr + h_tib),)
                
            except Exception as e:
                console.print(lang.get('an_error_occured', "An error occurred ") + ' ' + str(e) )
                console.print_exception()
                time.sleep(10)
        
        if global_sec_hr_total > 0:
            global_avg_sector_time = 3600 / global_sec_hr_total if (total_nocount > 0) else 0
        else:
            global_avg_sector_time = 0
        # Calculate global percentages and other stats as needed
        global_sumipds = (global_farm_plotted / (global_farm_notplotted + global_farm_plotted + global_farm_expired + global_farm_about_expire) * 100 if global_farm_notplotted + global_farm_plotted != 0 else 0)
        
        
# Add a row for global stats at the top of progress_table2
        
        global_progress_items = Table.grid(expand=False)
        global_progress_items.add_column(width=30)
        global_progress_items.add_column(width=18)
        global_progress_items.add_column(width=14)
        
       

        global_progress_items.add_row(color('SUMMARY_VALUE') + convert_to_tib(str(global_farm_plotted) + ' GB') + color('SUMMARY_ACCENT') +'/' + color('SUMMARY_VALUE')  + convert_to_tib(str(global_farm_notplotted + global_farm_plotted + global_farm_expired + global_farm_about_expire) + ' GB')+ color('SUMMARY_ACCENT')  + ' TiB ' +color('SUMMARY_VALUE') +  color('SUMMARY_VALUE') + '(+' + str(convert_to_tib(str(global_sec_day_total) + ' GB')) + color('SUMMARY_ACCENT') + '/' + color('SUMMARY_VALUE') + day + color('SUMMARY_ACCENT') + ')',  color('SUMMARY_ACCENT') + lang.get('avgsector', 'Avg') + ': ' + color('SUMMARY_VALUE') + seconds_to_mm_ss(global_avg_sector_time), color('SUMMARY_VALUE') +  color('SUMMARY_ACCENT') + ' ETA: ' +  color('SUMMARY_VALUE')  + hours_to_dh_m(longest_eta), create_progress_bar(global_sumipds, 12))
        

        
        global_table.add_row(Panel(
            global_progress_items, title_align='left', title=f"{color('SUMMARY_GLOBAL_TITLE') + lang.get('global_stats', 'Global Stats')} "  + color('SUMMARY_VALUE') + "(" + color_by_status(global_sumipds) + str(global_drive_count) + 'x ' + lang.get('plots', 'Plots') + ' - ' + str(round(global_sumipds,1)) + '%' + color('SUMMARY_ACCENT') +')' , border_style=color('SUMMARY_GLOBAL_FRAME'), subtitle_align='right', subtitle=color('SUMMARY_REWARDS') + lang.get('single_hits', 'H') + color('SUMMARY_ACCENT') + '/'+ color('SUMMARY_MISSES') + lang.get('single_misses', 'M') + ': ' + color('SUMMARY_REWARDS') + str(global_recenttotal_rewards) + color('SUMMARY_ACCENT') + '/' + color('SUMMARY_MISSES') + str(global_recentskips) + ' ' + str(global_hhr) + str(global_h_tib)))

        global_table.add_row(end_section=True)
        global_table.add_row(progress_table2)


        layout["sum1"].update(Panel(global_table, border_style=color('SUMMARY_FRAME'), title= color('SUMMARY_FRAME_TITLE') + str(len(c.remote_farms)) + ' ' + lang.get('farmers', 'Farmers'), subtitle= color('STATUS_0') + "<25% | " + color('STATUS_25') + '>25% | ' + color('STATUS_75') +  '>75% | ' + color('STATUS_100') +  "100%"))
        
        time.sleep(.1)
        return layout


""" def convert_svg_to_pdf():
    export_console = Console(record=True)
    content = c.layout['sum1']
    export_console.print(content)

    # Export console output to SVG
    svg_data = export_console.export_svg(title=lang.get('farmer', 'Farmer'))
    with open('output.svg', 'w') as svg_file:
        svg_file.write(svg_data)

    cairosvg.svg2png(url='output.svg', write_to='FarmerReport.png')
    os.remove('output.svg')
    requests.post(config.get('DISCORD_WEBHOOK', None), files={"file": open('FarmerReport.png', "rb")})
    os.remove('FarmerReport.png')
 """    
 
 
def format_s_ms(milliseconds):
    if float(milliseconds) < 1000:
        if float(milliseconds) > 200:
            return color('WARNING') + f"{milliseconds}ms"
        else:    
            return f"{milliseconds}ms"
    else:
        seconds = milliseconds / 1000.0
        if seconds >= 1:
            return color('ERROR') + f"{seconds:.2f}s"
        else:
            return color('WARNING') + f"{seconds:.2f}s"
        

        
def update_farmer_index():
    cooldown_period = 7  # Cooldown period in seconds after a manual update
    while c.running:
        if len(c.farm_names) > 0 and not c.paused:
            current_time = time.time()
            time_since_last_manual_update = current_time - c.last_manual_update_time

            # Rotate index only if cooldown period has elapsed
            if time_since_last_manual_update > cooldown_period :
                c.current_farmer_index = (c.current_farmer_index + 1) % len(c.farm_names)
                time.sleep(5)  # Regular update interval
        time.sleep(.1)
                
                
def create_main_layout():     
            
    layout = c.layout
    layout["side"].visible = c.view_state in {1, 2}
    layout["bodysum"].visible = c.view_state in {1, 3}
    #layout["box1"].visible = c.view_xtras
    c.layout = layout
    c.farm_names = c.farm_names or []
    c.remote_farms = c.remote_farms or {}
    sum_plotted = defaultdict(lambda: {})
    sum_size = defaultdict(lambda: {})

    #farmer_name = c.farm_names[c.current_farmer_index % len(c.farm_names)]
    #while True:
   
   
   # while c.paused:
   #     if not c.force_update:
   #         time.sleep(.2)   
   #     else:
   #         c.force_update = False
        
        #time.sleep(.2)
            
                         
                  
    try:
            
        if len(c.farm_names) > 0:
            farmer_name = c.farm_names[c.current_farmer_index % len(c.farm_names)]
        #        else: 
        #           continue
            farm_info = c.remote_farms.get(farmer_name, {})
            farmer_data = farm_info.get('data', {})
                

            #if not farmer_data:
            #    continue
            c.warnings = farmer_data.get('warnings', [])
            c.errors = farmer_data.get('errors', [])


            job_progress = Progress("{task.description}",
                                    SpinnerColumn(),
                                    TextColumn(
                                        "[progress.percentage]" + color('PERCENT') + "{task.percentage:>5.1f}%"),
                                    BarColumn(bar_width=8),)

    
            if farmer_data.get('farm_rewards', {}).values():
                total = sum(farmer_data.get('farm_rewards', []).values()) # total = sum(c.farm_rewards[farmer_name].values())
            else:
                total = 0
            if farmer_data.get('farm_skips', {}).values():
                skips = sum(farmer_data.get('farm_skips', {}).values()) # total = sum(c.farm_rewards[farmer_name].values())
            else:
                skips = 0
            # skips = sum(farmer_data.get('farm_skips',{}).values())

            if farmer_data.get('farm__recent_rewards', {}).values():
                recenttotal = sum(farmer_data.get('farm_recent_rewards', []).values()) # total = sum(c.farm_rewards[farmer_name].values())
            else:
                recenttotal = 0
                
            if farmer_data.get('farm_recent_skips', {}).values():
                recentskips = sum(farmer_data.get('farm_recent_skips', {}).values()) # total = sum(c.farm_rewards[farmer_name].values())
            else:
                recentskips = 0
            #  recentskips = sum(farmer_data.get('farm_recent_skips',{}).values())

            
            ipds = 0.0
            psd = 0.0
            remspace = 0.0
            sector = 0
            lastsectortime = 0
            c.psTotal = 0.0
            c.psdTotal = 0.0
            c.remTotal = 0.0
            
            for farm in sorted(filter(None, farmer_data.get("disk_farms")), key=int):
                is_completed = []
                is_replotting = []
                total_sectors = defaultdict(float)
                total_sectors['Expired'] = 0
                total_sectors['NotPlotted'] = 0
                total_sectors['Plotted'] = 0
                total_sectors['AboutToExpire'] = 0

                                    
                if farmer_data.get('farm_metrics', {}).get(farm, {}).get('subspace_farmer_sectors_total_sectors_Plotted'):
                    
                    psd = float(farmer_data.get('farm_metrics', {}).get(farm, {}).get('subspace_farmer_sectors_total_sectors_Plotted').get('value', 0))
                else: psd = 0
                
                if farmer_data.get('farm_metrics', {}).get(farm, {}).get('subspace_farmer_sectors_total_sectors_NotPlotted'):
                        remspace = float(farmer_data['farm_metrics'][farm]['subspace_farmer_sectors_total_sectors_NotPlotted'].get('value', 0))
                else:
                    remspace = 0
                
                replotspace = float(farmer_data.get('farm_metrics', {}).get(farm, {}).get('subspace_farmer_sectors_total_sectors_Expired', {}).get('value', 0)) + float(farmer_data.get('farm_metrics', {}).get(farm, {}).get('subspace_farmer_sectors_total_sectors_AboutToExpire', {}).get('value', 0)) 

                
                ps = remspace + psd + replotspace
                c.psTotal += ps
                c.psdTotal += psd
                c.remTotal += remspace
                
                
                if psd == 0 or ps == 0:
                    ipds = 0
                else:
                    ipds = (psd / ps) * 100
                if farmer_data.get('farm_metrics', {}).get(farm, {}):
                    sector = farmer_data.get('farm_metrics', {}).get(farm, {}).get('subspace_farmer_sectors_total_sectors_Plotted', {}).get('value', 0)
                else: 
                    sector = 0
                sector = '#' + str(sector)

                c.farm_rewards[farmer_name][farm] = c.farm_rewards.get(farmer_name, {}).get(farm, 0)
                c.farm_recent_rewards[farmer_name][farm] = c.farm_recent_rewards.get(farmer_name, {}).get(farm, 0)
                
                if farmer_data.get('farm_metrics', {}).get(farm):
                    summedPlotting = float(farmer_data['farm_metrics'].get(farm, ).get('subspace_farmer_sector_plotting_time_seconds_sum', {}).get('value','0')) 
                else:
                    summedPlotting = 0
                plottingCount = farmer_data.get('farm_metrics', {}).get(farm,{}).get('subspace_farmer_sector_plotting_time_seconds_count',{}).get('value', 0.0)
                
                
                if plottingCount == 0 or (remspace + replotspace == 0) :
                    averageTime = "00:00"
                else:
                    averageTime = seconds_to_mm_ss(summedPlotting / float(plottingCount))   # str(c.avgtime.get(farmer_name, {}).get(farm, '00:00'))

                disk_metrics = farmer_data.get('farm_metrics', {}).get(farm, {})
                
                for state in ["Plotted", "Expired", "AboutToExpire", "NotPlotted"]:
                    key = f"subspace_farmer_sectors_total_sectors_{state}"
                    total_sectors[state] += float(disk_metrics.get(key, {}).get('value', 0))
                
                if total_sectors.get('NotPlotted', 0) == 0 and total_sectors.get('AboutToExpire', 0) == 0 and total_sectors.get('Expired', 0) == 0 and total_sectors.get('Plotted', 0) > 0 :
                    #replotting_count += 1
                    is_completed.append(farm)
                    
                if total_sectors.get('AboutToExpire', 0) > 0 or total_sectors.get('Expired', 0) > 0:
                    #replotting_count += 1
                    is_replotting.append(farm)

                
                #replot = False
                if farm in is_completed and farm not in is_replotting:
                    ipds = 100
                    averageTime = "--:-- "
                    sector = '-----'
                elif c.last_sector_only:
                    averageTime =  seconds_to_mm_ss(c.last_sector_time.get(farmer_name, {}).get(farm, 0)) + ' ' 

                prove = ''
                
                
                proving_avg =  '{:.2f}'.format(round(float(farmer_data.get('proves', {}).get(farm, 0.0)),2)).lstrip('0')
                
                if proving_avg == '.00':
                    proving = '----'
                else:
                    if float(proving_avg) >= 10:
                        proving = '[blink]' + color('ERROR') + '>' + str(int(float(farmer_data.get('proves', {}).get(farm, 0.0)))) + 's'
                    elif float(proving_avg) >= 4:
                        proving = '[blink]' + color('ERROR') + str(round(float(farmer_data.get('proves', {}).get(farm, 0.0)),2)) + 's'
                    elif float(proving_avg) > 2:
                        proving = color('WARNING') + str(float(farmer_data.get('proves', {}).get(farm, 0.0))) + 's'
                    else:
                        proving = proving_avg + 's'
                        
                auditing_avg = int(float(farmer_data.get('audits', {}).get(farm, 0.0)))

                if farmer_data.get('prove_method', {}).get(farm, str()) == 'WS':
                    prove = '  [b yellow][[blink][b dark_orange]WS[/blink][b yellow]] '
                if farmer_data.get('prove_method', {}).get(farm, str()) == 'CC':
                    pass  
                farmid = farm
                farmid = c.drive_directory.get(farmer_name, {}).get(farm, '')
                if farmid == '':
                    continue
                
                if c.view_xtras:
                    sectortxt = str(sector).ljust(5)
                else:
                    sectortxt = ''
                    averageTime = ''

                    e = False
                    
                    # removed Sector + sectortxt
                if ps > 0: # Remove dropped drives from display
                    job_progress.add_task(prove + color_by_status(ipds, farm in is_replotting) + (farm + ':').ljust(3) + farmid.ljust(get_max_directory_length(farmer_name)) +  (' (' + convert_to_tib(str(psd) + ' GB') + '/' + convert_to_tib(str(ps) + ' GB') + ' TiB)').ljust(18)  + ' ' + averageTime + color('FARMER_REWARDS') + lang.get('single_hits','H') + color('FARMER_ACCENT') + '/'+ color('FARMER_MISSES') + lang.get('single_misses','M') + color('FARMER_MISSES') + ': ' + color('FARMER_REWARDS')  + str(c.farm_recent_rewards.get(farmer_name, {}).get(farm, 0)).rjust(2) + str(color('FARMER_ACCENT') + '/' + color('FARMER_MISSES'))  + str(c.farm_recent_skips.get(farmer_name, {}).get(farm, 0)).ljust(2) + color('FARMER_ACCENT') + ' A: ' + color('FARMER_VALUE') + format_s_ms((auditing_avg)).rjust(5) +  color('FARMER_ACCENT') + ' P: '+ color('FARMER_VALUE') + str(str(proving)).rjust(5), completed=ipds)

            if ipds > 0:
                total_completed = ipds
            else:
                total_completed = 0
            c.total_completed = total_completed

            progress_table = Table.grid(expand=True)

            
            progress2 = Progress(
                "{task.description}",
                SpinnerColumn(),
                TextColumn("[progress.percentage]" + color('PERCENT') + "{task.percentage:>5.1f}%"),
                BarColumn(),
            )
            #completed = 0.0
            if total_completed == 100:
                    progress2.add_task('[white]', completed=100)
            elif total_completed > 0:
                progress2.add_task('[white]', completed=(c.psdTotal/c.psTotal) * 100)
                c.psTotal += ps
                c.psdTotal += psd
                c.remTotal += remspace
            total = 0
            for key in c.farm_rewards.get(farmer_name, {}).keys():
                total = total + c.farm_rewards[farmer_name][key]
            for key in c.farm_recent_rewards.get(farmer_name, {}).keys():
                recenttotal = recenttotal + c.farm_recent_rewards[farmer_name][key]


            progress_table.add_column(min_width=25)

            tmp = Table.grid()
            tmp.add_column(width=13)
            tmp.add_column()
            tmp.add_row(progress2,' ' + color('FARMER_ACCENT') + ' ' + lang.get('cpu','CPU') + ': ' + color('FARMER_VALUE') + farmer_data.get('system_stats').get('cpu') + "%  " + color('FARMER_ACCENT') + lang.get('ram','RAM') + ": " + color('FARMER_VALUE') + farmer_data.get('system_stats').get('ram').replace(' ', color('FARMER_ACCENT') + '/' + color('FARMER_VALUE')) + '  '  + color('FARMER_ACCENT') + lang.get('load','Load') + ': ' + color('FARMER_VALUE') +farmer_data.get('system_stats').get('load', 0.0))

            progress_table.add_row(Panel(
                tmp, border_style=color('FARMER_STATS_FRAME'), subtitle_align='right' , subtitle=color('FARMER_ACCENT') + lang.get('rewards', 'Rewards') + ': ' + color('FARMER_REWARDS') + str(recenttotal) + color('FARMER_ACCENT') + '/' + color('FARMER_MISSES') + str(recentskips),))
            
            progress_table.add_row(job_progress, )
            UpTime = getUptime(farmer_data['startTime'])
            if UpTime == '--:--:--':
                frame_color = color('FARMER_VALUE', True)
            else: 
                frame_color = color('FARMER_VALUE')
            layout["box1"].update(Panel(progress_table, border_style=color('FARMER_FRAME'), title=color('FARMER_ACCENT') + f"{lang.get('farmer', 'Farmer')}: " + color('FARMER_VALUE') + farmer_name + color('FARMER_ACCENT') + " [" + frame_color + lang.get('uptime', 'Up') + ": " + UpTime + color('FARMER_ACCENT') + "] ", subtitle=color('STATUS_0') +"<25% | " + color('STATUS_25') + '>25% | ' + color('STATUS_75') +  '>75% | ' + color('STATUS_100') +  "100% | "+ color('STATUS_REPLOTTING')  + lang.get('replotting', 'Replotting')  ))
            
            c.sum_plotted = sum_plotted
            c.sum_size = sum_size
            
            time.sleep(.02)
            
    except Exception as e:
        console.print_exception()
        error_msg = lang.get('an_error_occurred', 'An error occured') + ' ' + lang.get('retrying_seconds', 'Pausing ## seconds').replace('##', '10') + '\n' + str(e)
        
        console.print(error_msg)
        time.sleep(10)
        # Add some additional error handling code here


cleanthread = threading.Thread(
    target=clean_thread, name='Cleaning', daemon=True)

utilthread = threading.Thread(
    target=utility_thread, name='Utils', daemon=True)

def get_max_directory_length(farmer_name):
    if farmer_name not in c.drive_directory:
        return 0  # Return 0 if the farmer name is not in the directory

    max_length = 0
    for farm in c.drive_directory[farmer_name]:
        directory = c.drive_directory[farmer_name][farm]
        if len(directory) > max_length:
            max_length = len(directory)

    return max_length # + 2  # Add 2 to the maximum length



async def main():
    layout = build_ui()  # Build and retrieve the UI layout
    layout["main"].update(make_waiting_message())
    c.layout = layout
    
    kb = KBHit(lambda: layout.update(layout), create_main_layout)   
    kb.start()
    
    if config.get('WALLET', False) and config.get('NODE_IP', False) and config.get('NODE_PORT', False):
        walletthread.start()
        
    if config.get('NODE_IP', False) and config.get('NODE_PORT', False):
        nodethread.start()
    
    socketthread.start()
    uithread.start()

    cleanthread.start()
    utilthread.start()
    
    index_thread = threading.Thread(target=update_farmer_index, name='IndexUpdater', daemon=True)
    index_thread.start()

   
    
    try:

        with Live(layout, refresh_per_second=4, screen=True) as live:
            while c.running: #while True:
                if not c.running:
                    print('Toodles!')
                    break

                layout["body"].visible = False
                layout["side"].visible = c.view_state in {1, 2}
                layout["bodysum"].visible = c.view_state in {1, 3}
                layout["footer"].update(create_footer(
                    create_summary_layout(layout)))
                
                live.refresh()
                
                c.layout = layout
                time.sleep(.1)
                
    except KeyboardInterrupt:
        print(lang.get('exiting_requested', 'Exiting as requested...') +" Toodles!")
        kb.stop()  # Stop the background thread
        kb.join()  # Wait for the thread to finish     

        uithread.join()
        walletthread.join()
        nodethread.join()
        cleanthread.join()
        socketthread.join()
        utilthread.join()
        index_thread.join()
 
        os._exit(0) 

    kb.stop()
    
    #import sys
    os._exit(0) 

  

if __name__ == "__main__":

    asyncio.run(main())

