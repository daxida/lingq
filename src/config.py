import sys

from dotenv import dotenv_values, find_dotenv


class Config:
    def __init__(self) -> None:
        env_path = find_dotenv()
        if not env_path:
            print(
                "Error: could not find an .env file.\n"
                "Create an .env file and add the entry: APIKEY=YourLingQAPIKey\n"
                "Or use lingq setup YourLingQAPIKey\n"
                "Exiting."
            )
            sys.exit(1)

        config = dotenv_values(env_path)
        if "APIKEY" not in config:
            print(
                "Error: the .env file does not contain the LingQ APIKEY.\n"
                "Inside the .env file add the entry: APIKEY=YourLingQAPIKey\n"
                "Exiting."
            )
            sys.exit(1)

        self.key = config["APIKEY"]
        self.headers = {"Authorization": f"Token {self.key}"}
