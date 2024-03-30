import asyncio
import websockets
import utilities.conf as c
import json
from rich.traceback import install

install(show_locals=True)

class Farmer(object):
    def __init__(self, farmer_name="Unknown", replotting={}, warnings=[], errors=[], startTime='', farm_rewards={}, disk_farms={}, farm_skips={},  system_stats={}, farm_metrics={}, prove_method={},drive_directory=''):
        self.system_stats = system_stats
        self.drive_directory = drive_directory
        self.farmer_name = farmer_name
        self.replotting = replotting
        self.warnings = warnings
        self.errors = errors
        self.startTime = startTime
        self.farm_rewards = farm_rewards
        self.disk_farms = disk_farms
        self.farm_skips = farm_skips
        self.farm_metrics = farm_metrics  # Add farm_metrics attribute
        self.prove_method = prove_method


def make_farmer():
    frmr = Farmer()
    frmr.drive_directory = c.drive_directory
    frmr.prove_method = c.prove_method
    frmr.system_stats = c.system_stats
    frmr.disk_farms = c.disk_farms
    frmr.farmer_name = c.farmer_name
    frmr.replotting = c.replotting
    frmr.warnings = c.warnings
    frmr.errors = c.errors
    frmr.startTime = c.startTime
    frmr.farm_rewards = c.farm_rewards
    frmr.farm_skips = c.farm_skips
    frmr.farm_metrics = c.farm_metrics  # Add farm_metrics to the object
    return frmr


def serialize_sets(obj):
    if isinstance(obj, set):
        return list(obj)
    return obj


async def ws_client():
    reconnect_delay = 20
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
        print(f'Unexpected error: {e}. Retrying in {reconnect_delay} seconds...')
    finally:
        await asyncio.sleep(reconnect_delay)


def main():
    asyncio.run(ws_client())
