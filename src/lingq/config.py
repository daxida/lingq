import sys
from pathlib import Path

from dotenv import dotenv_values
from platformdirs import user_config_dir

CONFIG_DIR = Path(user_config_dir(appname="lingq"))
CONFIG_PATH = CONFIG_DIR / ".env"


class Config:
    def __init__(self) -> None:
        if not CONFIG_PATH.exists():
            print(
                "Error: could not find the config file.\n"
                "To create one, use the command: lingq setup YourLingQAPIKey\n"
                "You can find your API key at: https://www.lingq.com/accounts/apikey/"
                "Exiting."
            )
            sys.exit(1)

        config = dotenv_values(CONFIG_PATH)
        if "APIKEY" not in config:
            # This should never happen unless one manually edits the config file.
            print(
                f"Error: the config file at {CONFIG_PATH} does not have a LingQ API key.\n"
                "To add one, use the command: lingq setup YourLingQAPIKey\n"
                "You can find your API key at: https://www.lingq.com/accounts/apikey/"
                "Exiting."
            )
            sys.exit(1)

        self.key = config["APIKEY"]
        self.headers = {"Authorization": f"Token {self.key}"}
