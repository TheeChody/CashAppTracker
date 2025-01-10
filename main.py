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
from twitchAPI.object.eventsub import ChannelChatMessageEvent, UserWhisperMessageEvent

if getattr(sys, 'frozen', False):
    application_path = f"{os.path.dirname(sys.executable)}\\_internal\\"
else:
    application_path = os.path.dirname(__file__)

data_path = f"{application_path}data\\"
Path(data_path).mkdir(parents=True, exist_ok=True)

time_format = "%Y-%m-%d %H:%M:%S"
id_streamer = "50014629"  # "268136120" - Chody | "50014629" - Ronin
target_scopes = [AuthScope.CHANNEL_BOT, AuthScope.USER_READ_CHAT, AuthScope.USER_WRITE_CHAT,
                 AuthScope.USER_READ_WHISPERS, AuthScope.USER_MANAGE_WHISPERS]
moderators = ("563919062", "659673020", "57231965", "755808445", "742401277", "659640208", "517351918", "195782134", "761241392", "588989623", "781923878", "82006620", "192918528", "872594380", "1211252085")


class BotSetup(Twitch):
    def __init__(self, app_id: str, app_secret: str):
        super().__init__(app_id, app_secret)
        self.bot = Twitch


class WebsocketsManager:
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

    def set_source_visibility(self, scene_name: str, source_name: str, source_visible: bool):
        response = self.ws.call(requests.GetSceneItemId(sceneName=scene_name, sourceName=source_name))
        item_id = response.datain['sceneItemId']
        self.ws.call(requests.SetSceneItemEnabled(sceneName=scene_name, sceneItemId=item_id, sceneItemEnabled=source_visible))

    def set_text(self, source_name: str, new_text: str):
        self.ws.call(requests.SetInputSettings(inputName=source_name, inputSettings={'text': new_text}))


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def read_file(file_name: str):
    with open(f"{data_path}{file_name}.txt", "r") as file:
        return file.read()


def write_file(file_name: str, to_write: any):
    with open(f"{data_path}{file_name}.txt", "w") as file:
        file.write(str(to_write))


async def flash_window(who: str):
    def refresh_ffreq_fsped():
        flash_speed = read_file("flash_speed")
        flash_frequency = read_file("flash_frequency")
        return int(flash_frequency), float(flash_speed)

    flash_frequency, flash_speed = refresh_ffreq_fsped()
    if who == "chody":
        os.system("color 27"), time.sleep(flash_speed)
        for x in range(1, flash_frequency):
            os.system("color 07"), time.sleep(flash_speed)
            os.system("color 27"), time.sleep(flash_speed)
        os.system("color 07"), time.sleep(5)
    elif who == "mystery":
        os.system(f"color 17"), time.sleep(flash_speed)
        os.system(f"color 47"), time.sleep(flash_speed)
        for x in range(1, flash_frequency):
            os.system("color 07"), time.sleep(flash_speed / 2)
            os.system(f"color 17"), time.sleep(flash_speed)
            os.system(f"color 47"), time.sleep(flash_speed)
        os.system("color 07"), time.sleep(5)


def refresh_goal_total():
    cash_goal = read_file("cash_goal")
    cash_total = read_file("cash_total")
    return int(cash_goal), int(cash_total)


def time_left():
    return str(datetime.datetime.strptime(read_file("time_end"), time_format) - datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), time_format)).title()


def bet_cashapp(cash_total, cash_goal):
    return f"CashApp Bet\n${int(cash_total):,}/${int(cash_goal):,}\n$roningt81"


