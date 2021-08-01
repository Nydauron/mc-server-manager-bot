import discord
from discord.ext import commands, tasks
import subprocess
import fcntl
import os
from serverinfo import get_server_info

def non_block_read(output):
    fd = output.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    try:
        return output.read()
    except:
        return ""
        
class ServerAlreadyRunning(commands.CommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
class ServerNotRunning(commands.CommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class MinecraftServerManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.proc_server = None
        self.verbose = False
        self.stdout_buf = ""
        self.webhook = None
        print(f"Loaded {self.qualified_name} cog")
    
    def cog_unload(self):
        print("Shutting down server")
        self.bot.loop.run_until_complete(self.stop_server())
    
    @tasks.loop(seconds=1.0)
    async def check_stdout(self):
        if self.proc_server:
            self.stdout_buf += non_block_read(self.proc_server.stdout)
            if self.stdout_buf != "":
                buf_split = self.stdout_buf.rsplit('\n', 1)
                
                if self.verbose:
                    await self.split_message_length(buf_split[0])
                else:
                    print("help")
                    print(buf_split[0])
                self.stdout_buf = buf_split[1]
    
    async def split_message_length(self, msg):
        i = 0
        msg_len = len(msg)
        while i < msg_len:
            try:
                line_idx = msg[i:min(i+2000, msg_len)].rindex('\n')
                msg_to_send = msg[i:line_idx]
                inc_i = line_idx + 1
            except ValueError:
                msg_to_send = msg[i:min(i+2000, msg_len)]
                inc_i = 2001
            if msg_to_send != "":
                print(msg_to_send)
                await self.webhook.send(msg_to_send)
            else:
                print("WARNING: TRIED TO SEND BLANK MSG!")
            i += inc_i
    
    @tasks.loop(seconds=5.0)
    async def update_info(self):
        from config import SERVER_IP
        if self.proc_server:
            try:
                server_info_json = get_server_info("localhost", 25565)
            except ConnectionRefusedError:
                print("Failed to get server info")
                return
            
            await self.bot.change_presence(status = discord.Status.online,
                                            activity=discord.Game(f"{server_info_json['version']['name']} ({server_info_json['players']['online']}/{server_info_json['players']['max']}) @ {SERVER_IP}"))
    
    @commands.command()
    async def start(self, ctx, verbose : bool = False):
        from config import BASH_COMMAND, SERVER_DIRECTORY
        if self.proc_server:
            raise ServerAlreadyRunning()
        msg = await ctx.reply(f"Starting the server with verbose set to {verbose}...")
        
        await ctx.trigger_typing()
        self.proc_server = subprocess.Popen(BASH_COMMAND,
                                            stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE,
                                            cwd=SERVER_DIRECTORY,
                                            text=True)
        self.verbose = verbose
        try:
            with open("grass.png", "rb") as f:
                self.webhook = await ctx.channel.create_webhook(name="Minecraft Server", avatar=f.read())
        except commands.errors.CommandInvokeError:
            self.webhook = ctx.channel
        
        self.check_stdout.start()
        self.update_info.start()
    
    @commands.command()
    async def verbose(self, ctx):
        if not self.proc_server:
            raise ServerNotRunning()
        
        self.verbose ^= True
        
        await ctx.reply(f"Verbose now set to {self.verbose}.")
            
        
    @commands.command(name="mc")
    async def send_mc_command(self, ctx, *, cmd : str):
        if not self.proc_server:
            raise ServerNotRunning()
        
        if cmd.partition(' ')[0] not in ['say', 'kick', 'ban', 'ban-ip', 'unban', 'whitelist', 'stop', 'restart']:
            print(f"`{cmd}` is not allowed.")
            await ctx.message.add_reaction(	u"\U0001F44E")
            return
        
        self.proc_server.stdin.write(f"{cmd}\n")
        self.proc_server.stdin.flush()
        await ctx.message.add_reaction(u"\U0001F44D")
        
    @commands.command()
    async def stop(self, ctx):
        if not self.proc_server:
            raise ServerNotRunning()
        await ctx.reply("Stopping the server ...")
        await ctx.trigger_typing()
        await self.stop_server()
        if self.stdout_buf != "":
            await ctx.send(self.stdout_buf)
            self.stdout_buf = ""
        await ctx.send("https://media1.tenor.com/images/e5109be83829f625fb13c73303457689/tenor.gif")
        
    async def stop_server(self):
        if self.proc_server:
            self.check_stdout.cancel()
            self.update_info.cancel()
            (data, errs) = self.proc_server.communicate(input="stop\n")
            print(data)
            if self.verbose:
                await self.split_message_length(data)
            else:
                print(buf_split[0])
            self.proc_server.wait()
            self.proc_server = None
            await self.webhook.delete(reason="Stopping MC Server")
            self.webhook = None
            await self.bot.change_presence(status = discord.Status.idle)
            

def setup(bot):
    bot.add_cog(MinecraftServerManager(bot))