import utilities.menu_keys as menu
import psutil
import asyncio
import sys
import datetime
from rich import box
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import print
import time
import yaml
import utilities.conf as c
import utilities.wallet as wallet
import utilities.farmer_socket as w
import threading
from utilities.menu_keys import KBHit
import utilities.node_monitor as node_monitor
import requests

console = Console()


farmer_uptime = 0

c.startTime = time.time()
with open("config.yaml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

#################

c.node_log_file = config['NODE_LOG_FILE']
c.show_logging = config['SHOW_LOGGING']
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


def wallet_thread():
    wallet.WalletMon()


walletthread = threading.Thread(
    target=wallet_thread, name='Wallet', daemon=True)
if config['WALLET']:
    walletthread.start()


def node_thread():
    node_monitor.main()


nodethread = threading.Thread(target=node_thread, name='Node', daemon=True)

if config['NODE_LOG_FILE']:
    nodethread.start()


def socket_thread():
    # print('Triggering socket thread')
    w.start()


def make_image(layout):
    console2 = Console(record=True)
    # await asyncio.sleep(900)  # 15mins = 900secs
   # while True:
    console2.print(layout, justify="center")
    console2.save_svg("layout.svg", title="FARMS")
    from discord_webhook import DiscordWebhook, DiscordEmbed

    webhook = DiscordWebhook(
        url="https://discord.com/api/webhooks/1199199521981345792/LOlCM6nTtmZTyI6Fnk-O8Hso7KVFG4NXmqXIUfsv8V2dy7au9uFB7SkBCYQfJh5Z_noR")

    with open("layout.svg", "rb") as f:
        webhook.add_file(file=f.read(), filename="layout.svg")

    embed = DiscordEmbed(
        title="FARMS", description="Current Farm Status", color="03b2f8")
    embed.set_thumbnail(url="attachment://layout.svg")

    webhook.add_embed(embed)
    response = webhook.execute()


async def cleanup_stale_farms(timeout=600,):  # 900 seconds = 15 minutes

    while True:
        current_time = time.time()
        stale_farms = [farm for farm, data in c.remote_farms.items(
        ) if current_time - data['last_update'] > timeout]
        for farm in stale_farms:
            del c.remote_farms[farm]
            c.farm_names.remove(farm)
            # send()  #Notify when stale farm is removed

        # Check twice within the timeout period
        await asyncio.sleep(timeout / 2)


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
        Layout(name="body", ratio=2, minimum_size=20, visible=c.show_logging),
    )

    layout["body"].split_column(
        Layout(name="body1",),
        Layout(name="body2",),
    )

    layout["side"].split(Layout(name="box1"))

    return layout


def convert_to_tib(space_str):
    """
    Converts an allocated drive space string to TiB.

    Parameters:
    space_str (str): The space string including units (e.g., "500 GB", "2 TiB").

    Returns:
    float: The allocated space converted to TiB.
    """
    unit_multipliers = {
        'G': 1 / 1024,
        'GB': 1 / 1024,
        'GiB': 1 / (2**10),
        'T': 1 * 0.909495,
        'TB': 1 * 0.909495,
        'TiB': 1,
    }

    # Split the input string into value and unit
    space_value, unit = space_str.split()
    space_value = float(space_value)

    # Identify the unit and convert to TiB
    if unit in unit_multipliers:
        return str(round(space_value * unit_multipliers[unit], 1)) + ' TiB'
    else:
        raise ValueError(f"Unknown unit: {unit}")


async def update_node_logs_every_minute(layout, ):

    while True:
        layout["body"].visible = c.show_logging
        layout["body1"].update(make_recent_node_logs())
        layout["header"].update(Header())
        layout["body2"].update(make_recent_logs())

        footer_txt = Table.grid(expand=True, )

        footer_txt.add_row(Align.center(
            f"CPU: {psutil.cpu_percent()}%   " + f"RAM: {round(psutil.virtual_memory().total / (1024.0 ** 3))}gb ({psutil.virtual_memory(
            ).percent}%)   Cores: {psutil.cpu_count(logical=False)} ({str(psutil.cpu_count(logical=True))})  Load: {psutil.getloadavg()[1]}"
        ))  # Add the CPU, RAM, and Cores to the footer

        layout["footer"].update(Panel(footer_txt, title="BitcoinBart Was Here", border_style="green",
                                      subtitle='[b white]SPACE: Toggle Logs | [b white]Q/ESC: Quit', subtitle_align='left', height=3))

        await asyncio.sleep(.2)  # Wait for 60 seconds before updating again


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


def make_recent_node_logs() -> Panel:
    """Some example content."""
    log_event_msg = Table.grid()
    for log in c.last_node_logs:
        log_event_msg.add_row(log)

    message_panel = Panel(
        Align.left(log_event_msg, vertical='middle'),
        box=box.ROUNDED,
        title="[b white]Node LOG ENTRIES",
        subtitle="[white]INFO [yellow]WARN [red]ERROR", subtitle_align='left',
        border_style="bright_blue",
    )

    return message_panel


