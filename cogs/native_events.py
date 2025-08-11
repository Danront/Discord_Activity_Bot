import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta, timezone

class EventCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="create_event", description="Créer un événement Discord natif")
    @app_commands.describe(
        name="Nom de l'événement",
        description="Description de l'événement",
        start_time="Heure de début (YYYY-MM-DD HH:MM en UTC+0)",
        end_time="Heure de fin (YYYY-MM-DD HH:MM en UTC+0)"
    )
    async def create_event(self, interaction: discord.Interaction, name: str, description: str, start_time: str, end_time: str):
        try:
            # Convertir les strings en objets datetime UTC
            fmt = "%Y-%m-%d %H:%M"
            start_dt = datetime.strptime(start_time, fmt).replace(tzinfo=timezone.utc)
            end_dt = datetime.strptime(end_time, fmt).replace(tzinfo=timezone.utc)

            # Créer l'événement
            event = await interaction.guild.create_scheduled_event(
                name=name,
                description=description,
                start_time=start_dt,
                end_time=end_dt,
                privacy_level=discord.PrivacyLevel.guild_only,
                entity_type=discord.EntityType.external,  # externe = événement externe (webinaire, lien par ex)
                location="Lien Zoom ou autre"  # Obligatoire si entity_type=external
            )
            await interaction.response.send_message(f"Événement créé : {event.name} (ID: {event.id})")
        except Exception as e:
            await interaction.response.send_message(f"Erreur lors de la création de l'événement : {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(EventCog(bot))
