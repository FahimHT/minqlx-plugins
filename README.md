# minqlx-plugins

## Requirements

The plug-in(s) are tested on the following python versions: `3.5.3, 3.7.3, 3.10.12, 3.11.4`.

Required libraries listed in `requirements.txt` should be installed by running the following command in the `minqlx-plugins` folder:
```
python3 -m pip install -r requirements.txt
```
## Setup

- Copy the plug-in `.py` file(s) to the **Quake Live Dedicated Server**'s `minqlx-plugins` folder.
- Add the plug-in(s) to the `qlx_plugins` cvar that specifies the list of plug-in to load for `minqlx`. Depending upon how the server is set-up, the cvar should be specified in one of the following locations: `autoexec.cfg`, `server.cfg`, as a command line parameter or in the `environment` section in `docker-compose.yml`.
  
  #### Example
  `autoexec.cfg` or `server.cfg`:
  ```
  set qlx_plugins "balance, docs, essentials, log, permission, plugin_manager, commands, listmaps, discordbot"
  ```
  Command line parameter or `docker-compose.yml`:
  ```
  QLX_PLUGINS="balance,docs,essentials,log,permission,plugin_manager,commands,listmaps,discordbot"
  ```
- Set the plug-in specific cvars if required.
- Restart the Server.


## Plug-in Specific Information

## Discord Bot

### Features
- Reports in game events, e.g., player connect/disconnect, game start/end, chat, in one or more specified Discord channels.
- Optionally relays all in-game chat (except team chat) to Discord.
- Allows players to post in Discord from inside the game using the `!discord` command.
  Example: `!discord @everyone please join!`
- Checks whether a newer version of the plug-in is available in the repository and informs when the server owner (set using the minqlx cvar `qlx_owner`) joins the game.
- Allows Discord channel members to view current game state using the `.ql` command.
- Allows members to check the deployed plug-in version using the `.ver` command.
- If an error occurs processing a command from the bot owner, the bot respond with an appropriate message.

### Setup
- [Create a Discord bot](https://discordpy.readthedocs.io/en/stable/discord.html) (remember to note down the bot token) and invite it to your server. 
- [Add the Message Content Intent](https://discordpy.readthedocs.io/en/latest/intents.html) for the bot (required for bot commands to works).
- Add the following plug-in cvars in `autoexec.cfg` or `server.cfg`.
- The `qlx_discord_bot_token` cvar is required.
- Specify a comma separated list of channels for the bot to post in.
  - The `qlx_discord_channel_id` is `required` for the bot to be able to post in-game events in Discord.
  - The `qlx_discord_chat_channel_id` is `optional`. Specify it only if you wish to relay all in-game chat (except team chat) to Discord.
  - The same channel can be specified in both `qlx_discord_channel_id` and `qlx_discord_chat_channel_id`.
  - To get a channel id, enable `Developer Mode` (`User Settings` (cog) > `Advanced`) in Discord. Now right click on the channel and select the `Copy Channel ID` option.

  ### Example
  ```
  // minqlx Plugin: DiscordBot
  set qlx_discord_bot_token "BOT_TOKEN"
  set qlx_discord_channel_id "CHANNEL_ID_1,CHANNEL_ID_2"
  set qlx_discord_chat_channel_id "CHANNEL_ID_1"
  ```
- Restart the server, the bot should come online shortly.
