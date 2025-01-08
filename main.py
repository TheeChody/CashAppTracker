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
id_streamer = "268136120"  # "268136120" - Chody | "50014629" - Ronin
target_scopes = [AuthScope.CHANNEL_BOT, AuthScope.USER_READ_CHAT, AuthScope.USER_WRITE_CHAT]
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
    with open(f"{data_path}cash_goal.txt", "r") as file:
        cash_goal = int(file.read())
    with open(f"{data_path}cash_total.txt", "r") as file:
        cash_total = int(file.read())
    return cash_goal, cash_total


def time_left():
    return time_end - datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), time_format)


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
    async def send_error_msg(message_id: str):
        await bot.send_chat_message(id_streamer, id_streamer, f"Make sure the command is valid eh? !cashapp add/remove/change(goal/total) x", reply_parent_message_id=message_id)
        return True

    if data.event.message.text.startswith("!cashapp"):
        message_id = data.event.message_id
        cash_goal, cash_total = refresh_total_goal()
        if data.event.chatter_user_id in (id_streamer, "268136120"):
            add = True
            error = False
            change = None
            msg = data.event.message.text.replace(" ", "")
            amount = msg.removeprefix("!cashapp")
            if amount.startswith("add"):
                amount = amount.removeprefix("add")
                if amount.isdigit():
                    cash_total += int(amount)
                    with open(f"{data_path}cash_total.txt", "w") as file:
                        file.write(str(cash_total))
                else:
                    error = await send_error_msg(message_id)
            elif amount.startswith("remove"):
                add = False
                amount = amount.removeprefix("remove")
                if amount.isdigit():
                    cash_total -= int(amount)
                    with open(f"{data_path}cash_total.txt", "w") as file:
                        file.write(str(cash_total))
                else:
                    error = await send_error_msg(message_id)
            elif amount.startswith("change"):
                amount = amount.removeprefix("change")
                if amount.startswith("goal"):
                    change = "goal"
                    amount = amount.removeprefix("goal")
                    if amount.isdigit():
                        with open(f"{data_path}cash_goal.txt", "w") as file:
                            file.write(str(amount))
                        cash_goal, cash_total = refresh_total_goal()
                    else:
                        error = await send_error_msg(message_id)
                elif amount.startswith("total"):
                    change = "total"
                    amount = amount.removeprefix("total")
                    if amount.isdigit():
                        with open(f"{data_path}cash_total.txt", "w") as file:
                            file.write(str(amount))
                        cash_goal, cash_total = refresh_total_goal()
                    else:
                        error = await send_error_msg(message_id)
                else:
                    error = await send_error_msg(message_id)
            else:
                error = await send_error_msg(message_id)
            if change is None and not error:
                remaining = int(cash_goal - cash_total)
                obs.set_text(obs_source_name, f"CashApp Bet\n${int(cash_total):,}/${int(cash_goal):,}\n$roningt81")
                await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; ${amount} {'contributed' if add else 'removed due to correction'}; ${f'{remaining:,} remaining' if remaining >= 0 else f'{abs(remaining):,} extra for Ronin'}; Time Left: {time_left()}.", reply_parent_message_id=message_id)
            elif change is not None and not error:
                remaining = int(cash_goal - cash_total)
                obs.set_text(obs_source_name, f"CashApp Bet\n${int(cash_total):,}/${int(cash_goal):,}\n$roningt81")
                if change == "goal":
                    await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; New Goal Set @ ${int(cash_goal):,}; ${f'{remaining:,} remaining' if remaining >= 0 else f'{abs(remaining):,} extra for Ronin'}; Time Left: {time_left()}.", reply_parent_message_id=message_id)
                elif change == "total":
                    await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; New Total Contributed Set @ ${int(cash_total):,}; ${f'{remaining:,} remaining' if remaining >= 0 else f'{abs(remaining):,} extra for Ronin'}; Time Left: {time_left()}.", reply_parent_message_id=message_id)
        elif data.event.chatter_user_id in moderators:
            await bot.send_chat_message(id_streamer, id_streamer, f"This command is restricted to RoninGT and TheeChody temporarily", reply_parent_message_id=message_id)
        else:
            await bot.send_chat_message(id_streamer, id_streamer, f"This mod is restricted to RoninGT and TheeChody temporarily, then restricted to Moderators", reply_parent_message_id=message_id)


