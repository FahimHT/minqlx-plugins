import minqlx
import requests
import threading
import discord
from discord.ext import commands
import asyncio
import json


VERSION = "1.1"


class AsyncBot(commands.Cog):
    def __init__(self, bot, discord_plugin):
        self.bot = bot
        self.discord_plugin = discord_plugin


    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if await self.bot.is_owner(ctx.message.author):
            server = self.discord_plugin.get_server_name() or "N/A"
            content = "{}\n>>> {}".format(server, error)
            await ctx.send(content)


    @commands.command(name="ql")
    async def send_server_status(self, ctx):
        content = self.discord_plugin.get_server_status()
        await ctx.send(content)


    @commands.command(name="ver")
    async def check_version(self, ctx):
        content = self.discord_plugin.check_version()
        await ctx.send(content)


class BotThread(threading.Thread):
    def __init__(self, discord_plugin):
        super().__init__(daemon=True)
        self.name = "Discord-bot-client thread"
        self.discord_plugin = discord_plugin
    

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        intents = discord.Intents.default()
        intents.messages = True
        self.async_bot = commands.Bot(command_prefix='.', loop=loop, intents=intents)
        self.async_bot.add_cog(AsyncBot(self.async_bot, self.discord_plugin))
        loop.run_until_complete(self.async_bot.start(self.discord_plugin.discord_bot_token))
        

