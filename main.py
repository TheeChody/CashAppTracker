import os
import sys
import time
import asyncio
import datetime
from pathlib import Path
from obswebsocket import obsws, requests
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.object.eventsub import ChannelChatMessageEvent

if getattr(sys, 'frozen', False):
    application_path = f"{os.path.dirname(sys.executable)}\\_internal\\"
else:
    application_path = os.path.dirname(__file__)

data_path = f'{application_path}data\\'
Path(data_path).mkdir(parents=True, exist_ok=True)

time_format = "%Y-%m-%d %H:%M:%S"
id_streamer = "50014629"  # "268136120"  # Chody  # "50014629"  # Ronin
target_scopes = [AuthScope.CHANNEL_BOT, AuthScope.USER_READ_CHAT, AuthScope.USER_WRITE_CHAT, AuthScope.CHANNEL_MODERATE, AuthScope.USER_READ_BROADCAST, AuthScope.MODERATOR_MANAGE_CHAT_MESSAGES]
moderators = ("563919062", "659673020", "57231965", "755808445", "742401277", "659640208", "517351918", "195782134", "761241392", "588989623", "781923878", "82006620", "192918528", "872594380", "1211252085")


class BotSetup(Twitch):
    def __init__(self, app_id: str, app_secret: str):
        super().__init__(app_id, app_secret)
        self.bot = Twitch


class WebsocketsManager:
    ws = None

    def __init__(self):
        self.ws = obsws(obs_host, obs_port, obs_pass)

    def connect(self):
        try:
            self.ws.connect()
            return True
        except Exception as e:
            print(f"Error connecting to OBS -- {e}")
            return False

    def disconnect(self):
        self.ws.disconnect()

    def set_source_visibility(self, scene_name, source_name, source_visible=True):
        response = self.ws.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))
        item_id = response.datain['sceneItemId']
        self.ws.call(requests.SetSceneItemEnabled(sceneName=scene_name, sceneItemId=item_id, sceneItemEnabled=source_visible))

    def set_text(self, source_name, new_text):
        self.ws.call(requests.SetInputSettings(inputName=source_name, inputSettings={'text': new_text}))


def refresh_total_goal():
    with open(f"{data_path}cash_goal", "r") as file:
        cash_goal = int(file.read())
    with open(f"{data_path}cash_total", "r") as file:
        cash_total = int(file.read())
    return cash_goal, cash_total


async def shutdown():
    try:
        obs.disconnect()
        print("OBS Disconnected"), time.sleep(0.5)
    except Exception as e:
        print(f"Error shutting down OBS -- {e}"), time.sleep(0.5)
        pass
    try:
        await bot.close()
        print("Twitch Connection Closed"), time.sleep(0.5)
    except Exception as e:
        print(f"Error shutting down twitch bot -- {e}"), time.sleep(0.5)
        pass
    os._exit(1)


async def on_stream_message(data: ChannelChatMessageEvent):
    cash_goal, cash_total = refresh_total_goal()
    if data.event.message.text.startswith("!cashapp"):
        if data.event.chatter_user_id in (id_streamer, "268136120"):
            add = True
            error = False
            error_msg = f"{data.event.chatter_user_name} make sure the command is valid eh? !cashapp add/remove x"
            msg = data.event.message.text.replace(" ", "")
            amount = msg.removeprefix("!cashapp")
            if amount.startswith("add"):
                amount = amount.removeprefix("add")
                if amount.isdigit():
                    cash_total += int(amount)
                    with open(f"{data_path}cash_total", "w") as file:
                        file.write(str(cash_total))
                else:
                    await bot.send_chat_message(id_streamer, id_streamer, error_msg)
                    error = True
            elif amount.startswith("remove"):
                add = False
                amount = amount.removeprefix("remove")
                if amount.isdigit():
                    cash_total -= int(amount)
                    with open(f"{data_path}cash_total", "w") as file:
                        file.write(str(cash_total))
                else:
                    await bot.send_chat_message(id_streamer, id_streamer, error_msg)
                    error = True
            else:
                await bot.send_chat_message(id_streamer, id_streamer, error_msg)
                error = True
            if not error:
                obs.set_text(obs_source_name, f"CashApp Bet\n${cash_total}/{cash_goal}\n$roningt81")
                await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; ${amount} {'contributed' if add else 'removed due to correction'}; ${cash_goal - cash_total} remaining; {time_end - datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), time_format)} time left.")
        elif data.event.chatter_user_id in moderators:
            await bot.send_chat_message(id_streamer, id_streamer, f"This command is restricted to RoninGT and TheeChody temporarily")
        else:
            await bot.send_chat_message(id_streamer, id_streamer, f"This mod is restricted to RoninGT and TheeChody temporarily, then restricted to Moderators", reply_parent_message_id=data.event.message_id)


