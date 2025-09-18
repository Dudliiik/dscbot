import discord
import time
from discord.ext import commands
from discord.utils import get

help_cooldowns={}

class Help(commands.Cog):
    def __init__(self, client):
        self.client = client

    
    @commands.command()
    async def help(self, ctx):
        help_role = get(ctx.guild.roles, name="Help")
        if help_role is None:
            await ctx.send("Role 'Help' doesn't exist!")
            return
        
        now = time.time()
        user_id = ctx.author.id
        last_used = help_cooldowns.get(user_id, 0)
        cooldown_seconds = 7200

        if now - last_used < cooldown_seconds:
            remaining = cooldown_seconds - (now - last_used)
            
            h = int(remaining // 3600)
            m = int(remaining % 3600 // 60)
            s = int(remaining % 60)
            await ctx.send(f"You can ping Help again in {h}h {m}m {s}s!")
            return
        
        help_cooldowns[user_id] = now
        
        await ctx.send(content=f"{help_role.mention}")

async def setup(client):
    await client.add_cog(Help(client))