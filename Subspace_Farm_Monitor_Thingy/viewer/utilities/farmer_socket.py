import websockets
import asyncio
import utilities.conf as c
import json
import time
import logging

# Toggle for enabling/disabling logging
ENABLE_LOGGING = False

# Configure logging if enabled
if ENABLE_LOGGING:
    logging.basicConfig(filename='farm_data.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log_info(message):
    if ENABLE_LOGGING:
        logging.info(message)

def log_error(message):
    if ENABLE_LOGGING:
        logging.error(message)

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
    log_info("Starting WebSocket server...")
    asyncio.run(main())

async def ws_server(websocket):
    errored = False
    try:
        while c.running:
            log_info("Waiting to receive data from websocket...")
            farm_data = await websocket.recv()
            log_info("Data received from websocket.")
            try:
                log_info("Attempting to parse received data...")
                parsed_data = json.loads(farm_data)
                log_info("Data parsed successfully.")
                
                farmer_name = parsed_data['farmer_name']
                log_info(f"Processing data for farmer: {farmer_name}")
                
                if farmer_name not in c.remote_farms:
                    log_info(f"Farmer {farmer_name} not in remote_farms. Adding new entry.")
                    c.remote_farms[farmer_name] = {
                        'data': parsed_data, 'last_update': time.time()}
                    c.farm_names.append(farmer_name)
                else:
                    log_info(f"Farmer {farmer_name} found in remote_farms. Updating existing entry.")
                    c.remote_farms[farmer_name]['data'] = parsed_data
                    c.remote_farms[farmer_name]['last_update'] = time.time()

                # Update farm-specific metrics
                log_info(f"Updating metrics for farmer: {farmer_name}")
                c.gpu = parsed_data.get('gpu_metrics', {})
                c.audits[farmer_name] = parsed_data.get('audits', {})
                c.proves[farmer_name] = parsed_data.get('proves', {})
                c.rewards_per_hr[farmer_name] = parsed_data.get('rewards_per_hr')
                c.drive_directory[farmer_name] = parsed_data['drive_directory']
                c.farm_metrics[farmer_name] = parsed_data['farm_metrics']
                c.farm_rewards[farmer_name] = parsed_data['farm_rewards']
                c.farm_recent_rewards[farmer_name] = parsed_data['farm_recent_rewards']
                c.system_stats[farmer_name] = parsed_data['system_stats']
                c.prove_method[farmer_name] = parsed_data['prove_method']
                c.farm_skips[farmer_name] = parsed_data['farm_skips']
                c.farm_recent_skips[farmer_name] = parsed_data['farm_recent_skips']
                c.dropped_drives[farmer_name] = parsed_data.get('dropped_drives', [])

                # Format parsed data and raw data for comparison
                log_info(f"Formatting data for farmer: {farmer_name}")
                formatted_data = json.dumps(parsed_data, indent=4)
                raw_data = farm_data
                
                # Store formatted data for later use (e.g., logging or UI display)
                if not hasattr(c, 'formatted_data'):
                    log_info("Creating formatted_data attribute in conf module.")
                    c.formatted_data = {}
                c.formatted_data[farmer_name] = {'formatted': formatted_data, 'raw': raw_data}
                
                # Log the formatted and raw data to a file
                log_info(f"Farmer: {farmer_name}\nFormatted Data:\n{formatted_data}\nRaw Data:\n{raw_data}")
                
                if errored:
                    log_info("WebSocket reconnected successfully.")
                    errored = False
            except json.JSONDecodeError:
                log_error("Failed to parse JSON data. JSONDecodeError encountered.")
                # Handle JSON parsing error if necessary
                pass

            await asyncio.sleep(0.2)
    except websockets.ConnectionClosedOK:
        log_info("WebSocket connection closed normally.")
        errored = False
    except websockets.ConnectionClosedError as e:
        wait_period = 45
        log_error(f"WebSocket connection closed with error: {e}. Retrying in {wait_period} seconds...")
        errored = True
        await asyncio.sleep(wait_period)

async def main():
    log_info("Initializing WebSocket server...")
    async with websockets.serve(ws_server, '', c.ui_port):
        log_info("WebSocket server running.")
        await asyncio.Future()  # run forever
