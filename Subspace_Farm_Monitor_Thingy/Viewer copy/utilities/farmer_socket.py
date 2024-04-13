import websockets
import asyncio
import utilities.conf as c

import json
import time

global errored


class Farmer(object):
    def __init__(self, farmer_name="Unknown", replotting={}, warnings=[], errors=[],  startTime='', farm_rewards={}, disk_farms={}, farm_skips={}, farm_metrics={}, drive_directory={} ):
        # print(farmer_name)
        
        self.farmer_name = farmer_name
        self.replotting = replotting
        self.warnings = warnings
        self.errors = errors
        self.drive_directory = drive_directory
        self.startTime = startTime
        self.farm_rewards = farm_rewards
        self.disk_farms = disk_farms
        self.farm_skips = farm_skips
        self.farm_metrics = farm_metrics


def make_farmer(farmer_name="Unknown", replotting={}, warnings=[], errors=[], startTime='', farm_rewards={}, farm_skips={}, disk_farms={}, farm_metrics={}, drive_directory={}):

    frmr = Farmer()
    frmr.drive_directory = drive_directory
    frmr.farmer_name = farmer_name
    frmr.replotting = replotting
    frmr.warnings = warnings
    frmr.errors = errors
    frmr.startTime = startTime
    frmr.farm_rewards = farm_rewards
    frmr.farm_skips = farm_skips
    frmr.disk_farms = disk_farms
    frmr.farm_metrics = farm_metrics

    return frmr


# Creating WebSocket server

def start():
    asyncio.run(main())


async def ws_server(websocket, path):
    errored = False
    try:
        while c.running:
            farm_data = await websocket.recv()
            farm_data = json.loads(farm_data)
            farmer_name = farm_data['farmer_name']
            if farmer_name not in c.remote_farms:
                c.remote_farms[farmer_name] = {
                    'data': farm_data, 'last_update': time.time()}
                c.farm_names.append(farmer_name)
            else:
                c.remote_farms[farmer_name]['data'] = farm_data
                c.remote_farms[farmer_name]['last_update'] = time.time()

           # c.warnings[farmer_name] = farm_data['warnings']
            c.rewards_per_hr[farmer_name] = farm_data.get('rewards_per_hr')
            c.drive_directory[farmer_name] = farm_data['drive_directory']
            c.farm_metrics[farmer_name] = farm_data['farm_metrics']
            c.farm_rewards[farmer_name] = farm_data['farm_rewards']
            c.system_stats[farmer_name] = farm_data['system_stats']
            c.replotting[farmer_name] = farm_data['replotting']
            c.prove_method[farmer_name] = farm_data['prove_method']
            c.farm_skips[farmer_name] = farm_data['farm_skips']
            if errored:
                #print("Websocket is now reconnected.")
                errored = False
            time.sleep(.01)
    except websockets.ConnectionClosedOK:
        errored = False
    except websockets.ConnectionClosedError as e:
        wait_period = 45 # *************************

        errored = True
        #print(f'Socket Exception... Retrying in {wait_period} seconds...\n {e}')
        time.sleep(wait_period)


async def main():
    async with websockets.serve(ws_server, '', c.ui_port,):
        await asyncio.Future()  # run forever
