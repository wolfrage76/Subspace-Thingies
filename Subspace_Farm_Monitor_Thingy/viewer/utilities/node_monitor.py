import asyncio
import websockets
import json
import yaml
from rich.console import Console
from rich.traceback import install
import utilities.conf as c

install()

# Load configuration from YAML file
with open("config.yaml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

console = Console()
nodeip = config['NODE_IP']
nodeport = config['NODE_PORT']

async def fetch_node_info():
    uri = f"ws://{nodeip}:{nodeport}"

    while c.running:
        try:
            async with websockets.connect(uri) as websocket:
                #console.log(f"Connected to {uri}")
                while c.running:
                    # Request for system peers
                    await websocket.send(json.dumps({
                        "jsonrpc": "2.0",
                        "method": "system_peers",
                        "params": [],
                        "id": 1
                    }))
                    peer_count_response = await websocket.recv()
                    peer_count = len(json.loads(peer_count_response).get('result', []))

                    # Request for system health
                    await websocket.send(json.dumps({
                        "jsonrpc": "2.0",
                        "method": "system_health",
                        "params": [],
                        "id": 2
                    }))
                    sync_state_response = await websocket.recv()
                    is_syncing = json.loads(sync_state_response).get('result', {}).get('isSyncing', False)

                    # Request for best block hash
                    await websocket.send(json.dumps({
                        "jsonrpc": "2.0",
                        "method": "chain_getBlockHash",
                        "params": [],
                        "id": 3
                    }))
                    best_block_hash_response = await websocket.recv()
                    best_block_hash = json.loads(best_block_hash_response).get('result')

                    # Request for block details using the best block hash
                    await websocket.send(json.dumps({
                        "jsonrpc": "2.0",
                        "method": "chain_getBlock",
                        "params": [best_block_hash],
                        "id": 4
                    }))
                    best_block_response = await websocket.recv()
                    best_block_number_hex = json.loads(best_block_response).get('result', {}).get('block', {}).get('header', {}).get('number', '0x0')
                    best_block_number = int(best_block_number_hex, 16)

                    # Update global configuration with fetched data
                    c.peers = peer_count
                    c.best_block = best_block_number
                    c.is_syncing = is_syncing

                    await asyncio.sleep(15)  # Wait before sending the next set of requests

        except websockets.ConnectionClosed as e:
            c.is_syncing = True
            #console.log("Connection closed unexpectedly, attempting to reconnect in 20 seconds...", style="bold red")
            await asyncio.sleep(20)  # Wait 20 seconds before attempting to reconnect

        except Exception as e:
            c.is_syncing = True
            #console.print(f"A node monitor error occurred: {e}", style="bold red")
            await asyncio.sleep(10)  # Wait before attempting to reconnect or proceed
        asyncio.sleep(.2)
# To run the fetch_node_info coroutine
# asyncio.run(fetch_node_info())
