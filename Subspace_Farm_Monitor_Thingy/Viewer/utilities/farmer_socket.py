import websockets
import asyncio
import utilities.conf as c
import json
import time

global errored



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


async def ws_server(websocket, path):
    errored = False
    try:
        while True:
            farm_data = await websocket.recv()
            farm_data = json.loads(farm_data)
            farmer_name = farm_data['farmer_name']
            c.reward_count = 0
            # Update or add the farm with the current timestamp and data
            if farmer_name not in c.remote_farms:
                c.remote_farms[farmer_name] = {
                    'data': farm_data, 'last_update': time.time()}
                # Ensure this line is present and correct
                c.farm_names.append(farmer_name)
            else:
                c.remote_farms[farmer_name]['data'] = farm_data
                c.remote_farms[farmer_name]['last_update'] = time.time()

            c.warnings = farm_data['warnings']
            c.farm_rewards[farmer_name] = farm_data['farm_rewards']

            c.replotting = farm_data['replotting']
            if errored:
                print("Websocket is now reconnected.")
                errored = False

    except websockets.ConnectionClosedOK:
        errored = False
    except websockets.ConnectionClosedError as e:
        wait_period = 20

        errored = True
        print(f'Socket Exception... Retrying in {
              wait_period} seconds...\n {e}')
        time.sleep(wait_period)


async def main():
    async with websockets.serve(ws_server, "", c.ui_port,):
        await asyncio.Future()  # run forever
