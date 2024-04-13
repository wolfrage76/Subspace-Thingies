import os
import subprocess

# Install required Python packages for this setup script
subprocess.check_call(["pip", "install", "rich", "pyyaml"])

from rich.console import Console
from rich.prompt import Prompt, Confirm
import yaml

console = Console()

def install_requirements():
    console.print("[info]Installing required Python packages for Wolfrage's Subspace Monitor Thingy...[/info]")
    try:
        subprocess.check_call(["pip", "install", "-r", "requirements.txt"])
        console.print("[info]Python packages for Subspace installed successfully![/info]")
    except subprocess.CalledProcessError:
        console.print("[error]Failed to install required Python packages for Subspace. Please try running 'pip install -r requirements.txt' manually.[/error]")

def load_existing_config():
    if os.path.exists("config.yaml"):
        with open("config.yaml", "r") as file:
            return yaml.safe_load(file)
    return {}

def create_config(existing_config):
    config = {
      
        "FARMER_NAME": Prompt.ask("Enter your farmer name", default=existing_config.get("FARMER_NAME", "'Wolfrage Rocks'")),
        "FRONT_END_IP": Prompt.ask("Enter your View frontend IP", default=existing_config.get("FRONT_END_IP", "'127.0.0.1'")),
        "FRONT_END_PORT": Prompt.ask("Enter the port for the View frontend", default=existing_config.get("FRONT_END_PORT", "'8016'")),
        "FARMER_LOG": Prompt.ask("Enter the path to your Farmer log file", default=existing_config.get("FARMER_LOG", "''")),
        "FARMER_IP": Prompt.ask("Enter your Farmer IP", default=existing_config.get("FARMER_IP", "'127.0.0.1'")),
        "FARMER_PORT": Prompt.ask("Enter your Farmer port", default=existing_config.get("FARMER_PORT", "'9191'")),
        "WALLET": Prompt.ask("Enter your wallet address (leave blank to disable wallet monitoring)", default=existing_config.get("WALLET", "")),
        "NODE_IP": Prompt.ask("Enter your Node IP", default=existing_config.get("NODE_IP", "'127.0.0.1'")),
        "NODE_PORT": Prompt.ask("Enter the port for your Node", default=existing_config.get("NODE_PORT", "'9944'")),
        
        "SEND_DISCORD": Confirm.ask("Do you want to send notifications to Discord (y/n)?", default=existing_config.get("SEND_DISCORD", True)),
        "SEND_PUSHOVER": Confirm.ask("Do you want to send notifications to Pushover (y/n)?", default=existing_config.get("SEND_PUSHOVER", False)),
        "SHOW_LOGGING": True,
        "MUTE_HICKORY": True,
        "USE_BANNERS": True,
        "WAIT_PERIOD": '600',
        "TOGGLE_ENCODING": True,
        "TOGGLE_ENCODING_NODE": False,
        "HOUR_24": False,
        "IS_LIVE": False,
        "COMMANDLINE": "''"
    }

    if config["SEND_DISCORD"]:
        config["DISCORD_WEBHOOK"] = Prompt.ask("Enter your Discord webhook URL for general notifications", default=existing_config.get("DISCORD_WEBHOOK", ""))
        config["DISCORD_WALLET_NOTIFICATIONS"] = Prompt.ask("Enter your Discord webhook URL for wallet notifications (Can leave blank to use the same as general notifications)", default=config["DISCORD_WEBHOOK"])

    if config["SEND_PUSHOVER"]:
        config["PUSHOVER_APP_TOKEN"] = Prompt.ask("Enter your Pushover application token", default=existing_config.get("PUSHOVER_APP_TOKEN", ""))
        config["PUSHOVER_USER_KEY"] = Prompt.ask("Enter your Pushover user key", default=existing_config.get("PUSHOVER_USER_KEY", ""))

    return config

def save_config(config):
    with open("config.yaml", "w") as file:
        yaml.dump(config, file, default_flow_style=False)

def main():
    try:
        console.print("[bold magenta]Subspace Configuration Setup[/bold magenta]", style="bold underline")
        
        if Confirm.ask("Do you want to automatically install the required Python packages for Subspace Monitor Thingy via pip?"):
            install_requirements()

        if os.path.exists("config.yaml"):
            os.rename("config.yaml", "config.yaml.bak")
            console.print("[info]Existing config.yaml file backed up as config.yaml.bak[/info]")

        existing_config = load_existing_config()

        if Confirm.ask("Do you want to import settings from the existing config.yaml file?"):
            config = create_config(existing_config)
        else:
            config = create_config({})

        save_config(config)
        console.print("[info]Configuration saved to config.yaml[/info]")
    except KeyboardInterrupt:
        console.print("[error]Setup canceled by user. Exiting...[/error]")

if __name__ == "__main__":
    main()
