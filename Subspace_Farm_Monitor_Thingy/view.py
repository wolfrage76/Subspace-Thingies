import requests
import psutil 

import datetime
from rich import box
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn
from rich.table import Table
import time
import utilities.conf as c
import platform

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
       #Layout(name="msgs",),
    )
    layout["main"].split_row(
        Layout(name="side",),
        Layout(name="body", ratio=2, minimum_size=20, visible=c.show_logging),
    )
    
    
    layout["body"].split_column(
        Layout(name="body1",),
        Layout(name="body2",),
    ),
    
    layout["side"].split(Layout(name="box1")) # ,Layout(name="box2", )
    
    #layout["msgs"].split_row(Layout(name="errors",  ) ,Layout(name="warnings",))
    
    return layout

def make_errors() -> Panel:
    """Some example content."""
    error_event_msg = Table.grid()
    #error_event_msg.add_column(no_wrap=False)
    for log in c.errors:
        if log != '':
            error_event_msg.add_row(log,)

    message_panel = Panel(
        Align.left(error_event_msg, vertical='middle'),
        box=box.ROUNDED,
        title="[b red]Recent ERRORs",
        border_style="red"
    )
    #message_panel.height = 7
    return message_panel

def make_warnings() -> Panel:
    """Some example content."""
    make_warning_logs = Table.grid()
    #make_warning_logs.add_column(no_wrap=False)
    for log in c.warnings:
        if log != '':
            make_warning_logs.add_row(log,)

    message_panel = Panel(
        Align.left(make_warning_logs, vertical='middle'),
        box=box.ROUNDED,
        title="[b dark_orange]Recent WARNING MSGS",
        border_style="yellow",
    )
    message_panel.height = 7
    return message_panel


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
    message.add_column(no_wrap=False)
    message.add_row(log_event_msg)

    message_panel = Panel(
        Align.left(log_event_msg, vertical='middle'),
        box=box.ROUNDED,
        title="[b white]FARMER LOG ENTRIES",
        subtitle="[white]INFO [yellow]WARN [red]ERROR", subtitle_align='right',
        border_style="bright_blue",
    )

    return message_panel


def make_recent_node_logs() -> Panel:
    """Some example content."""
    log_event_msg = Table.grid()
    #sponsor_message.add_column(style="green", justify="right")
    #log_event_msg.add_column(no_wrap=False)
    for log in c.last_node_logs:
        log_event_msg.add_row(
            log,
    )

    message = Table.grid()
    #message.add_column(no_wrap=True)
    message.add_row(log_event_msg)

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
            "Peers: " + c.peers+ '   (' + c.ul + ' | ' + c.dl + ') ', ' ', " Blocks: " + c.best_block + '/#' + c.imported , balance_info + " ",
        )
        return Panel(grid, style="white on blue")


def flip_flop_color(farmer):
    colors = ['[b white]', '[b cyan]']
    return colors[int(farmer) % 2]  # Todo: Set color based on % 

def color_by_status(percent, farm):
    colors = ['[b white]', '[dark_orange]','[b yellow]', '[b green]']
    if c.replotting[farm]:
        return '[blue]'
    elif percent == 100:
        return colors[3]
    elif percent >= 75:
        return colors[2]
    elif percent >= 25:
        return colors[1]
    else:
        return colors[0]
    
def main():
    
    layout = make_layout()
    
    from time import sleep

    from rich.live import Live
    
    with Live(layout, refresh_per_second=4,screen=True):
        while True:
            
            sector = 0
#            sleep(0.4)
            job_progress = Progress(
        "{task.description}",
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[progress.percentage][white]{task.percentage:>3.0f}%")
        
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
                    
                    job_progress.add_task(color_by_status(int(ipds), farm) + farm + ': (' +  ps +') Sector: ' + str(sector) + ' [' + c.deltas[farm] + ']', completed=int(ipds),)
                    overall += int(ipds)
                    
            if job_progress.tasks and len(job_progress.tasks) > 0:                    
                c.total_completed = overall / (len(job_progress.tasks))
            else:
                c.total_completed = 0
            
                        
            progress_table = Table.grid(expand=True)
            
            
            progress2 = Progress(
        "{task.description}",
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[progress.percentage][white]{task.percentage:>3.0f}%")
            )
            if job_progress.tasks and len(job_progress.tasks) > 0:
                progress2.add_task('[white]Overall Progress: ', completed = (overall / (len(job_progress.tasks))))
           # progress_table.add_row(progress2) 
            
            
            footer_txt = Table.grid(expand=True,)
            
            my_system = platform.uname()
            footer_txt.add_row(Align.center(
f"Cores: {psutil.cpu_percent()}%   " + f"RAM: {round(psutil.virtual_memory().total / (1024.0 ** 3))}gb ({psutil.virtual_memory().percent}%)   CPUs: {psutil.cpu_count(logical=False)} ({psutil.cpu_count(logical=True)})  Load: {psutil.getloadavg()[1]}" ,))
            
            layout["header"].update(Header())
            layout["body"].visible = c.show_logging
            layout["body2"].update(make_recent_logs())
            #layout["errors"].update(make_error_logs())
           #layout["warnings"].update(make_warnings())
            layout["body1"].update(make_recent_node_logs())
            
            #layout["errors"].update(make_errors())
            
            progress_table.add_row(Panel(progress2, border_style="green",subtitle='Rewards: ' + str(c.reward_count) ))
                              
            progress_table.add_row(job_progress)            
            
            layout["box1"].update(Panel(progress_table, border_style="green", title ="[blue]Farms" ,subtitle="[b white]< 25% | [b dark_orange]>25% | [yellow]> 75% | [b green]=100% | [blue]Replotting"))
             
            layout["footer"].update(Panel(footer_txt, title="BitcoinBart Was Here", border_style="green", subtitle='[b white]SPACE: Toggle Logs', subtitle_align='left', height=3),)
            
            
           
   
            
