import requests

import datetime
from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
#from rich.syntax import Syntax
from rich.table import Table
import time
import conf as c

console = Console()

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
wallet = c.wallet
balance = c.balance

def getUptime():
    """
    Returns the number of seconds since the program started.
    """
    sec = time.time() - c.startTime
    
    
    return 'Uptime: ' + str(datetime.timedelta(seconds=sec)).split('.')[0]

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
        Layout(name="body", ratio=2, minimum_size=20),
    )
    layout["side"].split(Layout(name="box2", minimum_size=10))
    return layout


def make_recent_logs() -> Panel:
    """Some example content."""
    log_event_msg = Table.grid()
    #sponsor_message.add_column(style="green", justify="right")
    log_event_msg.add_column(no_wrap=False)
    for log in c.last_logs:
        log_event_msg.add_row(
            log,
    )

    message = Table.grid()
    message.add_column(no_wrap=True)
    message.add_row(log_event_msg)

    message_panel = Panel(
        Align.left(
            Group("\n", Align.left(log_event_msg)),
        ),
        box=box.ROUNDED,
        title="[b white]FARMER LOG ENTRIES",
        subtitle="[white]INFO [yellow]WARN [red]ERROR",
        border_style="bright_blue",
    )
    return message_panel


class Header:
   
    def __rich__(self) -> Panel:
    
        if c.wallet:
            balance_info = c.balance + ' tSSC'
        else:
            balance_info = ""
        
        grid = Table.grid(expand=True)
        grid.add_column(justify="left")
        grid.add_column(justify="center")
        grid.add_column(justify="center")
        grid.add_column(justify="center")
        grid.add_column(justify="right")
        grid.add_row(getUptime(),
            "Peers: " + c.peers+ ' (' + c.ul + ' | ' + c.dl + ') ', 'Overall Plotting: ' + str(round(c.total_completed,2)) + '%' , " Best Block: " + c.best_block + '    Imported: #' + c.imported ,
            '' + balance_info,
        )
        return Panel(grid, style="white on blue")


def flip_flop_color(farmer):
    colors = ['[b white]', '[b cyan]']
    return colors[int(farmer) % 2]  # Todo: Set color based on % 

def color_by_status(percent):
    colors = ['[b white]', '[b yellow]', '[b green]']
    if percent > 74:
        return colors[2]
    elif percent > 25:
        return colors[1]
    else:
        return colors[0]
    
def main():
    
    layout = make_layout()
    from time import sleep

    from rich.live import Live
    
    with Live(layout, refresh_per_second=10):
        while True:
            sector = 0
            sleep(0.1)
            job_progress = Progress(
        "{task.description}",
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        
    )
            overall = 0
            for farm in sorted(disk_farms, key=int):
                    psd = "{:.2f}".format(float(farm_plot_size[farm]))
                    sector = curr_sector_disk[farm]
                    ipds = round(float(psd))
                    if farm in c.plot_space:
                        ps = c.plot_space[farm]
                    else:
                        ps = '----'
                        
                    job_progress.add_task(color_by_status(int(ipds)) + farm + ' (' +  ps +') Sector: ' + str(sector), completed=int(ipds))
                    overall += int(ipds)
                    
            if job_progress.tasks and len(job_progress.tasks) > 0:                    
                c.total_completed = overall / (len(job_progress.tasks))
            else:
                c.total_completed = 0
            
                        
            progress_table = Table.grid(expand=True)
          
            """ progress_table.add_row(
                Panel(job_progress, title="[blue]Farms: [b white] < 25% [b yellow] >25% [b green] > 75%", subtitle='Total Rewards: ' + str(c.reward_count), border_style="red", padding=(1, 2)),
                
            ) """
            footer_txt = Table.grid(expand=True)
            footer_txt.add_column(justify="center")

            footer_txt.add_row('','This is a test of some text!','',)
            
            layout["header"].update(Header())
            layout["body"].update(make_recent_logs())
            layout["box2"].update(Panel(job_progress, title="[blue]Farms  [b white] < 25% [b yellow] >25% [b green] > 75%", subtitle='Rewards: ' + str(c.reward_count), border_style="green", padding=(1, 2)))
            #layout["box1"].update(Panel(layout.tree, border_style="red"))
             
            layout["footer"].update(Align.center("BitcoinBart was here"))
            
