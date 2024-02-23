import asyncio
import websockets
import conf as c
 
class Farmer(object):
    def __init__(self, farmer_name="Unknown", replotting={},warnings=[], errors=[], curr_sector_disk={} , plot_space={}, farm_plot_size={},deltas={} , total_completed=0, startTime ='', farm_rewards = {} ):
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
        
        

def make_farmer(farmer_name="Unknown", replotting={},warnings=[], errors=[], curr_sector_disk={} , plot_space={}, farm_plot_size={},deltas={} , total_completed=0, startTime ='', farm_rewards = {}):
    
    frmr = Farmer()
    
    frmr.farmer_name = 'NAME!!'
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
    print("WebSocket: Client Connected.")
    url = "ws://127.0.0.1:8016"
    # Connect to the server
    async with websockets.connect(url) as ws:
        
        await ws.send(make_farmer().jsondump())
        #await ws.send(f"{age}")
 
        # Stay alive forever, listen to incoming msgs
        while True:
            msg = await ws.recv()
            print(msg)
 
 
     
 
# Start the connection
asyncio.run(ws_client())