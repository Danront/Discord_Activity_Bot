import discord
from discord.ext import commands
from discord import app_commands
import json
import os

import asyncio
from datetime import datetime, timezone, timedelta

DATA_FILE = "json/rsvp_data.json"

def load_data():
    if os.path.isfile(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class EventRSVPView(discord.ui.View):
    def __init__(self, cog, guild_id: int, event_id: int):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = str(guild_id)
        self.event_id = str(event_id)

    def format_list(self, user_ids):
        if not user_ids:
            return "Aucun."
        return "\n".join(f"<@{uid}>" for uid in user_ids)

    async def update_embed(self, interaction: discord.Interaction):
        data = self.cog.data
        guild_data = data.get(self.guild_id, {})
        event_data = guild_data.get(self.event_id, {"yes": [], "no": []})

        embed = interaction.message.embeds[0]
        embed.set_field_at(1, name="✅ Participants", value=self.format_list(event_data["yes"]), inline=False)
        embed.set_field_at(2, name="❌ Refus", value=self.format_list(event_data["no"]), inline=False)
        await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(label="✅ Je participe", style=discord.ButtonStyle.success)
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        data = self.cog.data
        guild_data = data.setdefault(self.guild_id, {})
        event_data = guild_data.setdefault(self.event_id, {"yes": [], "no": []})

        if user_id not in event_data["yes"]:
            event_data["yes"].append(user_id)
        if user_id in event_data["no"]:
            event_data["no"].remove(user_id)

        save_data(data)
        await self.update_embed(interaction)
        await interaction.response.defer()

    @discord.ui.button(label="❌ Je ne participe pas", style=discord.ButtonStyle.danger)
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        data = self.cog.data
        guild_data = data.setdefault(self.guild_id, {})
        event_data = guild_data.setdefault(self.event_id, {"yes": [], "no": []})

        if user_id not in event_data["no"]:
            event_data["no"].append(user_id)
        if user_id in event_data["yes"]:
            event_data["yes"].remove(user_id)

        save_data(data)
        await self.update_embed(interaction)
        await interaction.response.defer()


class EventRSVP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.bg_task = self.bot.loop.create_task(self.reminder_task())

    async def reminder_task(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            now = datetime.now(timezone.utc)
            # Pour chaque serveur/guild
            for guild_id, events in self.data.items():
                guild = self.bot.get_guild(int(guild_id))
                if guild is None:
                    continue
                # Récupérer les événements officiels à jour
                try:
                    scheduled_events = await guild.fetch_scheduled_events()
                except Exception:
                    continue
                for event_id_str, participants in events.items():
                    event = discord.utils.get(scheduled_events, id=int(event_id_str))
                    if event is None:
                        continue
                    # Calcul du temps restant avant l'événement
                    delta = event.start_time - now
                    if timedelta(minutes=59) < delta <= timedelta(hours=1, minutes=1):
                        # Envoi du rappel 1 heure avant (environ)
                        for user_id in participants.get("yes", []):
                            user = self.bot.get_user(int(user_id))
                            if user:
                                try:
                                    await user.send(f"🔔 Rappel : l'événement **{event.name}** commence dans environ 1 heure !")
                                except Exception:
                                    pass
            await asyncio.sleep(60)  # On vérifie toutes les 60 secondes
        
    @app_commands.command(name="send_reminder", description="Envoie un rappel DM immédiat aux participants d'un événement")
    @app_commands.describe(event_id="L'ID de l'événement Discord")
    async def send_reminder(self, interaction: discord.Interaction, event_id: str):
        await interaction.response.defer(ephemeral=True)
        guild_id = str(interaction.guild.id)
        guild_data = self.data.get(guild_id, {})
        event_data = guild_data.get(event_id)

        if event_data is None:
            await interaction.followup.send("Aucun RSVP trouvé pour cet événement.", ephemeral=True)
            return

        guild = interaction.guild
        event = None
        try:
            events = await guild.fetch_scheduled_events()
            event = discord.utils.get(events, id=int(event_id))
        except Exception:
            pass

        if event is None:
            await interaction.followup.send("Événement introuvable.", ephemeral=True)
            return

        sent_count = 0
        failed_count = 0
        for user_id in event_data.get("yes", []):
            user = self.bot.get_user(int(user_id))
            if user:
                try:
                    await user.send(f"🔔 Rappel TEST : l'événement **{event.name}** commence bientôt !")
                    sent_count += 1
                except Exception:
                    failed_count += 1

        await interaction.followup.send(f"Rappel envoyé à {sent_count} participant(s). Échecs : {failed_count}.", ephemeral=True)

    @app_commands.command(name="rsvp_event", description="Créer un message RSVP lié à un événement Discord")
    async def rsvp_event(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        events = await interaction.guild.fetch_scheduled_events()

        if not events:
            await interaction.followup.send("Aucun événement trouvé sur ce serveur.", ephemeral=True)
            return

        options = [
            discord.SelectOption(label=event.name, description=event.description or "Aucune description", value=str(event.id))
            for event in events
        ]

        select_menu = discord.ui.Select(placeholder="Choisissez un événement", options=options)

        async def select_callback(select_interaction: discord.Interaction):
            event_id = select_menu.values[0]
            event = discord.utils.get(events, id=int(event_id))

            guild_id = interaction.guild.id
            guild_data = self.data.setdefault(str(guild_id), {})
            event_data = guild_data.setdefault(event_id, {"yes": [], "no": []})

            embed = discord.Embed(
                title=event.name,
                description=event.description or "Aucune description",
                color=discord.Color.blurple()
            )
            embed.add_field(name="📅 Date", value=discord.utils.format_dt(event.start_time, "F"), inline=False)
            embed.add_field(name="✅ Participants", value="Aucun." if not event_data["yes"] else "\n".join(f"<@{uid}>" for uid in event_data["yes"]), inline=False)
            embed.add_field(name="❌ Refus", value="Aucun." if not event_data["no"] else "\n".join(f"<@{uid}>" for uid in event_data["no"]), inline=False)

            view = EventRSVPView(self, guild_id, int(event_id))
            await select_interaction.response.send_message(embed=embed, view=view)

        select_menu.callback = select_callback

        view = discord.ui.View()
        view.add_item(select_menu)

        await interaction.followup.send("Sélectionnez un événement :", view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(EventRSVP(bot))