class Header:

    def __rich__(self) -> Panel:
        if c.wallet:
            balance_info = str(c.balance)
        else:
            balance_info = ""

        grid = Table.grid(expand=True)
        grid.add_column(justify="left")
        grid.add_column(justify="center")
        grid.add_column(justify="center")
        grid.add_column(justify="center")
        grid.add_column(justify="right")
        grid.add_row('Up: ' + getUptime(),
                     "Peers: " + c.peers +
                     '   (' + c.ul + ' | ' + c.dl + ') ', ' ',
                     " Blocks: " + c.best_block + '/#' + c.imported, balance_info + " ",
                     )
        return Panel(grid, style="white on blue")


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
    def __init__(self, farmer_name="Unknown", replotting={}, warnings=[], errors=[], curr_sector_disk={}, plot_space={}, farm_plot_size={}, deltas={}, total_completed=0, startTime='', farm_rewards={}, disk_farms={}):
        print(farmer_name)

        self.farmer_name = farmer_name
        self.replotting = replotting
        self.warnings = warnings
        self.errors = errors
        self.curr_sector_disk = curr_sector_disk
        self.plot_space = plot_space
        self.farm_plot_size = farm_plot_size
        self.deltas = deltas
        self.total_completed = total_completed
        self.startTime = startTime
        self.farm_rewards = farm_rewards
        self.disk_farms = disk_farms


def make_farmer(farmer_name="Unknown", replotting={}, warnings=[], errors=[], curr_sector_disk={}, plot_space={}, farm_plot_size={}, deltas={}, total_completed=0, startTime='', farm_rewards={}):

    frmr = Farmer()

    frmr.farmer_name = farmer_name
    frmr.replotting = replotting
    frmr.warnings = warnings
    frmr.errors = errors
    frmr.curr_sector_disk = curr_sector_disk
    frmr.plot_space = plot_space
    frmr.farm_plot_size = farm_plot_size
    frmr.deltas = deltas
    frmr.total_completed = total_completed
    frmr.startTime = startTime
    frmr.farm_rewards = farm_rewards

    return frmr


# Creating WebSocket server

def start():
    asyncio.run(main())


def make_waiting_message() -> Panel:
    """Create a 'Waiting for data' message."""
    return Panel("Waiting for data...", style="yellow")


socketthread = threading.Thread(
    target=socket_thread, name='Socket', daemon=True)
socketthread.start()


def menu_thread():
    menu.main()


menuthread = threading.Thread(target=menu_thread, name='Menu', daemon=True)
# menuthread.start()


def flip_flop_color(farmer):
    colors = ['[grey78]', '[b white]']
    return colors[int(farmer) % 2]  # Todo: Set color based on %


def color_by_status(percent, replot):
    colors = ['[b white]', '[dark_orange]',
              '[b yellow]', '[b green]', '[dodger_blue2]']
    if replot:
        return colors[4]
    elif percent == 100:
        return colors[3]
    elif percent >= 75:
        return colors[2]
    elif percent >= 25:
        return colors[1]
    else:
        return colors[0]


def generate_farms_and_drives_grid():
    # console = Console()
    table = Table(show_header=True, header_style="bold magenta", )

    # Define the headers for both farmer and drive data
    table.add_column("Farms",  width=20)
    table.add_column("Rewards", justify="right")
    table.add_column("Plot Space", justify="right")
    table.add_column("% Completed", justify="right")

    # Iterate over all connected farms
    for farmer_name, farmer_data in c.remote_farms.items():
        # Add farmer data
        table.add_row('[black]' + farmer_name,
                      str(farmer_data.get('total_rewards', 'N/A')),
                      str(farmer_data.get('total_plot_size', 'N/A')),
                      f"{farmer_data.get('overall_completion', 0)}%", style='on green'
                      # Include additional farmer data as needed
                      )

        # Iterate over drives for the current farm
        for drive in sorted(farmer_data['data']['disk_farms'], key=int):
            table.add_row(f"{flip_flop_color(drive)}Drive {drive}:",
                          "",  # Rewards are typically not listed per drive in the provided structure
                          str(farmer_data['data']['plot_space'][drive]),
                          f"{farmer_data['data']['farm_plot_size'][drive]}%",
                          # Include additional drive data as needed
                          )
        table.add_row("", "", "", "")

    # Print the table
    print(table)
    return table


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
    layout["body"].visible = c.show_logging
    layout["body2"].update(make_recent_logs())
    layout["body1"].update(make_recent_node_logs())
    layout["box1"].update(Panel("", border_style="green", title="[yellow]Waiting for Farmers...",
                                subtitle="[b white]< 25% | [b dark_orange]>25% | [yellow]> 75% | [b green]=100% | [blue1]Replotting"))
    footer_txt = Table.grid(expand=True)
    footer_txt.add_row(Align.center(
        f"CPU: {psutil.cpu_percent()}%   " + f"RAM: {round(psutil.virtual_memory().total / (1024.0 ** 3))}gb ({psutil.virtual_memory(
        ).percent}%)   Cores: {psutil.cpu_count(logical=False)} ({str(psutil.cpu_count(logical=True))})  Load: {psutil.getloadavg()[1]}",
    ))

    layout["footer"].update(Panel(footer_txt, title="BitcoinBart Was Here", border_style="green",
                                  subtitle='[b white]SPACE: Toggle Logs | [b white]Q/ESC: Quit', subtitle_align='left', height=3))

    return layout