async def shutdown():
    try:
        obs.set_source_visibility(obs_scene_name, obs_source_name, False)
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
        await bot.send_chat_message(id_streamer, id_streamer, f"Make sure the command is valid eh? !betcashapp add/remove/change(end/goal/total) x", reply_parent_message_id=message_id)
        return True

    if data.event.message.text.startswith("!betcashapp"):
        message_id = data.event.message_id
        try:
            cash_goal, cash_total = refresh_goal_total()
            if data.event.chatter_user_id in (id_streamer, "268136120"):
                add = True
                error = False
                change = None
                msg = data.event.message.text.replace(" ", "")
                amount = msg.removeprefix("!betcashapp")
                if amount.startswith("add"):
                    amount = amount.removeprefix("add")
                    if amount.isdigit():
                        cash_total += int(amount)
                        write_file("cash_total", cash_total)
                    else:
                        error = await send_error_msg(message_id)
                elif amount.startswith("remove"):
                    add = False
                    amount = amount.removeprefix("remove")
                    if amount.isdigit():
                        cash_total -= int(amount)
                        write_file("cash_total", cash_total)
                    else:
                        error = await send_error_msg(message_id)
                elif amount.startswith("change"):
                    amount = amount.removeprefix("change")
                    if amount.startswith("goal"):
                        change = "goal"
                        amount = amount.removeprefix("goal")
                        if amount.isdigit():
                            write_file("cash_goal", amount)
                            cash_goal, cash_total = refresh_goal_total()
                        else:
                            error = await send_error_msg(message_id)
                    elif amount.startswith("total"):
                        change = "total"
                        amount = amount.removeprefix("total")
                        if amount.isdigit():
                            write_file("cash_total", amount)
                            cash_goal, cash_total = refresh_goal_total()
                        else:
                            error = await send_error_msg(message_id)
                    elif amount.startswith("end"):
                        change = "end"
                        try:
                            new_end = datetime.datetime.strptime(data.event.message.text.removeprefix("!betcashapp change end "), time_format)
                        except Exception as g:
                            await bot.send_chat_message(id_streamer, id_streamer, f"Error translating new end date -- {g if g != '' else 'NO ERROR MESSAGE...'}")
                            return
                        write_file("time_end", new_end)
                    else:
                        error = await send_error_msg(message_id)
                else:
                    error = await send_error_msg(message_id)
                if change is None and not error:
                    remaining = int(cash_goal - cash_total)
                    obs.set_text(obs_source_name, bet_cashapp(cash_total, cash_goal))
                    await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; ${amount} {'contributed' if add else 'removed due to correction'}; ${f'{remaining:,} Remaining' if remaining >= 0 else f'{abs(remaining):,} Extra for Ronin'}; Time Left: {time_left()}.", reply_parent_message_id=message_id)
                elif change is not None and not error:
                    remaining = int(cash_goal - cash_total)
                    obs.set_text(obs_source_name, bet_cashapp(cash_total, cash_goal))
                    if change == "goal":
                        await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; New Goal Set @ ${int(cash_goal):,}; ${f'{remaining:,} Remaining' if remaining >= 0 else f'{abs(remaining):,} Extra for Ronin'}; Time Left: {time_left()}.", reply_parent_message_id=message_id)
                    elif change == "total":
                        await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; New Total Contributed Set @ ${int(cash_total):,}; ${f'{remaining:,} Remaining' if remaining >= 0 else f'{abs(remaining):,} Extra for Ronin'}; Time Left: {time_left()}.", reply_parent_message_id=message_id)
                    elif change == "end":
                        await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; New End Date Set: {read_file('time_end')}; New Time Remaining: {time_left()}; ${f'{remaining:,} Remaining' if remaining >= 0 else f'{abs(remaining):,} Extra for Ronin'}")
            elif data.event.chatter_user_id in moderators:
                await bot.send_chat_message(id_streamer, id_streamer, f"This command is restricted to RoninGT and TheeChody temporarily", reply_parent_message_id=message_id)
            else:
                cash_goal, cash_total = refresh_goal_total()
                remaining = int(cash_goal - cash_total)
                await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; ${f'{remaining:,} Remaining' if remaining >= 0 else f'{abs(remaining):,} Extra for Ronin'}; Time Left: {time_left()}.", reply_parent_message_id=message_id)
        except Exception as f:
            await bot.send_chat_message(id_streamer, id_streamer, f"A error has occurred -- {f if f != '' else 'NO ERROR MESSAGE...'}", reply_parent_message_id=message_id)
            return


async def on_whisper(data: UserWhisperMessageEvent):
    if data.event.from_user_id == "268136120":  # "1023291886"
        await flash_window("chody")
    elif data.event.from_user_id == "1211252085":
        await flash_window("mystery")


