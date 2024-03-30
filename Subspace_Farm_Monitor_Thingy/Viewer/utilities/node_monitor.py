import asyncio
import websockets
import json
import utilities.conf as c
import time
import yaml

with open("config.yaml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

#################

nodeip = config['NODE_IP']
nodeport = config['NODE_PORT']
async def fetch_node_info():
    
    uri = f"ws://{nodeip}:{nodeport}"
    while c.running:
        try:
            async with websockets.connect(uri) as websocket:
                # Peer count
                await websocket.send(json.dumps({
                    "jsonrpc": "2.0",
                    "method": "system_peers",
                    "params": [],
                    "id": 1
                }))
                peer_count_response = await websocket.recv()
                peer_count = len(json.loads(peer_count_response).get('result', []))
                
                # Sync state
                await websocket.send(json.dumps({
                    "jsonrpc": "2.0",
                    "method": "system_health",
                    "params": [],
                    "id": 2
                }))
                sync_state_response = await websocket.recv()
                is_syncing = json.loads(sync_state_response).get('result', {}).get('isSyncing', False)
                
                # Best block hash
                await websocket.send(json.dumps({
                    "jsonrpc": "2.0",
                    "method": "chain_getBlockHash",
                    "params": [],
                    "id": 3
                }))
                best_block_hash_response = await websocket.recv()
                best_block_hash = json.loads(best_block_hash_response).get('result')
                
                # Block details for best block hash
                await websocket.send(json.dumps({
                    "jsonrpc": "2.0",
                    "method": "chain_getBlock",
                    "params": [best_block_hash],
                    "id": 4
                }))
                best_block_response = await websocket.recv()
                best_block_number_hex = json.loads(best_block_response).get('result', {}).get('block', {}).get('header', {}).get('number', '0x0')
                best_block_number = int(best_block_number_hex, 16)
                
                # Update global configuration
                c.peers = peer_count
                c.best_block = best_block_number
                c.is_syncing = is_syncing

        except websockets.ConnectionClosed:
            print("Connection closed, attempting to reconnect in 20 seconds...")
            time.sleep(20)
        except Exception as e:
            print(f"A node monitor error occurred: {e}")
            time.sleep(20)