async def main():
    cleanup_task = asyncio.create_task(
        cleanup_stale_farms(600))  # Start the cleanup task

    layout = build_ui()  # Build and retrieve the UI layout
    layout["main"].update(make_waiting_message())
    # c.layout = layout
    update_logs_task = asyncio.create_task(
        update_node_logs_every_minute(layout))

    # image_create = asyncio.create_task(make_image())

    # menu_keys.KeyboardThread.run()
    try:

        kb = KBHit(lambda: layout.update(layout))
        kb.start()  # Start the background thread for keypress detection

        from rich.live import Live

        with Live(layout, refresh_per_second=10, screen=True) as live:

            farmer_name = ""  # Initialize farmer_name

            while True:
                layout["body1"].update(make_recent_node_logs())

                if not c.running:
                    print('Toodles!')
                    quit()
                # Initialize to an empty list if not already set
                c.farm_names = c.farm_names or []
                # Initialize to an empty dictionary if not already set
                c.remote_farms = c.remote_farms or {}
                for farmer_index in range(len(c.farm_names)):
                    try:
                        farmer_name = c.farm_names[farmer_index % len(
                            c.farm_names)]
                        farm_info = c.remote_farms.get(farmer_name, {})

                        # Access the 'data' key for the actual farm data
                        farmer_data = farm_info.get('data', {})

                        if not farmer_data:  # Check if farmer_data is empty
                            continue

                        c.warnings = farmer_data.get('warnings', [])
                        c.errors = farmer_data.get('errors', [])

                        overall = 0
                        job_progress = Progress(
                            "{task.description}",
                            SpinnerColumn(),
                            BarColumn(),
                            TextColumn(
                                "[progress.percentage][white]{task.percentage:>3.0f}%")
                        )

                        for farm in sorted(farmer_data.get("disk_farms", []), key=int):
                            psd = "{:.2f}".format(
                                float(farmer_data.get("farm_plot_size", {}).get(farm, 0)))
                            sector = farmer_data.get(
                                "curr_sector_disk", {}).get(farm, 0)
                            ipds = round(float(psd))
                            ps = farmer_data.get(
                                "plot_space", {}).get(farm, '----')
                            # sector = farmer_data.get("curr_sector_disk", {}).get(farm, 0)

                            replots = farmer_data.get("replotting", {})
                            if farm in replots:
                                replot = True
                            else:
                                replot = False

                            color = color_by_status(int(ipds), replot)

                            job_progress.add_task(color + farm + ': (' + convert_to_tib(ps) + ') Sector: ' + str(sector) + ' [' + farmer_data.get("deltas", {}).get(farm, '00:00') + ']',
                                                  completed=int(ipds))
                            overall += int(ipds)

                        if job_progress.tasks and len(job_progress.tasks) > 0:
                            c.total_completed = overall / \
                                (len(job_progress.tasks))
                        else:
                            c.total_completed = 0

                        progress_table = Table.grid(expand=True)

                        progress2 = Progress(
                            "{task.description}",
                            SpinnerColumn(),
                            BarColumn(),
                            TextColumn(
                                "[progress.percentage][white]{task.percentage:>3.0f}%")
                        )
                        if job_progress.tasks and len(job_progress.tasks) > 0:
                            progress2.add_task('[white]Overall Progress: ', completed=(
                                overall / (len(job_progress.tasks))))

                        total = 0
                        for key in c.farm_rewards[farmer_name].keys():
                            total = total + c.farm_rewards[farmer_name][key]

                        progress_table.add_column()
                        progress_table.add_row(Panel(
                            progress2, border_style="green", subtitle='Rewards: ' + str(total)))

                        progress_table.add_row(job_progress, )

                        layout["box1"].update(Panel(progress_table, border_style="green", title="[yellow]Farmer: " + farmer_name + " [Up: " + getUptime(farmer_data['startTime']) + "] ",
                                                    subtitle="[b white]< 25% | [b dark_orange]>25% | [yellow]> 75% | [b green]=100% | [blue1]Replotting"))

                       # make_image(layout)
                        c.layout = layout
                        # Pause for 5 seconds before processing the next farm
#                        generate_farms_and_drives_grid()
                        await asyncio.sleep(5)

                    except Exception as e:
                        console.print(f"An error occurred: {e}")
                        # Add any additional error handling code here

    except KeyboardInterrupt:
        print("Exiting as requested. Toodles!")
        sys.exit()
    finally:
        kb.stop()  # Stop the background thread
        kb.join()  # Wait for the thread to finish

if __name__ == "__main__":

    asyncio.run(main())
    kb = KBHit()
    kb.start()