class discordbot(minqlx.Plugin):
    def __init__(self):
        self.set_cvar_once("qlx_discord_channel_id", "")
        self.set_cvar_once("qlx_discord_chat_channel_id", "")
        self.set_cvar_once("qlx_discord_bot_token", "")

        self.discord_channel_id_str = self.get_cvar("qlx_discord_channel_id")
        self.discord_chat_channel_id_str = self.get_cvar("qlx_discord_chat_channel_id")
        self.discord_bot_token = self.get_cvar("qlx_discord_bot_token")
        self.command_prefix = self.get_cvar("qlx_commandPrefix") or "!"
        self.discord_cmd_prefix = self.command_prefix + "discord"

        if not self.discord_bot_token:
            self.msg("^3Please set qlx_discord_bot_token.")
            return

        self.lock = threading.RLock()
        self.player_names = set()
        
        self.bot_thread = BotThread(self)
        self.bot_thread.start()

        self.add_hook("game_start", self.handle_game_start)
        self.add_hook("game_end", self.handle_game_end)
        self.add_hook("player_connect", self.handle_player_connect)
        self.add_hook("player_disconnect", self.handle_player_disconnect)
        self.add_hook("chat", self.handle_chat)
        self.add_hook("unload", self.handle_unload)
        self.add_hook("player_loaded", self.handle_player_loaded)

        self.add_command("discord", self.cmd_to_discord, usage="<message>")

        if self.discord_channel_id_str:
            self.discord_channel_ids = {item for item in self.discord_channel_id_str.split(',') if item.strip()}
        else:
            self.msg("^3Please set qlx_discord_channel_id.")

        if self.discord_chat_channel_id_str:
            self.discord_chat_channel_ids = {item for item in self.discord_chat_channel_id_str.split(',') if item.strip()}
        

    def handle_game_end(self, *args, **kwargs):
        with self.lock:
            content = "Game ended."
            if self.game.red_score is not None and self.game.blue_score is not None:
                if self.game.red_score >= 0 and self.game.blue_score >= 0:
                    content += " Result: Red {} - Blue {}.".format(self.game.red_score, self.game.blue_score)
            self.send_message(self.discord_channel_ids, content)


    def handle_chat(self, player, msg, channel):
        with self.lock:
            if self.discord_chat_channel_id_str and ("chat" == channel.name or "spectator_chat" == channel.name):
                message = self.clean_text(msg)
                if not message.startswith(self.discord_cmd_prefix):
                    content = "{} says: {}".format(self.clean_text(player.name), message)
                    self.send_message(self.discord_chat_channel_ids, content)


    def handle_player_connect(self, player):
        with self.lock:
            player_name = self.clean_text(player.name)

            if player_name not in self.player_names:
                self.player_names.add(player_name)
                content = "{} connected. Current players: {}.".format(player_name, len(self.player_names))
                self.send_message(self.discord_channel_ids, content)


    def handle_player_disconnect(self, player, reason):
        with self.lock:
            player_name = self.clean_text(player.name)

            if player_name in self.player_names:
                self.player_names.discard(player_name)
                content = "{} disconnected. Current players: {}.".format(player_name, len(self.player_names))
                self.send_message(self.discord_channel_ids, content)


    def handle_game_start(self, *args, **kwargs):
        with self.lock:
            if self.players() is not None:
                self.player_names = {self.clean_text(x.name) for x in self.players()}
                content = "Game started, map: {}, players: {}.".format(self.game.map_title, len(self.player_names))
                self.send_message(self.discord_channel_ids, content)


    def handle_unload(self, plugin):
        asyncio.run_coroutine_threadsafe(self.bot_thread.async_bot.change_presence(status=discord.Status.offline), loop=self.bot_thread.async_bot.loop)
        asyncio.run_coroutine_threadsafe(self.bot_thread.async_bot.close(), loop=self.bot_thread.async_bot.loop)
    

    def cmd_to_discord(self, player, msg, channel):
        with self.lock:
            if len(msg) < 2:
                return minqlx.RET_USAGE

            message = " ".join(msg[1:])
            content = "{} says: {}".format(self.clean_text(player.name), self.clean_text(message))
            self.send_message(self.discord_channel_ids, content)


    def get_server_status(self):
        count = len(self.players())
        game_state = self.game.state.capitalize().replace("_", " ")
        content = "Server: {}\n>>> Map: {}, Status: {}\nPlayers: {}".format(self.game.hostname, self.game.map_title, game_state, count)

        if count > 0:
            names = {self.clean_text(x.name) for x in self.players()}
            content += ", (" + ", ".join(names) + ")"
        content += "\n"
        return content


    @minqlx.delay(5)
    @minqlx.thread
    def handle_player_loaded(self, player):
        if player.steam_id == minqlx.owner():
            self.check_version(player=player)


    # Adapted from https://github.com/BarelyMiSSeD/minqlx-plugins/blob/master/listmaps.py
    def check_version(self, player=None):
        with self.lock:
            server = "Server: {}\n".format(self.game.hostname)
            content = "{}>>> Could not retrieve {} version from repository".format(server, self.__class__.__name__)
            url = "https://raw.githubusercontent.com/FahimHT/minqlx-plugins/master/discordbot.py"
            res = requests.get(url)

            if requests.codes.ok != res.status_code:
                return "{}, response: {}".format(content, res.status_code)
            
            try:
                for line in res.iter_lines():
                    if line.startswith(b"VERSION"):
                        line = line.replace(b"VERSION = ", b"")
                        line = line.replace(b"\"", b"")
                        
                        if VERSION.encode() != line:
                            msg1 = "{} current version {} is different from repository version {}".format(self.__class__.__name__, VERSION, line.decode())
                            msg2 = "See https://github.com/FahimHT/minqlx-plugins"
                            
                            if player:
                                player.tell(msg1)
                                player.tell(msg2)
                            
                            content = "{}>>> {}\n{}".format(server, msg1, msg2)
                            return content
                        else:
                            content = "{}>>> Currently running {} version {} (latest)".format(server, self.__class__.__name__, VERSION)
                            return content
            except Exception as e:
                message = "{}, message: {}".format(content, e)
                minqlx.console_print(message)
                return message

            return content


    def get_server_name(self):
        return self.game.hostname
                      

    @minqlx.thread
    def send_message(self, channel_id, message):
        if channel_id and message:
            for channel in channel_id:
                requests.post("https://discordapp.com/api/channels/" + channel + "/messages",
                              data=json.dumps({'content': message}),
                              headers={'Content-type': 'application/json',
                                       'Authorization': 'Bot ' + self.discord_bot_token})
