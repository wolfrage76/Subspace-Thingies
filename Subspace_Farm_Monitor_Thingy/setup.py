import os
import socket
import yaml


def is_valid_ip(address):
    try:
        socket.inet_aton(address)
        return True
    except socket.error:
        return False


def verify_path(prompt, default="", is_file=False):
    while True:
        user_input = input(
            f"{prompt} (default: {default}): ").strip() or default
        if is_file:
            if os.path.isfile(user_input):
                return user_input
            else:
                print("The file does not exist. Please enter a valid file path.")
        else:  # Assuming it's a directory path if not a file
            if os.path.isdir(user_input) or not user_input:
                return user_input
            else:
                print(
                    "The directory does not exist. Please enter a valid directory path.")


def verify_ip(prompt, default="127.0.0.1"):
    while True:
        user_input = input(
            f"{prompt} (default: {default}): ").strip() or default
        if is_valid_ip(user_input):
            return user_input
        else:
            print("Invalid IP address. Please enter a valid IP address.")


def get_input(prompt, default=None):
    return input(f"{prompt} (default: {default}): ").strip() or default


def get_boolean(prompt, default=False):
    while True:
        user_input = input(
            f"{prompt} (True/False, default: {default}): ").strip().lower() or str(default).lower()
        if user_input == 't' or user_input == 'true':
            return True
        elif user_input == 'f' or user_input == 'false':
            return False
        else:
            print("Invalid input. Please enter True or False.")


def main():
    config = {
        'FARMER_NAME': get_input('Enter the farmer name:', default='Wolfrage Rocks'),
        'NODE_IP': verify_ip('Enter your node IP address:', default='127.0.0.1'),
        'NODE_PORT': get_input('Enter the node port:', default='9944'),
        'FRONT_END_IP': verify_ip('Enter your View frontend IP address:', default='127.0.0.1'),
        'FRONT_END_PORT': get_input('Enter the View frontend port:', default='8016'),
        'FARMER_LOG': verify_path('Enter the path to your farmer log file:', is_file=True),
        'WALLET': get_input('Enter the wallet address (disables wallet balance monitoring if blank):'),
        'NODE_LOG_FILE': verify_path('Enter the path to your node log file:', is_file=True),
        'SEND_DISCORD': get_boolean('Send notifications to Discord?', default=False),
        'SEND_PUSHOVER': get_boolean('Send notifications to Pushover?', default=False),
        'DISCORD_WEBHOOK': get_input('Enter the Discord webhook URL:', default=None),
        'DISCORD_WEBHOOK': get_input('Enter the Discord webhook URL for WALLET notifications\nDefaults to regular webhhok URL if blank:', default=None),
        'PUSHOVER_APP_TOKEN': get_input('Enter the Pushover application token:', default=""),
        'PUSHOVER_USER_KEY': get_input('Enter the Pushover user key:', default=""),
        'WAIT_PERIOD': get_input('Enter the wallet check interval seconds:', default='120'),
        'HOUR_24': get_boolean('Use 24-hour format?', default=False),
    }

    with open('config.yaml', 'w') as file:
        yaml.dump(config, file, default_flow_style=False, sort_keys=False)

    print("Configuration saved to config.yaml")


if __name__ == "__main__":
    main()
