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
        return output.readline()
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
        self.output_channel = None
        print(f"Loaded {self.qualified_name} cog")
    
    def cog_unload(self):
        print("Shutting down server")
        self.bot.loop.run_until_complete(self.stop_server())
    
    @tasks.loop(seconds=1.0)
    async def check_stdout(self):
        if self.proc_server:
            buf = non_block_read(self.proc_server.stdout)
            if buf != "":
                print(buf, end="")
                await self.output_channel.send(buf)
                
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
    async def start(self, ctx):
        from config import BASH_COMMAND, SERVER_DIRECTORY
        if self.proc_server:
            raise ServerAlreadyRunning()
        msg = await ctx.reply("Starting the server ...")
        self.output_channel = ctx.channel
        await ctx.trigger_typing()
        self.proc_server = subprocess.Popen(BASH_COMMAND,
                                            stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE,
                                            cwd=SERVER_DIRECTORY,
                                            text=True)
        msg.edit("Starting the server ... Started")
        
        self.check_stdout.start()
        self.update_info.start()
        
    @commands.command(name="mc")
    async def send_mc_command(self, ctx, *, cmd : str):
        print(cmd)
        
        if cmd.partition(' ')[0] not in ['kick', 'ban', 'ban-ip', 'unban', 'whitelist', 'stop', 'restart']:
            print("Not allowed :)")
        
        if not self.proc_server:
            raise ServerNotRunning()
        self.proc_server.stdin.write(f"{cmd}\n")
        self.proc_server.stdin.flush()
        
    @commands.command()
    async def stop(self, ctx):
        if not self.proc_server:
            raise ServerNotRunning()
        await ctx.reply("Stopping the server ...")
        await ctx.trigger_typing()
        await self.stop_server()
        await ctx.send("Stopped")
        
    async def stop_server(self):
        if self.proc_server:
            self.check_stdout.cancel()
            self.update_info.cancel()
            (data, errs) = self.proc_server.communicate(input="stop\n")
            print(data)
            for line in data.splitlines():
                await self.output_channel.send(line)
            self.proc_server.wait()
            self.proc_server = None
            await self.bot.change_presence(status = discord.Status.idle)
            

def setup(bot):
    bot.add_cog(MinecraftServerManager(bot))