
import psutil
import asyncio
import datetime
from rich import box, print
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.progress_bar import ProgressBar
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
with open("config.yaml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

#################

c.show_logging = not config['SHOW_LOGGING']
c.hour_24 = config['HOUR_24']
c.ui_port = config['FRONT_END_PORT']
c.toggle_encoding = config['TOGGLE_ENCODING']
c.wallet = config['WALLET']

c.running = True


def getVer():  # gonna hijack this for the loop.  Will change later
    # URL to the GitHub API for the latest release of the subspace repository
    url = "https://api.github.com/repos/subspace/subspace/releases/latest"

    # Make a GET request to the GitHub API
    response = requests.get(url)
    data = response.json()

    # Extract the tag name (version) of the latest release
    c.latest_version = data['tag_name']


getVer()


def clean_thread():
    asyncio.run(cleanup_stale_farms(100))
    
def utility_thread():
    asyncio.run(utility_run(600))

async def utility_run(timeout=900,):  # 900 seconds = 15 minutes
    #export_console_to_png(c.layout['sum1'])
    while c.running & config['USE_BANNERS']:
      try:  
        url = 'https://subspacethingy.ifhya.com/announcement'
        response = requests.get(url)
        data = response.json()
        c.banners = data.get('text',"Check out the community tools at: http://subspace.ifhya.com")
      
      except Exception as e:
          pass
      await asyncio.sleep(timeout)
def wallet_thread():
    wallet.WalletMon()


def ui_thread():
    while c.running:
        create_main_layout()


uithread = threading.Thread(
    target=ui_thread, name='UI', daemon=True)

walletthread = threading.Thread(
    target=wallet_thread, name='Wallet', daemon=True)


def node_thread():
    #node_monitor.main()
    asyncio.run(node_monitor.fetch_node_info())


nodethread = threading.Thread(target=node_thread, name='Node', daemon=True)


async def cleanup_stale_farms(timeout=600,):  # 900 seconds = 15 minutes

    while c.running:
        current_time = time.time()
        removed = str()
        stale_farms = [farm for farm, data in c.remote_farms.items(
        ) if current_time - data['last_update'] > timeout]
        for farm in stale_farms:
            if not c.running:
                break
            removed += ' ' + farm
            del c.remote_farms[farm]
            c.farm_names.remove(farm)
            # send()  #Notify when stale farm is removed
            if removed:
                send("Farm(s) Removed due to inactivity:" + removed)
        # Check twice within the timeout period
        await asyncio.sleep(timeout / 2)


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


def create_progress_bar1(completed: float, width: int) -> Progress:
    color = color_by_status(completed)
    progress = Progress(
        TextColumn(" [progress.percentage]" + color +
                   "{task.percentage:>3.1f}%"),
        SpinnerColumn(),
        BarColumn(),
        # TextColumn("[bold green]{task.completed}/{task.total}"),
        # TextColumn("ETA: {task.fields[eta]}"),
        # expand=True
    )

    task_id = progress.add_task(
        description="",  completed=completed)

    return progress


def create_progress_bar(progress: float, width: int = 10) -> ProgressBar:
    progress_bar = ProgressBar(total=100, width=width, )
    progress_bar.completed = progress
    return progress_bar


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
    if space_str == '----':
        return '0'
    space_value, unit = space_str.split()
    space_value = (float(space_value) )  # Edited to proper size

    # Identify the unit and convert to TiB
    if unit in unit_multipliers:
        return str(round(((space_value * (100/(100 - config.get('CACHE_SIZE', 1)))) * unit_multipliers[unit]) * 0.9843111634, 2) )
    else:
        return 0  # If the unit is unknown, return the original string

def create_footer(layout):
    footer_txt = Table.grid(expand=True, )
    footer_txt.add_column(ratio=1)
    footer_txt.add_column(ratio=5,)
    footer_txt.add_column(ratio=1,)

    footer_txt.add_row(Align.left('Latest: ' + c.latest_version + ' '), Align.center(c.banners))
    
    footer = Panel(footer_txt, title="[b white]- [bold]BitcoinBart Was Here -", border_style="blue",
                   subtitle='[b white][[yellow]1[b white]|[yellow]2[b white]|[yellow]3[b white]]: Change Display  [b white][[yellow]Q[b white]]uit', subtitle_align='right',height=3)
 
    return footer


def make_recent_logs() -> Panel:
    """Some example content."""
    log_event_msg = Table.grid()
    for log in c.errors:
        log_event_msg.add_row(log)

    message_panel = Panel(
        Align.left(log_event_msg, vertical='middle'),
        box=box.ROUNDED,
        title="[b white]FARMER RECENT ERRORS",
        subtitle="[white]INFO [yellow]WARN [red]ERROR", subtitle_align='right',
        border_style="bright_blue",
    )

    return message_panel

class Header:
    peers = str(c.peers)
    def __rich__(self) -> Panel:
        if c.wallet:
            balance_info = str(c.balance)
        else:
            balance_info = " "
        peers  = c.peers or 0
        peercnt = ''
        if peers >= 40:
            peercnt = '[green]' + str(peers) + '[b white]'
        elif peers  >= 30:
            peercnt = '[yellow]' + str(peers) + '[b white]'
        elif peers  >= 15:
            peercnt = '[orange3]' + str(peers) + '[b white]'
        else:
            peercnt = '[blink red]' + str(peers) + '[b white]'
        
        ul = c.ul  or '0'
        dl = c.dl or '0'
        
        grid = Table.grid(expand=True)
        grid.add_column(justify="left")
        grid.add_column(justify="center")
        grid.add_column(justify="center")
        grid.add_column(justify="center")
        grid.add_column(justify="right")
       
        peerCount = "Peers: " + peercnt
        
        ulDl = '' #f'   ({ul}kb/s |  {dl}kb/s) '
        if not c.is_syncing:
            sync = '[[green]Synced[b white]] - '
        else: 
            sync = '[red]Not Synced - '
        blocks = sync + f'Block: #{c.best_block}'
            
        grid.add_row('Up: ' + getUptime(),
                     peerCount + ulDl
                     , ' ', blocks, balance_info + " ",
                     )
        return Panel(grid, style="white on blue3")


def getUptime(started=None):
    """
    Returns the number of seconds since the program started.
    """
    if started:
        sec = time.time() - started
    else:
        sec = time.time() - c.startTime

    return str(datetime.timedelta(seconds=sec)).split('.')[0]


class Farmer(object):
    def __init__(self, farmer_name="Unknown", replotting=None, warnings=None, errors=None, startTime='', farm_rewards=None, disk_farms=None, ):
        if errors is None:
            errors = []
        if disk_farms is None:
            disk_farms = {}
        if farm_rewards is None:
            farm_rewards = {}
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
        self.disk_farms = disk_farms


def make_farmer(farmer_name="Unknown", replotting={}, warnings=[], errors=[],  startTime='', farm_rewards={}, ):

    frmr = Farmer()
    frmr.farmer_name = farmer_name
    frmr.replotting = replotting
    frmr.warnings = warnings
    frmr.errors = errors
    frmr.startTime = startTime
    frmr.farm_rewards = farm_rewards

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

def color_by_status(percent, replot=False):
    colors = ['[b white]', '[dark_orange]',
              '[yellow]', '[green]', '[b blue]', '[b yellow]', '[orange1]', '[white]']
    if replot:
        return colors[4]
    elif percent == 100:
        return colors[3]
    elif percent >= 90:
        return colors[5]
    elif percent >= 75:
        return colors[2]
    elif percent >= 50:
        return colors[6]
    elif percent >= 35:
        return colors[7]
    elif percent >= 25:
        return colors[1]
    else:
        return colors[0]


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
    layout["box1"].update(Panel("", border_style="blue", title="[yellow]Waiting for Farmers...",
                                subtitle="[b white]<25% | [b dark_orange]>25% | [yellow]>75% | [b green]100% | [b blue]Replotting"))
    layout["bodysum"].visible = (c.view_state == 1 or c.view_state == 3)
    layout["sum1"].update(Panel("", border_style="blue", title="[yellow]Waiting for Farmers...",
                                subtitle="[b white]<25% | [b dark_orange]>25% | [yellow]>75% | [b green]100%"))
    footer_txt = Table.grid(expand=True)
    footer_txt.add_row(Align.left('Latest: ' + c.latest_version + ' '),  Align.center(c.banners))  

    layout["footer"].update(create_footer(layout))

    return layout


def format_time(minutes, seconds):
    return f"{str(minutes).zfill(2)}:{str(seconds).zfill(2)}"

def calculate_average_plotting_time_for_farmer(farmer_metrics):
    total_plotting_time = 0
    total_sector_count = 0

    for disk_metrics in farmer_metrics.values():
        plotting_time_sum = float(disk_metrics.get('subspace_farmer_sector_plotting_time_seconds_sum', {}).get('value', 0))
        sector_count = float(disk_metrics.get('subspace_farmer_sector_plotting_time_seconds_count', {}).get('value', 0))

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
    while c.running:
        progress_table2 = Table.grid(expand=True)
        progress_table2.add_column(width=8)
        c.sum_size = {}
        c.sum_plotted = {}
        
        for farmer_index in range(len(c.farm_names)):
            drive_count = 0
            calc_avg = 0.0
            
            is_completed = []
            is_replotting = []
            #disk_id = None
            farm_plotted = 0.0  # Initialize farm_plotted here
            farm_notplotted = 0.0  # Initialize farm_notplotted here
            total_sectors = defaultdict(float)  # Initialize total_sectors here
            try:
                progress_items = Table.grid(expand=False)
                progress_items.add_column(width=11)
                progress_items.add_column(width=15)
                progress_items.add_column(width=12)
                farmer_name = c.farm_names[farmer_index % len(c.farm_names)]
                farm_info = c.remote_farms.get(farmer_name, {})

                farmer_data = farm_info.get('data', {})
                if not farmer_data:
                    continue

                c.warnings = farmer_data.get('warnings', [])
                c.errors = farmer_data.get('errors', [])

                #total_completed = c.psTotal / c.psdTotal
                farm_plotted = 0.0
                total_sectors = defaultdict(float)
                farm_notplotted = 0.0
                #and total_sectors.get('NotPlotted', 0) == 0
                for disk in farmer_data.get("disk_farms", []):
                    #farm_notplotted = 0
                    
                    total_sectors['Expired'] = 0
                    total_sectors['NotPlotted'] = 0
                    total_sectors['Plotted'] = 0
                    
                    disk_metrics = farmer_data.get('farm_metrics', {}).get(disk, {})
                    
                    for state in ["Plotted", "Expired", "AboutToExpire", "NotPlotted"]:
                        key = f"subspace_farmer_sectors_total_sectors_{state}"
                        total_sectors[state] += float(disk_metrics.get(key, {}).get('value', 0))
                    
                    if total_sectors.get('NotPlotted',0) == 0 or total_sectors.get('Expired', 0) > 0:
                        is_completed.append(disk)
                    
                    if total_sectors.get('Expired', 0) > 0:
                        #replotting_count += 1
                        is_replotting.append(disk)
                    farm_plotted += total_sectors.get('Plotted',0)
                    farm_notplotted += total_sectors.get('NotPlotted',0)

                total = sum(farmer_data.get('farm_rewards', {}).values())
                skips = sum(farmer_data.get('farm_skips').values())
                drive_count += len(farmer_data.get("disk_farms", []))
                nocount = (drive_count - len(is_completed))
                if nocount <=0:
                    calc_avg = 0
                else:
                    calced = calculate_average_plotting_time_for_farmer(farmer_data.get('farm_metrics', {}))
                    calc_avg = calced / nocount
                
                if farm_notplotted != 0 and farmer_data.get('farm_metrics') and calc_avg > 0:
                    sec_hr = 3600 / calc_avg
                    eta = (farm_notplotted) / sec_hr
                else:
                    sec_hr = 0
                    eta = 0

                if farm_notplotted + farm_plotted == 0:
                    sumipds = 0
                else:
                    sumipds = farm_plotted / (farm_notplotted + farm_plotted) * 100

            
                color = color_by_status(sumipds)
                progress_items.add_row(color + str(drive_count).rjust(3) + 'x Plots ', color + convert_to_tib(str(round(farm_plotted, 2)) + ' GB').rjust(5) + '/' + convert_to_tib(str(round(farm_notplotted + farm_plotted, 2) ) + ' GB') + ' TiB ', create_progress_bar1(sumipds, 12),  color + ' ETA: ' + hours_to_dh_m(eta))

                progress_table2.add_row(Panel(
                    progress_items, title_align='left', title="[yellow]Farmer: " + farmer_name, border_style="blue", subtitle_align='right', subtitle='[yellow]H/M: [green]' + str(total) + '[white]/[b red]' + str(skips) + ' [white]Avg Sector: ' + seconds_to_mm_ss(calc_avg) + ' ' + ' Sectors/hr: ' + str(round(sec_hr, 2)),))

            except Exception as e:
                console.print(f"An error occurred: {e}")
                console.print_exception()
        #layout["sum1"].visible = (c.view_state == 1 or c.view_state ==3)
        layout["sum1"].update(Panel(progress_table2, border_style="blue", title="[yellow] " + str(len(c.remote_farms)) +
                                " Farmers", subtitle="[b white]<25% | [b dark_orange]>25% | [yellow]>75% | [b green]100%"))
        return layout

""" def export_console_to_png(content, filename='console_output.png', width=80):
    # Create a separate console instance for rendering the content
    export_console = Console(record=True, width=width)
    content = c.layout['sum1']
    export_console.print(content)

    # Export console output to SVG
    svg_data = export_console.export_svg(title='Farm Report,')
    with open('temp.svg', 'w') as svg_file:
        svg_file.write(svg_data)

    # Convert SVG to PNG using cairosvg
    cairosvg.svg2png(url='temp.svg', write_to=filename)
    requests.post(config['DISCORD_WEBHOOK'], files={"file": open(filename, "rb")})
    # Clean up temporary SVG file
    
    os.remove('temp.svg')
"""
    

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

    
    for farmer_index in range(len(c.farm_names)):
        try:
            farmer_name = c.farm_names[farmer_index % len(c.farm_names)]
            farm_info = c.remote_farms.get(farmer_name, {})
            farmer_data = farm_info.get('data', {})
            

            if not farmer_data:
                continue

            c.warnings = farmer_data.get('warnings', [])
            c.errors = farmer_data.get('errors', [])


            job_progress = Progress("{task.description}",
                                    SpinnerColumn(),
                                    TextColumn(
                                        "[progress.percentage][white]{task.percentage:>3.1f}%"),
                                    BarColumn(bar_width=8),

                                    )
            if farmer_data.get('farm_rewards', {}).values():
                total = sum(farmer_data.get('farm_rewards', []).values()) # total = sum(c.farm_rewards[farmer_name].values())
            else:
                total = 0
            if farmer_data.get('farm_skips', {}).values():
                total = sum(farmer_data.get('farm_skips', {}).values()) # total = sum(c.farm_rewards[farmer_name].values())
            else:
                total = 0
            skips = sum(farmer_data.get('farm_skips',{}).values())
            
            ipds = 0.0
            psd = 0.0
            remspace = 0.0
            sector = 0
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
                                    
                if farmer_data.get('farm_metrics', {}).get(farm, {}).get('subspace_farmer_sectors_total_sectors_Plotted'):
                    
                    psd = float(farmer_data.get('farm_metrics', {}).get(farm, {}).get('subspace_farmer_sectors_total_sectors_Plotted').get('value', 0))
                else: psd = 0
                
                if farmer_data.get('farm_metrics', {}).get(farm, {}).get('subspace_farmer_sectors_total_sectors_NotPlotted'):
                     remspace = float(farmer_data['farm_metrics'][farm]['subspace_farmer_sectors_total_sectors_NotPlotted'].get('value', 0))
                else:
                    remspace = 0
                
                ps = remspace + psd
                c.psTotal += ps
                c.psdTotal += psd
                c.remTotal += remspace
                
                
                if psd == 0 or ps == 0:
                    ipds = 0
                else:
                    ipds = (psd / ps) * 100
                if farmer_data.get('farm_metrics', {}).get(farm):
                    sector = farmer_data.get('farm_metrics', {}).get(farm).get('subspace_farmer_sectors_total_sectors_Plotted', 0).get('value',0)
                else: 
                    sector = 0
               # replots = farmer_data.get("replotting", {})
                
               # if farm in replots:
               #     replot = True
               # else:
               #     replot = False

                #color = color_by_status(int(ipds), replot)
                c.farm_rewards[farmer_name][farm] = c.farm_rewards.get(farmer_name, {}).get(farm, 0)
                
                if farmer_data.get('farm_metrics', {}).get(farm):
                    summedPlotting = float(farmer_data['farm_metrics'].get(farm).get('subspace_farmer_sector_plotting_time_seconds_sum', {}).get('value','0')) 
                else:
                    summedPlotting = 0
                plottingCount = farmer_data.get('farm_metrics', {}).get(farm,{}).get('subspace_farmer_sector_plotting_time_seconds_count',{}).get('value', 0.0)
               
                
                if not plottingCount or plottingCount == 0:
                    averageTime = "00:00".ljust(5)
                else:
                    averageTime = seconds_to_mm_ss(summedPlotting / float(plottingCount))   # str(c.avgtime.get(farmer_name, {}).get(farm, '00:00'))

                disk_metrics = farmer_data.get('farm_metrics', {}).get(farm, {})
                
                for state in ["Plotted", "Expired", "AboutToExpire", "NotPlotted"]:
                    key = f"subspace_farmer_sectors_total_sectors_{state}"
                    total_sectors[state] += float(disk_metrics.get(key, {}).get('value', 0))
                
                if total_sectors.get('NotPlotted',0) == 0 or total_sectors.get('Expired', 0) > 0: #  or total_sectors.get('Expired', 0) > 0:
                    is_completed.append(farm)
                
                if total_sectors.get('Expired', 0) > 0:
                    #replotting_count += 1
                    is_replotting.append(farm)
                
                #replot = False
                if farm in is_completed and farm not in is_replotting:
                    ipds = 100
                    averageTime = "--:--"
                    sector = 0
                
              #  elif farm in is_replotting:
                    #ipds = 100
                    #averageTime = "--:--"
                   # replot = True
                
                prove = ''
                color = color_by_status(int(ipds), farm in is_replotting)
                if farmer_data.get('prove_method', {}).get(farm, 'Unknown') == 'WS':
                    prove = '  [b yellow][[blink][b dark_orange]WS[/blink][b yellow]] '
                if farmer_data.get('prove_method', {}).get(farm, 'Unknown') == 'CC':
                    pass  #prove = '  [b yellow][[green]CC[b yellow]]'
                farmid = farm
                farmid = c.drive_directory.get(farmer_name, {}).get(farm, '')
                if farmid == '':
                    continue
                
                if c.view_xtras:
                    sectortxt = ' #' + str(sector).ljust(5)
                else:
                    sectortxt = ''
                    averageTime = ''
                    
                 
                job_progress.add_task(prove + color + (farm + ':').ljust(3) + ' ' + farmid.ljust(get_max_directory_length(farmer_name)) +  (' (' + convert_to_tib(str(psd) + ' GiB') + '/' + convert_to_tib(str(ps) + ' GiB') + ' TiB) ').ljust(18) + sectortxt + ' ' + averageTime + ' ' + 'H/M: [green]' + str(c.farm_rewards.get(farmer_name, {}).get(farm, 0)) + '[yellow]/[red]' + str(c.farm_skips.get(farmer_name, {}).get(farm, 0)), completed=round(ipds, 1), )

            if ipds > 0:
                total_completed = ipds
            else:
                total_completed = 0
            c.total_completed = total_completed

            progress_table = Table.grid(expand=True)

            
            progress2 = Progress(
                "{task.description}",
                SpinnerColumn(),
                TextColumn(
                    "[progress.percentage][white]{task.percentage:>3.1f}%"),
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

            progress_table.add_column(min_width=25)
           # progress_items = Table.grid(expand=False, )
            # progress_items.add_column(width=15)

            # progress_items.add_row(farmer_name + ': ', str(round(total_completed)).rjust(3) + '%  ',
            #  create_progress_bar(total_completed, 10), ' stuff')

            tmp = Table.grid()
            tmp.add_column(width=20)
            tmp.add_column()
            tmp.add_row(progress2, f" CPU: {farmer_data.get('system_stats').get('cpu')}%" +
                        f"  RAM: {farmer_data.get('system_stats').get('ram')}" + f"  Load: {farmer_data.get('system_stats').get('load', 0.0)}"
                        )

            progress_table.add_row(Panel(
                tmp, border_style="blue", subtitle_align='right' , subtitle='[yellow]Rewards: [green]' + str(total) + '[yellow]/[red]' + str(skips),))

            #progress_table.add_row("                 Size            Sector Time   Reward/Miss   Plotted",
           #                        style="dim white")

            progress_table.add_row(job_progress, )

            layout["box1"].update(Panel(progress_table, border_style="blue", title="[yellow]Farmer: " + farmer_name + " [Up: " + getUptime(farmer_data['startTime']) + "] ",
                                        subtitle="[b white]<25% | [b dark_orange]>25% | [yellow]>75% | [b green]100% | [b blue]Replotting"))
            
            c.sum_plotted = sum_plotted
            c.sum_size = sum_size
            
            # render_layout_as_svg(layout)
            time.sleep(5)
            #export_console_to_png(layout, console, 'console_output.png')
        except Exception as e:
            console.print_exception()
            console.print(f"An error occurred: {e}")
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
    """ cleanup_task = asyncio.create_task(
        # Start the cleanup task
        cleanup_stale_farms(600), name='cleanup_stale_farms') """

    layout = build_ui()  # Build and retrieve the UI layout
    layout["main"].update(make_waiting_message())
    c.layout = layout

    if config['WALLET']:
        walletthread.start()
    
    nodethread.start()
    socketthread.start()
    uithread.start()

    cleanthread.start()
    utilthread.start()
    
    kb = KBHit(lambda: layout.update(layout), create_main_layout)
    kb.start()
    
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
#                export_console_to_png(layout['sum1'], 'console_output.png')
    except KeyboardInterrupt:
        print("Exiting as requested. Toodles!")
        kb.stop()  # Stop the background thread
        kb.join()  # Wait for the thread to finish     

        uithread.join()
        walletthread.join()
        nodethread.join()
        cleanthread.join()
        socketthread.join()
        utilthread.join()

        os._exit(0) 

    kb.stop()
    
    #import sys
    os._exit(0) 

  

if __name__ == "__main__":

    asyncio.run(main())
