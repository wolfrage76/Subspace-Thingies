import asyncio
import websockets
import utilities.conf as c
import json


class Farmer(object):
    def __init__(self, farmer_name="Unknown", replotting={}, warnings=[], errors=[], curr_sector_disk={}, plot_space={}, farm_plot_size={}, deltas={}, total_completed=0, startTime='', farm_rewards={}, disk_farms={}, farm_skips={}):
        # print(farmer_name)

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
        self.farm_skips = farm_skips


def make_farmer(farmer_name="Unknown", replotting={}, warnings=[], errors=[], curr_sector_disk={}, plot_space={}, farm_plot_size={}, deltas={}, total_completed=0, startTime='', farm_rewards={}, disk_farms={}, farm_skips={}):

    frmr = Farmer()

    frmr.disk_farms = c.disk_farms
    frmr.farmer_name = c.farmer_name
    frmr.replotting = c.replotting
    frmr.warnings = c.warnings
    frmr.errors = c.errors
    frmr.curr_sector_disk = c.curr_sector_disk
    frmr.plot_space = c.plot_space
    frmr.farm_plot_size = c.farm_plot_size
    frmr.deltas = c.deltas
    frmr.total_completed = c.total_completed
    frmr.startTime = c.startTime
    frmr.farm_rewards = c.farm_rewards
    frmr.farm_skips = c.farm_skips

    return frmr


def serialize_sets(obj):
    if isinstance(obj, set):
        return list(obj)

    return obj


async def ws_client():
    reconnect_delay = 20
    # print("WebSocket: Client Connected.")
    url = "ws://" + c.front_end_ip + ":" + c.front_end_port
    # Connect to the server

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
