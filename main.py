import asyncio
import os
import sys
import datetime
from pathlib import Path
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope
from twitchAPI.oauth import UserAuthenticationStorageHelper

if getattr(sys, 'frozen', False):
    application_path = f"{os.path.dirname(sys.executable)}\\_internal"
else:
    application_path = os.path.dirname(__file__)

data_path = f'{application_path}\\data\\'
Path(data_path).mkdir(parents=True, exist_ok=True)

time_format = "%Y-%m-%d %H:%M:%S"
with open(f"{data_path}twitch_client", "r") as file_client:
    twitch_client = file_client.read()
with open(f"{data_path}twitch_secret", "r") as file_secret:
    twitch_secret = file_secret.read()
if twitch_client == "" or twitch_secret == "":
    print("Please make sure all the files have the appropriate keys please")
    bot_files_loaded = False
else:
    bot_files_loaded = True

id_streamer = "50014629"  # "268136120"  # Chody  # "50014629"  # Ronin
target_scopes = [AuthScope.CHANNEL_BOT, AuthScope.USER_READ_CHAT, AuthScope.USER_WRITE_CHAT,
                 AuthScope.CHANNEL_MODERATE, AuthScope.USER_READ_BROADCAST, AuthScope.MODERATOR_MANAGE_CHAT_MESSAGES]


class BotSetup(Twitch):
    def __init__(self, app_id: str, app_secret: str):
        super().__init__(app_id, app_secret)
        self.bot = Twitch


async def run():
    bot = BotSetup(twitch_client, twitch_secret)

    twitch_helper = UserAuthenticationStorageHelper(bot, target_scopes)
    await twitch_helper.bind()

    while True:
        try:
            initialize = input("Initialize program? Y/N\n")
            if initialize.lower() in ("y", "yes"):
                initialize = True
            else:
                initialize = False
            if initialize:
                cash_total = 0
                time_start = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), time_format)
                time_end = input("Input end date; YYYY-mm-dd HH:MM:SS\n")
                time_end = datetime.datetime.strptime(time_end, time_format)
                with open(f"{data_path}time_start", "w") as file_start:
                    file_start.write(str(time_start))
                with open(f"{data_path}time_end", "w") as file_end:
                    file_end.write(str(time_end))
                cash_goal = int(input("Enter CashApp Goal Value\n"))
                with open(f"{data_path}cash_goal", "w") as file_cash_goal:
                    file_cash_goal.write(str(cash_goal))
            else:
                with open(f"{data_path}time_start", "r") as file_start:
                    time_start = file_start.read()
                    time_start = datetime.datetime.strptime(time_start, time_format)
                with open(f"{data_path}time_end", "r") as file_end:
                    time_end = file_end.read()
                    time_end = datetime.datetime.strptime(time_end, time_format)
                with open(f"{data_path}cash_goal", "r") as file_cash_goal:
                    cash_goal = int(file_cash_goal.read())
                with open(f"{data_path}cash_total", "r") as file_cash_total:
                    cash_total = int(file_cash_total.read())

            print(time_start, time_end - time_start)
            while True:
                option = input("Enter 1 to print out time remaining & Goal Progress\nEnter 2 to update cash app balance\nEnter 0 to exit program\n")
                if option not in ('0', '1', '2'):
                    print("Please make a valid choice")
                elif option == "0":
                    print("Exiting program..")
                    break
                elif option == "1":
                    await bot.send_chat_message(id_streamer, id_streamer, f"{time_end - datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), time_format)} time left. ${cash_goal - cash_total} remaining.")
                elif option == "2":
                    cash_add = int(input("Enter cash to add to total gathered;\n"))
                    cash_total += cash_add
                    with open(f"{data_path}cash_total", "w") as file_cash_total:
                        file_cash_total.write(str(cash_total))
                    await bot.send_chat_message(id_streamer, id_streamer, f"{time_end - datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), time_format)} time left. ${cash_goal - cash_total} remaining.")
                else:
                    print("IDK what key you pressed, but that wasn't valid")
            break
        except Exception as e:
            print(f"Error occurred -- {e}")
            break


if __name__ == "__main__":
    asyncio.run(run())
