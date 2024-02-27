import asyncio
import websockets
import conf as c
 
class Farmer(object):
    def __init__(self, farmer_name="Unknown", replotting={},warnings=[], errors=[], curr_sector_disk={} , plot_space={}, farm_plot_size={},deltas={} , total_completed=0, startTime = 0, farm_rewards = {} ):
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
        
        

def make_farmer(farmer_name="Unknown", replotting={},warnings=[], errors=[], curr_sector_disk={} , plot_space={}, farm_plot_size={},deltas={} , total_completed=0, startTime = 0, farm_rewards = {}):
    
    frmr = Farmer()
    
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

    
    
    return frmr

async def ws_client():
    retry_delay = 5  # seconds
    while True:
        try:
            print("Attempting to connect WebSocket client...")
            async with websockets.connect("ws://127.0.0.1:8016") as ws:
                # Send and receive messages as before
                await ws.send(make_farmer())
                while True:
                    msg = await ws.recv()
                    #print(msg)
        except OSError as e:
            print(f"Network error: {e}. The server might not be running. Retrying in {retry_delay} seconds...")
        except websockets.ConnectionClosed as e:
            print(f"WebSocket connection closed: {e}, retrying in {retry_delay} seconds...")
        except Exception as e:
            print(f"WebSocket error: {e}, retrying in {retry_delay} seconds...")
        finally:
            print("Attempting to reconnect...")
            await asyncio.sleep(retry_delay)
            
 
# Start the connection
asyncio.run(ws_client())