async def run():
    twitch_helper = UserAuthenticationStorageHelper(bot, target_scopes)
    await twitch_helper.bind()

    event_sub = EventSubWebsocket(bot)
    event_sub.start()

    await event_sub.listen_channel_chat_message(id_streamer, id_streamer, on_stream_message)

    while True:
        try:
            option = input("Enter 1 to message remaining goal & time left\nEnter 2 to ADD to CashApp balance\nEnter 3 to REMOVE from CashApp balance\nEnter 4 to change goal\nEnter 5 to change total contributed\nEnter 0 to exit program\n")
            if option not in ('0', '1', '2', '3', '4', '5'):
                print("Please make a valid choice")
            elif option == "0":
                print("Exiting program..\nProgram will close in 2 seconds, or close program manually"), time.sleep(2)
                await shutdown()
            elif option == "1":
                cash_goal, cash_total = refresh_total_goal()
                remaining = int(cash_goal - cash_total)
                await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; ${f'{remaining:,} remaining' if remaining >= 0 else f'{abs(remaining):,} extra for Ronin'}; Time Left: {time_left()}.")
            elif option == "2":
                while True:
                    cash_goal, cash_total = refresh_total_goal()
                    try:
                        cash_add = int(input("Enter cash to ADD to total gathered;\n"))
                        cash_total += cash_add
                    except Exception as f:
                        print(f"Not Valid, try again -- {f}")
                        break
                    with open(f"{data_path}cash_total.txt", "w") as file:
                        file.write(str(cash_total))
                    remaining = int(cash_goal - cash_total)
                    obs.set_text(obs_source_name, f"CashApp Bet\n${int(cash_total):,}/${int(cash_goal):,}\n$roningt81")
                    await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; ${cash_add} contributed; ${f'{remaining:,} remaining' if remaining >= 0 else f'{abs(remaining):,} extra for Ronin'}; Time Left: {time_left()}.")
                    break
            elif option == "3":
                while True:
                    cash_goal, cash_total = refresh_total_goal()
                    try:
                        cash_remove = int(input("Enter cash to REMOVE from total gathered;\n"))
                        cash_total -= cash_remove
                    except Exception as f:
                        print(f"Not Valid, try again -- {f}")
                        break
                    with open(f"{data_path}cash_total.txt", "w") as file:
                        file.write(str(cash_total))
                    remaining = int(cash_goal - cash_total)
                    obs.set_text(obs_source_name, f"CashApp Bet\n${int(cash_total):,}/${int(cash_goal):,}\n$roningt81")
                    await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; ${cash_remove} removed due to correction; ${f'{remaining:,} remaining' if remaining >= 0 else f'{abs(remaining):,} extra for Ronin'}; Time Left: {time_left()}.")
                    break
            elif option == "4":
                while True:
                    cash_goal, cash_total = refresh_total_goal()
                    try:
                        new_goal = int(input("Enter thee new Goal Value\n"))
                    except Exception as f:
                        print(f"Not Valid, try again -- {f}")
                        break
                    with open(f"{data_path}cash_goal.txt", "w") as file:
                        file.write(str(new_goal))
                    remaining = int(new_goal - cash_total)
                    obs.set_text(obs_source_name, f"CashApp Bet\n${int(cash_total):,}/${int(new_goal):,}\n$roningt81")
                    await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; New Goal Set @ {int(new_goal):,}; ${f'{remaining:,} remaining' if remaining >= 0 else f'{abs(remaining):,} extra for Ronin'}; Time Left: {time_left()}.")
                    break
            elif option == "5":
                while True:
                    cash_goal, cash_total = refresh_total_goal()
                    try:
                        new_total = int(input("Enter thee new Total Contributed Value\n"))
                    except Exception as f:
                        print(f"Not Valid, try again -- {f}")
                        break
                    with open(f"{data_path}cash_total.txt", "w") as file:
                        file.write(str(new_total))
                    remaining = int(cash_goal - new_total)
                    obs.set_text(obs_source_name, f"CashApp Bet\n${int(new_total):,}/${int(cash_goal):,}\n$roningt81")
                    await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; New Total Contributed Set @ {int(new_total):,}; ${f'{remaining:,} remaining' if remaining >= 0 else f'{abs(remaining):,} extra for Ronin'}; Time Left: {time_left()}.")
                    break
            else:
                print("IDK what key you pressed, but that wasn't valid"), time.sleep(2.5)
        except KeyboardInterrupt:
            print("Exiting program.."), time.sleep(2)
            await shutdown()
        except Exception as e:
            print(f"Error occurred -- {e}\nProgram will close in 120 seconds, or close program manually"), time.sleep(120)
            await shutdown()


