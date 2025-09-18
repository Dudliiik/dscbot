import asyncio
import discord
from discord.ext import commands

# Close Button ---------------------------------

class CloseButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close", emoji="🔒", style=discord.ButtonStyle.gray)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Sure?",
            description="Are you sure about closing this ticket?",
            color=discord.Colour.dark_blue()
        )
        await interaction.response.send_message(embed=embed, view=Buttons(), ephemeral=True)

# Buttons --------------------------------------

class Buttons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

# Confirm Button -------------------------------

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.red)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(
            title="Ticket Closed",
            description="This ticket has been closed and will be deleted shortly.",
            color=discord.Colour.dark_blue()
        )
        await interaction.followup.send(embed=embed, ephemeral=False)

        async def delete_channel_later(channel):
            await asyncio.sleep(2)
            try:
                await channel.delete()
            except Exception as e:
                print(f"Failed to delete channel: {e}")

        asyncio.create_task(delete_channel_later(interaction.channel))

# Cancel Button --------------------------------

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await interaction.delete_original_response()
        self.stop()

# Ticket Categories ----------------------------

class TicketCategory(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Partnership", description="Open this only if your server follows our guidelines.", emoji="🎫"),
            discord.SelectOption(label="Role Request", description="Open this ticket to apply for an artist rankup.", emoji="⭐"),
            discord.SelectOption(label="Support", description="Open this ticket if you have any general queries.", emoji="📩")
        ]
        super().__init__(placeholder="Select a topic", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True) 
        await interaction.message.edit(view=TicketDropdownView())

        category = self.values[0]
        user = interaction.user

        categories = {
            "Partnership": {
                "title": "Partnership Ticket",
                "description": "Thanks {user.name} for contacting the partnership team of **Thumbnailers**!\n"
                                "Send your server's ad, and the ping you're expecting with any other additional details.\n"
                                "Our team will respond to you shortly.",
                "ping": [1136118197725171813, 1102975816062730291],
                "ping_user": True,
                "discord_category": "Partnership Tickets",
                "ticket_opened_category": "Partnership ticket"
            },
            "Role Request": {
                "title": "Role Request Ticket",
                "description": "Thank you for contacting support.\n"
                                "Please refer to <#1102968475925876876> and make sure you send the amount of thumbnails required for the rank you're applying for, as and when you open the ticket. "
                                "Make sure you link 5 minecraft based thumbnails at MINIMUM if you apply for one of the artist roles.",
                "ping": [1156543738861064192],
                "ping_user": False,
                "discord_category": "Role Request Tickets",
                "ticket_opened_category": "Role Request ticket"
            },
            "Support": {
                "title": "Support Ticket",
                "description": "Thanks {user.name} for contacting the support team of **Thumbnailers**!\n"
                                "Please explain your case so we can help you as quickly as possible!",
                "ping": [1102976554759368818, 1102975816062730291],
                "ping_user": True,
                "discord_category": "Support Tickets",
                "ticket_opened_category": "Support ticket"
            }
        }

        channel_name = f"{category.lower().replace(' ', '-')}-{user.name}"

        if category != "Support":
            if discord.utils.get(interaction.guild.channels, name=channel_name):
                await interaction.followup.send(
                    f"You already have a ticket in {category} category.", ephemeral=True
                )
                return

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        }

        discord_category_name = categories[category]["discord_category"]
        category_obj = discord.utils.get(interaction.guild.categories, name=discord_category_name)
        ticket_category_name = categories[category]["ticket_opened_category"]
        category_ticket = discord.utils.get(interaction.guild.categories, name=ticket_category_name)

        

        if category_obj is None:
            channel = await interaction.guild.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                reason=f"Ticket opened by {user} for {category}"
            )
        else:
            channel = await interaction.guild.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                category=category_obj,
                reason=f"Ticket opened by {user} for {category}"
            )

        config = categories[category]

        embed = discord.Embed(
            title=config["title"],
            description=config["description"].format(user=user),
            color=discord.Color.blue()
        )

        view = CloseButton()
        ping_roles = " ".join(f"<@&{rid}>" for rid in config["ping"])

        if config.get("ping_user", True):  
            content = f"{user.mention} {ping_roles}"
        else:
            content = ping_roles

        await channel.send(content=content, embed=embed, view=view)
        await interaction.followup.send(f"Your {ticket_category_name} has been opened {channel.mention} ✅", ephemeral=True)


class TicketDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCategory())

# ------------ Ticket setup command ------------

class Tickets(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.has_permissions(administrator=True)
    @commands.command(aliases=["ticket"])
    async def ticket_command(self, ctx):
        embed = discord.Embed(
            title="Open a ticket!",
            description=(
                "Welcome! You can create a ticket for any of the categories listed below. "
                "Please ensure you select the appropriate category for your issue. "
                "If your concern doesn't align with any of the options provided, feel free to create a general support ticket. Thank you!\n\n"
                "**Warn system for wrong tickets.**\n"
                "A straight warning will be issued for opening incorrect tickets for incorrect reasons. "
                "It is quite clear what ticket you need to open for what problem."
            ),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed, view=TicketDropdownView())

async def setup(client):
    await client.add_cog(Tickets(client))
