import discord
from discord.ext import commands
from dotenv import load_dotenv
from discord.utils import get
import os
import asyncio
from flask import Flask
from threading import Thread


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

GUILD_ID = 1417123832862474262

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

# ---------------- Bot event ----------------

BOLD = '\033[1m'

@client.event
async def on_ready():
    print(BOLD + f"Logged in as {client.user}")
    synced = await client.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Slash commands synced: {len(synced)} Commands")

#------------------------ VIP+ ------------------------

@client.event
async def on_member_update(before, after):
    if getattr(before, "premium_subscription_count", 0) < 2 and getattr(after, "premium_subscription_count", 0) >= 2:
        role = discord.utils.get(after.guild.roles, name="VIP+")
        if role:
            await after.add_roles(role)
    
# ---------------- Persistent TicketView ----------------

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # persistent

    @discord.ui.button(label="✅ Accept & Close", style=discord.ButtonStyle.green, custom_id="accept_close")
    async def accept_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title=(f"{interaction.user.name} has accepted ticket closure."),
            description="This ticket has been closed and will be deleted shortly.",
            color=discord.Colour.dark_blue()
        )

        if not is_ticket_channel(interaction.channel):
            await interaction.response.send_message("This button can only be used in ticket channels.", ephemeral=True)
            return
        await interaction.response.send_message(embed=embed, ephemeral=False)
        await asyncio.sleep(2)
        await interaction.channel.delete()


    @discord.ui.button(label="❌ Deny & Keep Open", style=discord.ButtonStyle.gray, custom_id="deny_keep")
    async def deny_keep(self, interaction: discord.Interaction, button: discord.ui.Button):
     if not is_ticket_channel(interaction.channel):
        await interaction.response.send_message(
            "This button can only be used in ticket channels.", ephemeral=True)
        return
     await interaction.response.send_message(
        content=f"{interaction.user.mention} has denied the ticket closure.", ephemeral=False)
     await interaction.message.delete()
        
# ---------------- Helper Function ----------------

def is_ticket_channel(channel: discord.abc.GuildChannel):
    ticket_prefixes = ["partnership-", "support-", "role-request-"]
    return any(channel.name.startswith(prefix) for prefix in ticket_prefixes)

# ---------------- /closerequest command ----------------

@client.tree.command(
    name="closerequest",
    description="Sends a message asking the user to confirm the ticket is able to be closed.",
    guild=discord.Object(id=GUILD_ID)
)
@discord.app_commands.checks.has_permissions(administrator=True)
async def closerequest(interaction: discord.Interaction):
    if not is_ticket_channel(interaction.channel):
        await interaction.response.send_message("You can only use this command in ticket channels.", ephemeral=True)
        return

    embed = discord.Embed(
        title="Close Request",
        description=f"{interaction.user.mention} has requested to close this ticket.\n\nPlease accept or deny using the buttons below.",
        color=discord.Color.green()
    )

    await interaction.response.send_message(interaction.user.mention, embed=embed, view=CloseTicketView())

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
    embed = discord.Embed(description=f"Purged {real_deleted} messages", color=discord.Colour.red())
    await interaction.channel.send(embed=embed, delete_after=4)

# ---------------- Run bot + web ----------------

async def main():
    async with client:
        await load_cogs()
        await client.start(TOKEN)

if __name__ == "__main__":
    Thread(target=run_web).start()
    asyncio.run(main())