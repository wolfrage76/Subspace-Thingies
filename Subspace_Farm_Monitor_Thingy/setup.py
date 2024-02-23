import os
import socket
import yaml

def is_valid_ip(address):
    try:
        socket.inet_aton(address)
        return True
    except socket.error:
        return False

def verify_path(prompt, default=None, is_file=False):
    while True:
        user_input = input(f"{prompt} (default: {default}): ").strip() or default
        if is_file:
            if os.path.isfile(user_input):
                return user_input
            else:
                print("The file does not exist. Please enter a valid file path.")
        else:  # Assuming it's a directory path if not a file
            if os.path.isdir(user_input) or not user_input:
                return user_input
            else:
                print("The directory does not exist. Please enter a valid directory path.")

def verify_ip(prompt, default="127.0.0.1"):
    while True:
        user_input = input(f"{prompt} (default: {default}): ").strip() or default
        if is_valid_ip(user_input):
            return user_input
        else:
            print("Invalid IP address. Please enter a valid IP address.")

def get_input(prompt, default=None):
    return input(f"{prompt} (default: {default}): ").strip() or default

def get_boolean(prompt, default=False):
    while True:
        user_input = input(f"{prompt} (True/False, default: {default}): ").strip().lower() or str(default).lower()
        if user_input in ['true', 'false']:
            return user_input == 'true'
        else:
            print("Invalid input. Please enter True or False.")

def main():
    config = {
        'IS_LIVE': get_boolean('Is this configuration for a live environment?', default=False),
        'TOGGLE_ENCODING': get_boolean('If reading Farmer log but disk list does not appear, set False. Has to deal with how you are logging.', default=False),
        'FARMER_NAME': get_input('Enter the farmer name:'),
        'NODE_IP': verify_ip('Enter your node IP address:', default='127.0.0.1'),
        'NODE_PORT': get_input('Enter the node port:', default='9944'),
        'FRONT_END_IP': verify_ip('Enter your View frontend IP address:', default='127.0.0.1'),
        'FRONT_END_PORT': get_input('Enter the View frontend port:', default='9944'),
        'SHOW_LOGGING': get_boolean('Show logging?', default=True),
        'FARMER_LOG': verify_path('Enter the path to your farmer log file:', is_file=True),
        'WALLET': get_input('Enter the wallet address:'),
        'NODE_EXECUTABLE_FOLDER': verify_path('Enter the node executable folder path:', is_file=False),
        'NODE_LOG_FILE': verify_path('Enter the path to your node log file:', is_file=True),
        'SEND_DISCORD': get_boolean('Send notifications to Discord?', default=True),
        'SEND_PUSHOVER': get_boolean('Send notifications to Pushover?', default=False),
        'DISCORD_WEBHOOK': get_input('Enter the Discord webhook URL:', default=""),
        'PUSHOVER_APP_TOKEN': get_input('Enter the Pushover application token:', default=""),
        'PUSHOVER_USER_KEY': get_input('Enter the Pushover user key:', default=""),
        'WAIT_PERIOD': get_input('Enter the wallet check interval seconds:', default='120'),
        'SHOW_PING': get_boolean('Show ping?', default=False),
        'MUTE_HICKORY': get_boolean('Mute Hickory?', default=True),
        'HOUR_24': get_boolean('Use 24-hour format?', default=False),
        'COMMANDLINE': get_input('Enter the command line to run:')
    }

    with open('config.yaml', 'w') as file:
        yaml.dump(config, file, default_flow_style=False, sort_keys=False)

    print("Configuration saved to config.yaml")

if __name__ == "__main__":
    main()