# Bitcoin Bart was here

import time
import substrateinterface
    
import yaml
import utilities.conf as c

global substrate
    
def WalletMon():
        with open('config.yaml', 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        
        
        ####CONFIG####
        
        c.discord_url = config['DISCORD_WEBHOOK']
        c.wallet = config['WALLET']  
        c.wait_period = config['WAIT_PERIOD']                                        
        c.show_ping = False # config['SHOW_PING']         # Show Ping notice in console to show it's alive
        
        c.nodeip = config['NODE_IP']                   # Your nodes IP -- 127.0.0.1, 192.168.1.69, whatever
        c.nodeport = config['NODE_PORT']               # Port the node is using
        
        ##############
        if c.wallet:
         while True:
            try:
                substrate = substrateinterface.SubstrateInterface(url="ws://" + c.nodeip +":" + c.nodeport)  
                #runtime_calls = substrate.get_metadata_runtime_call_functions()
                #runtime_calls = substrate.get_block('0xcb2f6be14111ff6e1a4ecdd71c4d10fbf629e4293fb980a8fabd6818fe89f33d')
                #print(runtime_calls)
                first_time = True  # We don't need to tell people their balance has changed on first run
                last_balance = 0.0

                while True:
             
                    balance = (query_wallet(substrate).value["data"]["free"] +
                            query_wallet(substrate).value["data"]["reserved"])
                    balance_from_exp = (balance / 10 ** substrate.properties.get('tokenDecimals', 0))
                    balance = str(balance_from_exp)
                    
                    if first_time:
                        last_balance = balance # 
                        #print('Starting Balance: ' + str(self.last_balance / 10 ** self.substrate.properties.get('tokenDecimals', 0)) )
                      
                    if balance != last_balance and not first_time:
                       
                        
                        if balance_from_exp > (last_balance / 10 ** substrate.properties.get('tokenDecimals', 0)):

                            chng = balance_from_exp - (
                                    last_balance / 10 ** substrate.properties.get('tokenDecimals', 0))
                            result = (
                                f"Wallet {c.nodeipwallet[-5:]} received coins! \nBalance @ {format_balance(balance)}  (Change: +{round(chng, 4)})")

                            #(result)
                            send(result)

                        elif balance_from_exp < (last_balance / 10 ** substrate.properties.get('tokenDecimals', 0)):
                            chng = (balance_from_exp - (
                                    last_balance / 10 ** substrate.properties.get('tokenDecimals', 0)))
                            result = f"Wallet {c.wallet[-5:]} removed coins! \nBalance @ {format_balance(balance)}  (Change: -{round(chng, 4)})"

                            print(result)
                            send( result)
                        else:
                            pass

                    first_time = False
                    last_balance = balance

                    time.sleep(60)
            except:
                print('Exception... Retrying in ' + str(60) + ' seconds...') # Yeah, needs real error 
                                                                                           # handling next
                time.sleep(60)

    
def send(msg=None, image=None):
        if msg and c.discord_url: 
        
##### Discord
            import requests
            data = {"content": msg}
            # self.discord_url = self.cfg['DISCORD_WEBHOOK']

            response = requests.post(c.discord_url, json=data)
            success_list = [204]
            if response.status_code not in success_list:
                print('Error sending Discord: ' + str(response.status_code))
                
        
def query_wallet(substrate):
    result = substrate.query(
        "System", "Account", [c.wallet]
    )
    return result

def format_balance(amount: int):
    amount = format(amount / 10 ** substrate.properties.get('tokenDecimals', 0), ".15g")
    return f"{amount} {substrate.properties.get('tokenSymbol', 'UNIT')}"

                
if __name__ == '__main__':

    # Run the bot
    WalletMon()