async def run():
    twitch_helper = UserAuthenticationStorageHelper(bot, target_scopes)
    await twitch_helper.bind()

    event_sub = EventSubWebsocket(bot)
    event_sub.start()

    await event_sub.listen_channel_chat_message(id_streamer, id_streamer, on_stream_message)

    while True:
        try:
            cash_add = 0
            cash_remove = 0
            option = input("Enter 1 to message remaining goal & time left\nEnter 2 to ADD to CashApp balance\nEnter 3 to REMOVE from CashApp balance\nEnter 0 to exit program\n")
            if option not in ('0', '1', '2', '3'):
                print("Please make a valid choice")
            elif option == "0":
                print("Exiting program..\nProgram will close in 2 seconds, or close program manually"), time.sleep(2)
                await shutdown()
            elif option == "1":
                cash_goal, cash_total = refresh_total_goal()
                await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; ${cash_goal - cash_total} remaining; {time_end - datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), time_format)} time left.")
            elif option == "2":
                cash_goal, cash_total = refresh_total_goal()
                try:
                    cash_add = int(input("Enter cash to ADD to total gathered;\n"))
                    cash_total += cash_add
                except Exception as f:
                    print(f"Not Valid, try again -- {f}")
                with open(f"{data_path}cash_total", "w") as file:
                    file.write(str(cash_total))
                obs.set_text(obs_source_name, f"CashApp Bet\n${cash_total}/{cash_goal}\n$roningt81")
                await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; ${cash_add} contributed to thee CashApp Bet; ${cash_goal - cash_total} remaining. {time_end - datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), time_format)} time left.")
            elif option == "3":
                cash_goal, cash_total = refresh_total_goal()
                try:
                    cash_remove = int(input("Enter cash to REMOVE from total gathered;\n"))
                    cash_total -= cash_remove
                except Exception as f:
                    print(f"Not Valid, try again -- {f}")
                with open(f"{data_path}cash_total", "w") as file:
                    file.write(str(cash_total))
                obs.set_text(obs_source_name, f"CashApp Bet\n${cash_total}/{cash_goal}\n$roningt81")
                await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; ${cash_remove} removed due to correction; ${cash_goal - cash_total} remaining. {time_end - datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), time_format)} time left")
            else:
                print("IDK what key you pressed, but that wasn't valid"), time.sleep(5)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Error occurred -- {e}\nProgram will close in 120 seconds, or close program manually"), time.sleep(120)
            await shutdown()


if __name__ == "__main__":
    trigger = ""
    with open(f"{data_path}twitch_client", "r") as file:
        twitch_client = file.read()
        if twitch_client == "":
            trigger += "twitch_client\n"
    with open(f"{data_path}twitch_secret", "r") as file:
        twitch_secret = file.read()
        if twitch_secret == "":
            trigger += "twitch_secret\n"
    with open(f"{data_path}obs_host", "r") as file:
        obs_host = file.read()
        if obs_host == "":
            trigger += "obs_host\n"
    with open(f"{data_path}obs_port", "r") as file:
        obs_port = file.read()
        if obs_port == "":
            trigger += "obs_port\n"
    with open(f"{data_path}obs_pass", "r") as file:
        obs_pass = file.read()
        if obs_pass == "":
            trigger += "obs_pass\n"
    with open(f"{data_path}obs_scene_name", "r") as file:
        obs_scene_name = file.read()
        if obs_scene_name == "":
            trigger += "obs_scene_name\n"
    with open(f"{data_path}obs_source_name", "r") as file:
        obs_source_name = file.read()
        if obs_source_name == "":
            trigger += "obs_source_name\n"
    if trigger != "":
        print(f"Please make sure all the files have the appropriate keys please\n\n\n{trigger}\nis(are) empty!\nProgram will close in 120 seconds, or close program manually"), time.sleep(120)
        os._exit(1)

    bot = BotSetup(twitch_client, twitch_secret)
    obs = WebsocketsManager()

    connect = obs.connect()
    if not connect:
        print("Error Establishing OBS Connection!!"), time.sleep(10)
        os._exit(1)

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

        print(f"{'Initialization' if initialize else 'Files Loaded'} successful!\nTime Start; {time_start}\nTime Till End; {time_end - datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), time_format)}")

        obs.set_source_visibility(obs_scene_name, obs_source_name, True)
        obs.set_text(obs_source_name, f"CashApp Bet\n${cash_total}/{cash_goal}\n$roningt81")

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error occurred -- {e}\nProgram will close in 120 seconds, or close program manually"), time.sleep(120)
        os._exit(1)

    asyncio.run(run())
