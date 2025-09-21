import discord
from discord.ext import commands
from dotenv import load_dotenv
from discord.utils import get
import os
import asyncio
from flask import Flask
from threading import Thread
from cogs.tickets import CloseTicketView


# ---------------- Load .env ----------------

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ---------------- Flask ----------------

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ---------------- Discord bot ----------------

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ---------------- Load cogs ----------------

async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"cogs.{filename[:-3]}")


# ---------------- /shutdown command ----------------

GUILD_ID = 1415013619246039082

@client.tree.command(
        name="shutdown", 
        description="Shuts down the bot.",
        guild=discord.Object(id=GUILD_ID)
        )
async def shutdown(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "Only users with permissions can toggle this command", ephemeral=True)
        return
    await interaction.response.send_message("🛑 Shut down the bot...", ephemeral=False)
    await client.close()

#------------------------ VIP+ ------------------------

@client.event
async def on_member_update(before, after):
    if getattr(before, "premium_subscription_count", 0) < 2 and getattr(after, "premium_subscription_count", 0) >= 2:
        role = discord.utils.get(after.guild.roles, name="VIP+")
        if role:
            await after.add_roles(role)

# ---------------- Bot event ----------------

BOLD = '\033[1m'

@client.event
async def on_ready():
    print(BOLD + f"Logged in as {client.user}")
    synced = await client.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Slash commands synced: {len(synced)} Commands")
    client.add_view(CloseTicketView())

# ----------------------- /role give command  ----------------------- 

@client.tree.command(
    name="role",
    description="Adds a role to a member.",
    guild=discord.Object(id=GUILD_ID)
)
@discord.app_commands.checks.has_permissions(administrator=True)
async def addRole(interaction: discord.Interaction, user: discord.Member, role: discord.Role):
    await interaction.response.defer()

    if role in user.roles:
        await interaction.followup.send(f"{user.mention} already has the role {role.name}")
    else:
        await user.add_roles(role)
        await interaction.followup.send(f"Added {role.name} to {user.mention}!")

# ----------------------- /role remove command  ----------------------- 

@client.tree.command(
    name="remove",
    description="Removes a role from a member.",
    guild=discord.Object(id=GUILD_ID)
)
@discord.app_commands.checks.has_permissions(administrator=True)
async def removeRole(interaction: discord.Interaction, user: discord.Member, role: discord.Role):
    await interaction.response.defer()
    await user.remove_roles(role)
    await interaction.followup.send(f"Removed {role.name} from {user.mention}!")

# ------------------ /purge command ----------------------------

@client.tree.command(
    name="purge",
    description="Clears messages",
    guild=discord.Object(id=GUILD_ID)
)
@discord.app_commands.checks.has_permissions(administrator=True)
async def purge(interaction: discord.Interaction, amount: int):
    await interaction.response.defer()
    deleted = await interaction.channel.purge(limit=amount+1)
    real_deleted = max(len(deleted) - 1, 0)
    await interaction.channel.send(f"Purged {real_deleted} messages", delete_after=4)

# ---------------- Run bot + web ----------------

async def main():
    async with client:
        await load_cogs()
        await client.start(TOKEN)

if __name__ == "__main__":
    Thread(target=run_web).start()
    asyncio.run(main())