if __name__ == "__main__":
    trigger = ""
    with open(f"{data_path}twitch_client.txt", "r") as file:
        twitch_client = file.read()
        if twitch_client == "":
            trigger += "twitch_client\n"
    with open(f"{data_path}twitch_secret.txt", "r") as file:
        twitch_secret = file.read()
        if twitch_secret == "":
            trigger += "twitch_secret\n"
    with open(f"{data_path}obs_host.txt", "r") as file:
        obs_host = file.read()
        if obs_host == "":
            trigger += "obs_host\n"
    with open(f"{data_path}obs_port.txt", "r") as file:
        obs_port = file.read()
        if obs_port == "":
            trigger += "obs_port\n"
    with open(f"{data_path}obs_pass.txt", "r") as file:
        obs_pass = file.read()
        if obs_pass == "":
            trigger += "obs_pass\n"
    with open(f"{data_path}obs_scene_name.txt", "r") as file:
        obs_scene_name = file.read()
        if obs_scene_name == "":
            trigger += "obs_scene_name\n"
    with open(f"{data_path}obs_source_name.txt", "r") as file:
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
            with open(f"{data_path}time_start.txt", "w") as file:
                file.write(str(time_start))
            with open(f"{data_path}time_end.txt", "w") as file:
                file.write(str(time_end))
            cash_goal = int(input("Enter CashApp Goal Value\n"))
            with open(f"{data_path}cash_goal.txt", "w") as file:
                file.write(str(cash_goal))
            with open(f"{data_path}cash_total.txt", "w") as file:
                file.write(str(0))
        else:
            with open(f"{data_path}time_start.txt", "r") as file:
                time_start = file.read()
                time_start = datetime.datetime.strptime(time_start, time_format)
            with open(f"{data_path}time_end.txt", "r") as file:
                time_end = file.read()
                time_end = datetime.datetime.strptime(time_end, time_format)
            with open(f"{data_path}cash_goal.txt", "r") as file:
                cash_goal = int(file.read())
            with open(f"{data_path}cash_total.txt", "r") as file:
                cash_total = int(file.read())

        print(f"{'Initialization' if initialize else 'Files Loaded'} successful{'ly' if not initialize else ''}!\nTime Start; {time_start}\nTime Till End; {time_left()}")

        obs.set_source_visibility(obs_scene_name, obs_source_name, True)
        obs.set_text(obs_source_name, f"CashApp Bet\n${int(cash_total):,}/${int(cash_goal):,}\n$roningt81")
    except KeyboardInterrupt:
        print("Exiting program.."), time.sleep(2)
        os._exit(1)
    except Exception as e:
        print(f"Error occurred -- {e}\nProgram will close in 120 seconds, or close program manually"), time.sleep(120)
        os._exit(1)

    asyncio.run(run())
