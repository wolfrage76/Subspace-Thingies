# Bitcoin Bart was here

import time
from substrateinterface import SubstrateInterface

class WalletMon(object):
    
    
    
    def __init__(self):
    
        import yaml

        with open('config.yaml', 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        
        
        ####CONFIG####
        
        self.discord_url = config['DISCORD_WEBHOOK']
        self.wallet = config['WALLET']  
        self.wait_period = config['WAIT_PERIOD']                                        
        
        nodeip = config['NODE_IP']     # Your nodes IP -- 127.0.0.1, 192.168.1.69, whatever
        nodeport = config['NODE_PORT']            # Port the node is using
        self.show_ping = True        # Show Ping notice in console to show it's alive
        
        ##############
        while True:
            try:
                self.substrate = SubstrateInterface(url="ws://" + nodeip + ":" + nodeport)  

                self.first_time = True  # We don't need to tell people their balance has changed on first run
                self.last_balance = 0.0
                
            
            
 #       print('Starting wallet monitoring...')
 #       send(self,'Starting wallet monitoring...')
        # map multiple wallets in query  # Eventually
                '''
                hash = substrate.get_chain_finalised_head()
                result = substrate.query_map('System', 'Account', block_hash = hash, max_results=2)
                for account, account_info in result:
                    print(f"Free balance of account '{account.value}': {account_info.value['data']['free']}")
                '''

                while True:
             
                    balance = (self.query_wallet(self.substrate).value["data"]["free"] +
                            self.query_wallet(self.substrate).value["data"]["reserved"])
                    balance_from_exp = (balance / 10 ** self.substrate.properties.get('tokenDecimals', 0))

                    if self.first_time:
                        self.last_balance = balance # 
                        print('Starting Balance: ' + str(self.last_balance / 10 ** self.substrate.properties.get('tokenDecimals', 0)) )
                        
                    if balance != self.last_balance and not self.first_time:
                        if balance_from_exp > (self.last_balance / 10 ** self.substrate.properties.get('tokenDecimals', 0)):

                            chng = balance_from_exp - (
                                    self.last_balance / 10 ** self.substrate.properties.get('tokenDecimals', 0))
                            result = (
                                f"Wallet {self.wallet[-5:]} received coins! \nBalance @ {self.format_balance(balance)}  (Change: +{round(chng, 4)})")

                            print(result)
                            send(self, result)

                        elif balance_from_exp < (self.last_balance / 10 ** self.substrate.properties.get('tokenDecimals', 0)):
                            chng = (balance_from_exp - (
                                    self.last_balance / 10 ** self.substrate.properties.get('tokenDecimals', 0)))
                            result = f"Wallet {self.wallet[-5:]} removed coins! \nBalance @ {self.format_balance(balance)}  (Change: -{round(chng, 4)})"

                            print(result)
                            send(self, result)
                        else:
                            pass

                    self.first_time = False
                    self.last_balance = balance

                    if self.show_ping: 
                        print(time.strftime("%H:%M |", time.localtime()) + ' Ping! Still alive!')
                    time.sleep(self.wait_period)
            except:
                print('Exception... Retrying in ' + str(self.wait_period) + ' seconds...') # Yeah, needs real error 
                                                                                           # handling next
                time.sleep(self.wait_period)
                
        
    def query_wallet(self, substrate):
        result = substrate.query(
            "System", "Account", [self.wallet]
        )
        return result

    def format_balance(self, amount: int):
        amount = format(amount / 10 ** self.substrate.properties.get('tokenDecimals', 0), ".15g")
        return f"{amount} {self.substrate.properties.get('tokenSymbol', 'UNIT')}"
    
    
def send(self, msg=None, image=None):
        if msg and self.discord_url: 
        
##### Discord
            import requests
            data = {"content": msg}
            # self.discord_url = self.cfg['DISCORD_WEBHOOK']

            response = requests.post(self.discord_url, json=data)
            success_list = [204]
            if response.status_code not in success_list:
                print('Error sending Discord: ' + str(response.status_code))
                
                
if __name__ == '__main__':

    # Run the bot
    WalletMon()
