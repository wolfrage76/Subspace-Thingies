import time
import substrateinterface
import yaml
import utilities.conf as c
import requests


def get_wallet_balance(substrate):
    result = substrate.query("System", "Account", [c.wallet])
    balance = result.value["data"]["free"] + result.value["data"]["reserved"]
    return round(balance / 10 ** substrate.properties.get('tokenDecimals', 0), 3)


def format_balance(amount, substrate):
    return f"{amount:.3f} {substrate.properties.get('tokenSymbol', 'UNIT')}"


def send_notification(message, discord_url):
    if discord_url:
        data = {"content": message}
        response = requests.post(discord_url, json=data)
        if response.status_code not in [204]:
            print(f'Error sending Discord: {response.status_code}')


def WalletMon():
    with open('config.yaml', 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    # Configurations
    discord_wallet = config.get('DISCORD_WALLET_NOTIFICATIONS', None)
    discord_url = config.get('DISCORD_WEBHOOK', None)
    if discord_wallet:
        discord_url = discord_wallet

    wallet = c.wallet  # config.get('WALLET', None)
    wait_period = config.get('WAIT_PERIOD', 60)
    nodeip = config.get('NODE_IP', '127.0.0.1')
    nodeport = str(config.get('NODE_PORT', 9944))

    if wallet:
        substrate = substrateinterface.SubstrateInterface(
            url=f"ws://{nodeip}:{nodeport}")
        first_time = True
        last_balance = 0.0

        while True:
            try:
                current_balance = get_wallet_balance(substrate)

                if not first_time:
                    change = current_balance - last_balance
                    if change != 0:
                        direction = "received" if change > 0 else "removed"
                        sign = "+" if change > 0 else "-"
                        message = f" Your wallet {wallet[-5:]} {direction} coins! \nBalance @ {
                            format_balance(current_balance, substrate)}  (Change: {sign}{abs(change):.4f})"
                        send_notification(message, discord_url)

                else:
                    first_time = False

                last_balance = current_balance
                c.balance = format_balance(current_balance, substrate)
                time.sleep(wait_period)

            except Exception as e:
                print(f'Wallet Exception... Retrying in {
                      wait_period} seconds...')
                print(f'Wallet Error: {e}')
                time.sleep(wait_period)


# if __name__ == '__main__':
 #   WalletMon()