async def run():
    twitch_helper = UserAuthenticationStorageHelper(bot, target_scopes)
    await twitch_helper.bind()

    event_sub = EventSubWebsocket(bot)
    event_sub.start()

    await event_sub.listen_channel_chat_message(id_streamer, id_streamer, on_stream_message)
    await event_sub.listen_user_whisper_message(id_streamer, on_whisper)

    while True:
        cls()
        try:
            option = input("Enter 1 to message remaining goal & time left\nEnter 2 to ADD to CashApp balance\nEnter 3 to REMOVE from CashApp balance\nEnter 4 to change goal\nEnter 5 to change total contributed\nEnter 6 to change bet time limit\nEnter 7 to change flash settings\nEnter 0 to exit program\n")
            cls()
            cash_goal, cash_total = refresh_goal_total()
            if option not in ('0', '1', '2', '3', '4', '5', '6', '7'):
                print("Please make a valid choice"), time.sleep(2)
            elif option == "0":
                print("Exiting program..\nProgram will close in 2 seconds"), time.sleep(2)
                await shutdown()
            elif option == "1":
                remaining = int(cash_goal - cash_total)
                await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; ${f'{remaining:,} Remaining' if remaining >= 0 else f'{abs(remaining):,} Extra for Ronin'}; Time Left: {time_left()}.")
            elif option == "2":
                while True:
                    cash_add = input("Enter cash to ADD to total gathered;\n")
                    if not cash_add.isdigit():
                        print(f"Not Valid, try again.. (hINT)"), time.sleep(2), cls()
                    else:
                        cash_total += int(cash_add)
                        write_file("cash_total", cash_total)
                        remaining = int(cash_goal - cash_total)
                        obs.set_text(obs_source_name, bet_cashapp(cash_total, cash_goal))
                        await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; ${cash_add} contributed; ${f'{remaining:,} Remaining' if remaining >= 0 else f'{abs(remaining):,} Extra for Ronin'}; Time Left: {time_left()}.")
                        break
            elif option == "3":
                while True:
                    cash_remove = input("Enter cash to REMOVE from total gathered;\n")
                    if not cash_remove.isdigit():
                        print(f"Not Valid, try again.. (hINT)"), time.sleep(2), cls()
                    else:
                        cash_total -= int(cash_remove)
                        write_file("cash_total", cash_total)
                        remaining = int(cash_goal - cash_total)
                        obs.set_text(obs_source_name, bet_cashapp(cash_total, cash_goal))
                        await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; ${cash_remove} removed due to correction; ${f'{remaining:,} Remaining' if remaining >= 0 else f'{abs(remaining):,} Extra for Ronin'}; Time Left: {time_left()}.")
                        break
            elif option == "4":
                while True:
                    new_goal = input("Enter thee new Goal Value;\n")
                    if not new_goal.isdigit():
                        print(f"Not Valid, try again.. (hINT)"), time.sleep(2), cls()
                    else:
                        write_file("cash_goal", new_goal)
                        remaining = int(int(new_goal) - cash_total)
                        obs.set_text(obs_source_name, bet_cashapp(cash_total, new_goal))
                        await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; New Goal Set: ${int(new_goal):,}; ${f'{remaining:,} Remaining' if remaining >= 0 else f'{abs(remaining):,} Extra for Ronin'}; Time Left: {time_left()}.")
                        break
            elif option == "5":
                while True:
                    new_total = input("Enter thee new Total Contributed Value;\n")
                    if not new_total.isdigit():
                        print(f"Not Valid, try again.. (hINT)"), time.sleep(2), cls()
                    else:
                        write_file("cash_total", new_total)
                        remaining = int(cash_goal - int(new_total))
                        obs.set_text(obs_source_name, bet_cashapp(new_total, cash_goal))
                        await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; New Total Contributed Set: ${int(new_total):,}; ${f'{remaining:,} Remaining' if remaining >= 0 else f'{abs(remaining):,} Extra for Ronin'}; Time Left: {time_left()}.")
                        break
            elif option == "6":
                while True:
                    try:
                        new_end = input("Input end date; YYYY-mm-dd HH:MM:SS\n")
                        new_end = datetime.datetime.strptime(new_end, time_format)
                        break
                    except Exception as f:
                        print(f"Not Valid, try again -- {f if f != '' else 'NO ERROR MESSAGE...'}"), time.sleep(10), cls()
                write_file("time_end", new_end)
                remaining = int(cash_goal - cash_total)
                obs.set_text(obs_source_name, bet_cashapp(cash_total, cash_goal))
                await bot.send_chat_message(id_streamer, id_streamer, f"CashApp Bet Update; New End Date Set: {str(new_end)}; New Time Remaining: {time_left()}; ${f'{remaining:,} Remaining' if remaining >= 0 else f'{abs(remaining):,} Extra for Ronin'}.")
            elif option == "7":
                while True:
                    # cls()
                    option = input("Enter 1 to change FREQUENCY\nEnter 2 to change SPEED\nEnter 0 to return to Main Menu\n")
                    cls()
                    if option not in ('0', '1', '2'):
                        print("Please make a valid choice"), time.sleep(2)
                    elif option == "0":
                        print("Going back to Main Menu.."), time.sleep(2)
                        break
                    elif option == "1":
                        while True:
                            new_frequency = input("Enter new desired FREQUENCY;\n")
                            if not new_frequency.isdigit():
                                print(f"Not Valid, try again.. (hINT)"), time.sleep(2), cls()
                            else:
                                write_file("flash_frequency", new_frequency), cls()
                                break
                    elif option == "2":
                        while True:
                            new_speed = input("Enter new desired SPEED (float);\n")
                            try:
                                float(new_speed)
                                write_file("flash_speed", new_speed), cls()
                                break
                            except ValueError:
                                print(f"Not Valid, try again"), time.sleep(2), cls()
                    else:
                        print(f"IDK what key you pressed, but that wasn't valid -- '{option}' was pressed"), time.sleep(5)
            else:
                print(f"IDK what key you pressed, but that wasn't valid -- '{option}' was pressed"), time.sleep(5)
        except Exception as e:
            print(f"Error occurred -- {e if e != '' else 'NO ERROR MESSAGE...'}\nProgram will close in 30 sec, or close program manually"), time.sleep(30)
            await shutdown()


