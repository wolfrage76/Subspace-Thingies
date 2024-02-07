import websockets
import asyncio
 
# Creating WebSocket server

def start():
    asyncio.run(main()
                )
async def ws_server(websocket):
    print("WebSocket: Server Started.")

 
    try:
        while True:
            # Receiving values from client
            farm_data = await websocket.recv()
            #age = await websocket.recv()
  
            # Prompt message when any of the field is missing
            if farm_data == "":
                print("Error Receiving Value from Client.")
                break
 
            # Printing details received by client
            print("Details Received from Client:")
            print(f"Farm Data: {farm_data}")
 
            # Sending a response back to the client
            if farm_data == "narf":
                await websocket.send(f"Yeahaw!")
            else:
                await websocket.send(f"Wakka wakka!")
 
    except websockets.ConnectionClosedError:
        print("Internal Server Error.")
 
 
async def main():
    async with websockets.serve(ws_server, "localhost", 7890):
        await asyncio.Future()  # run forever
 