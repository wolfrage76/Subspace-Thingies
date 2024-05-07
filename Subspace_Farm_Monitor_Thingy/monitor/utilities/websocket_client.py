import asyncio
import websockets
import utilities.conf as c
import json
from rich.traceback import install

install(show_locals=True)

class Farmer(object):
    def __init__(self, farmer_name="Unknown", warnings=[], errors=[], startTime='', farm_rewards={}, farm_recent_rewards={}, disk_farms={}, farm_skips={}, farm_recent_skips={}, system_stats={}, farm_metrics={}, prove_method={},drive_directory='',rewards_per_hr={},proves={}, audits={}, l3_concurrency='', l3_farm_sector_time='', dropped_drives=[]):
        
        self.l3_concurrency = l3_concurrency
        self.l3_farm_sector_time = l3_farm_sector_time    
        self.dropped_drives = dropped_drives
        self.system_stats = system_stats
        self.drive_directory = drive_directory
        self.farmer_name = farmer_name
        self.warnings = warnings
        self.errors = errors
        self.startTime = startTime
        self.farm_rewards = farm_rewards
        self.farm_recent_rewards = farm_recent_rewards
        self.disk_farms = disk_farms
        self.farm_skips = farm_skips
        self.farm_recent_skips = farm_recent_skips
        self.farm_metrics = farm_metrics  # Add farm_metrics attribute
        self.prove_method = prove_method
        self.rewards_per_hr = rewards_per_hr
        self.proves = proves
        self.audits = audits
        


def make_farmer():
    frmr = Farmer()
    frmr.l3_concurrency = c.l3_concurrency
    frmr.l3_farm_sector_time = c.l3_farm_sector_time
    frmr.dropped_drives = c.dropped_drives
    frmr.audits = c.audits
    frmr.proves = c.proves
    frmr.rewards_per_hr= c.rewards_per_hr
    frmr.drive_directory = c.drive_directory
    frmr.prove_method = c.prove_method
    frmr.system_stats = c.system_stats
    frmr.disk_farms = c.disk_farms
    frmr.farmer_name = c.farmer_name
    frmr.warnings = c.warnings
    frmr.errors = c.errors
    frmr.startTime = c.startTime
    frmr.farm_rewards = c.farm_rewards
    frmr.farm_recent_rewards = c.farm_recent_rewards
    frmr.farm_skips = c.farm_skips
    frmr.farm_recent_skips = c.farm_recent_skips
    frmr.farm_metrics = c.farm_metrics  # Add farm_metrics to the object
    #frmr.rewards_per_hour = c.rewards_per_hour
    
    return frmr


def serialize_sets(obj):
    if isinstance(obj, set):
        return list(obj)
    return obj


async def ws_client():
    reconnect_delay = 20
   
    if c.connected_farmer:
        url = "ws://" + c.front_end_ip + ":" + c.front_end_port
        try:
            async with websockets.connect(url) as ws:
                frmr = make_farmer()
                frmr_dump = json.dumps(frmr.__dict__, default=serialize_sets)
                await ws.send(frmr_dump)
        except websockets.exceptions.ConnectionClosedOK:
            pass
        except websockets.exceptions.ConnectionClosedError as e:
            print(f'Connection closed: {e}. Retrying in {reconnect_delay} seconds...')
        except Exception as e:
            print(f'Unexpected socket error: {e}. Retrying in {reconnect_delay} seconds...')

    await asyncio.sleep(reconnect_delay)    

def main():
    asyncio.run(ws_client())
