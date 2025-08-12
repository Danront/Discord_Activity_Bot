import discord
from discord.ext import commands
from discord import app_commands

class RSVPView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.participants = set()  # Stocke les ID des membres
        self.declined = set()      # Stocke ceux qui refusent

    def format_participants(self):
        if not self.participants:
            return "Aucun participant pour le moment."
        return "\n".join(f"<@{user_id}>" for user_id in self.participants)

    def format_declined(self):
        if not self.declined:
            return "Aucun refus pour le moment."
        return "\n".join(f"<@{user_id}>" for user_id in self.declined)

    async def update_message(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        embed.set_field_at(0, name="✅ Participants", value=self.format_participants(), inline=False)
        embed.set_field_at(1, name="❌ Refus", value=self.format_declined(), inline=False)
        await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(label="✅ Je participe", style=discord.ButtonStyle.success)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        self.participants.add(user_id)
        self.declined.discard(user_id)
        await self.update_message(interaction)
        await interaction.response.defer()

    @discord.ui.button(label="❌ Je ne participe pas", style=discord.ButtonStyle.danger)
    async def decline_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        self.declined.add(user_id)
        self.participants.discard(user_id)
        await self.update_message(interaction)
        await interaction.response.defer()


class RSVP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rsvp", description="Créer un message pour confirmer la présence à un événement")
    @app_commands.describe(titre="Titre de l'événement", description="Description de l'événement")
    async def rsvp(self, interaction: discord.Interaction, titre: str, description: str):
        embed = discord.Embed(title=titre, description=description, color=discord.Color.blue())
        embed.add_field(name="✅ Participants", value="Aucun participant pour le moment.", inline=False)
        embed.add_field(name="❌ Refus", value="Aucun refus pour le moment.", inline=False)
        view = RSVPView()
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(RSVP(bot))