if __name__ == "__main__":
    trigger = ""
    twitch_client = read_file("twitch_client")
    if twitch_client == "":
        trigger += "twitch_client\n"
    twitch_secret = read_file("twitch_secret")
    if twitch_secret == "":
        trigger += "twitch_secret\n"
    obs_host = read_file("obs_host")
    if obs_host == "":
        trigger += "obs_host\n"
    obs_port = read_file("obs_port")
    if obs_port == "":
        trigger += "obs_port\n"
    obs_pass = read_file("obs_pass")
    if obs_pass == "":
        trigger += "obs_pass\n"
    obs_scene_name = read_file("obs_scene_name")
    if obs_scene_name == "":
        trigger += "obs_scene_name\n"
    obs_source_name = read_file("obs_source_name")
    if obs_source_name == "":
        trigger += "obs_source_name\n"
    if trigger != "":
        print(f"Please make sure all the files have the appropriate keys please\n\n\n{trigger}\nis(are) empty!\nProgram will close in 30 seconds, or close program manually"), time.sleep(30)
        os._exit(1)

    bot = BotSetup(twitch_client, twitch_secret)
    obs = WebsocketsManager()

    connect = obs.connect()
    if not connect:
        print("Error Establishing OBS Connection!! Program will close in 5 sec"), time.sleep(5)
        os._exit(1)

    try:
        initialize = input("Initialize program? Y/N\n")
        if initialize.lower() in ("y", "yes"):
            initialize = True
        else:
            initialize = False
        cls()
        if initialize:
            cash_total = 0
            time_start = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), time_format)
            while True:
                try:
                    time_end = input("Input end date; YYYY-mm-dd HH:MM:SS\n")
                    time_end = datetime.datetime.strptime(time_end, time_format)
                    break
                except Exception as f:
                    print(f"Not Valid, try again -- {f}"), time.sleep(5), cls()
            write_file("time_start", time_start)
            write_file("time_end", time_end)
            while True:
                cash_goal = input("Enter CashApp Goal Value\n")
                if not cash_goal.isdigit():
                    print(f"Not Valid, try again.. (hINT)"), time.sleep(2), cls()
                else:
                    break
            write_file("cash_goal", cash_goal)
            write_file("cash_total", 0)
        else:
            time_start = datetime.datetime.strptime(read_file("time_start"), time_format)
            time_end = datetime.datetime.strptime(read_file("time_end"), time_format)
            cash_goal = int(read_file("cash_goal"))
            cash_total = int(read_file("cash_total"))
        cls()
        obs.set_text(obs_source_name, bet_cashapp(cash_total, cash_goal))
        obs.set_source_visibility(obs_scene_name, obs_source_name, True)
        print(f"{'Initialization' if initialize else 'Files Loaded'} successful{'ly' if not initialize else ''}!\nTime Start{'ed' if not initialize else ''}; {time_start}\nTime End; {time_end}\nTime Till End; {time_left()}"), time.sleep(2)
    except KeyboardInterrupt:
        cls()
        print("Exiting program..\nProgram will close in 2 sec"), time.sleep(2)
        asyncio.run(shutdown())
    except Exception as e:
        print(f"Error occurred -- {e if e != '' else 'NO ERROR MESSAGE...'}\nProgram will close in 30 sec, or close program manually"), time.sleep(30)
        asyncio.run(shutdown())

    asyncio.run(run())
