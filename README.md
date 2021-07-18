# MC Server Manager Bot

A Discord bot that helps you manage your Minecraft server within Discord.

## Installation

- Create a new folder inside the directory of where your Minecraft server will be located.
- Clone or download/extract this repo to the new folder

### Setup
There is a template config file that you will need to setup before running the
bot for the first time. Below is a list of all the settings in the config file:

| Setting | Responsible For |
|---|---|
| BOT_TOKEN | The token of your bot. You will need to create a new application by going to [the Discord Development Portal](https://discord.com/developers/applications). From there, go to the Bot tab, add it to the app, and copy the token field that is hidden until clicked. **DO NOT SHARE THIS TOKEN!** |
| BOT_PREFIX | The prefix that the bot will use to respond to commands. |
| SERVER_IP | This hopefully will become obsolete, but this is simply the external host/IP. |
| SERVER_DIRECTORY | A relative or absolute path to the directory where the server is. (Most likely will be ".." if you created the new folder inside your server directory.) |
| BASH_COMMAND | An array that contains the process and necessary arguments that will be run to launch the server. |

Install the dependencies to your virtual environment by doing `pip install -r requirements.txt`.

Run the bot simply by typing `python app.py`. 

## Commands

- `!start`: Starts the server. All logging will be sent to the same channel as which the command was sent in.
- `!stop`: Stops the server.
- `!mc <Minecraft command>`: Sends a command to the server.
  - As of right now, it is hardcoded to only accept commands `kick`, `ban`, `ban-ip`, `unban`, `whitelist`, `stop`, and `restart`.

