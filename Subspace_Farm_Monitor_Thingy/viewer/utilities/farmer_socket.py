import websockets
import asyncio
import utilities.conf as c

import json
import time

global errored


class Farmer(object):
    
    def __init__(self, farmer_name="Unknown", warnings=[], errors=[], startTime='', farm_rewards={}, farm_recent_rewards={}, disk_farms={}, farm_skips={}, farm_recent_skips={}, farm_metrics={}, drive_directory={}, l3_concurrency='', l3_farm_sector_time='', dropped_drives=[]):
        
        self.dropped_drives = dropped_drives
        self.farmer_name = farmer_name
        self.warnings = warnings
        self.errors = errors
        self.drive_directory = drive_directory
        self.startTime = startTime
        self.farm_rewards = farm_rewards
        self.farm_recent_rewards = farm_recent_rewards
        self.disk_farms = disk_farms
        self.farm_skips = farm_skips
        self.farm_recent_skips = farm_recent_skips
        self.farm_metrics = farm_metrics
        #self.last_sector_time = last_sector_time
        self.dropped_drives = dropped_drives
        self.l3_concurrency = l3_concurrency
        self.l3_farm_sector_time = l3_farm_sector_time


def make_farmer(farmer_name="Unknown", warnings=[], errors=[], startTime='', farm_rewards={}, farm_recent_rewards={}, farm_skips={}, farm_recent_skips={}, disk_farms={}, farm_metrics={}, drive_directory={}, l3_concurrency='', l3_farm_sector_time='',dropped_drives=[]):

    frmr = Farmer()
    frmr.dropped_drives = dropped_drives
    frmr.drive_directory = drive_directory
    frmr.farmer_name = farmer_name
    frmr.warnings = warnings
    frmr.errors = errors
    frmr.startTime = startTime
    frmr.farm_rewards = farm_rewards
    frmr.farm_recent_rewards = farm_recent_rewards
    frmr.farm_skips = farm_skips
    frmr.farm_recent_skips = farm_recent_skips
    frmr.disk_farms = disk_farms
    frmr.farm_metrics = farm_metrics
    frmr.l3_concurrency = l3_concurrency
    frmr.l3_farm_sector_time = l3_farm_sector_time

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
            c.audits[farmer_name] = farm_data.get('audits', {})
            c.proves[farmer_name] = farm_data.get('proves', {})
            c.rewards_per_hr[farmer_name] = farm_data.get('rewards_per_hr')
            c.drive_directory[farmer_name] = farm_data['drive_directory']
            c.farm_metrics[farmer_name] = farm_data['farm_metrics']
            c.farm_rewards[farmer_name] = farm_data['farm_rewards']
            c.farm_recent_rewards[farmer_name] = farm_data['farm_recent_rewards']
            c.system_stats[farmer_name] = farm_data['system_stats']
            c.prove_method[farmer_name] = farm_data['prove_method']
            c.farm_skips[farmer_name] = farm_data['farm_skips']
            c.farm_recent_skips[farmer_name] = farm_data['farm_recent_skips']
            #c.last_sector_time[farmer_name] = farm_data['last_sector_time']
            c.dropped_drives[farmer_name] = farm_data.get('dropped_drives', [])
            
            if errored:
                #print("Websocket is now reconnected.")
                errored = False
            time.sleep(.2)
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
