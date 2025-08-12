import discord
from discord.ext import commands
from discord import app_commands

class RaidHelper(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Stocke les raids en mémoire : raid_name -> set of user IDs
        self.raids = {}

    @app_commands.command(name="create_raid", description="Créer un raid avec un nom et une limite de joueurs")
    @app_commands.describe(nom="Nom du raid", limite="Nombre maximum de joueurs")
    async def creer_raid(self, interaction: discord.Interaction, nom: str, limite: int):
        if nom in self.raids:
            await interaction.response.send_message(f"Un raid nommé '{nom}' existe déjà.", ephemeral=True)
            return
        if limite < 1:
            await interaction.response.send_message("La limite doit être au moins 1.", ephemeral=True)
            return

        self.raids[nom] = {"limite": limite, "joueurs": set()}
        await interaction.response.send_message(f"Raid '{nom}' créé avec une limite de {limite} joueurs.")

    @app_commands.command(name="join_raid", description="Rejoindre un raid existant")
    @app_commands.describe(nom="Nom du raid à rejoindre")
    async def rejoindre_raid(self, interaction: discord.Interaction, nom: str):
        raid = self.raids.get(nom)
        if not raid:
            await interaction.response.send_message(f"Le raid '{nom}' n'existe pas.", ephemeral=True)
            return
        
        if len(raid["joueurs"]) >= raid["limite"]:
            await interaction.response.send_message(f"Le raid '{nom}' est déjà complet.", ephemeral=True)
            return
        
        if interaction.user.id in raid["joueurs"]:
            await interaction.response.send_message("Tu es déjà dans ce raid.", ephemeral=True)
            return

        raid["joueurs"].add(interaction.user.id)
        await interaction.response.send_message(f"{interaction.user.display_name} a rejoint le raid '{nom}' !")

    @app_commands.command(name="list_raid", description="Afficher la liste des joueurs d'un raid")
    @app_commands.describe(nom="Nom du raid")
    async def liste_raid(self, interaction: discord.Interaction, nom: str):
        raid = self.raids.get(nom)
        if not raid:
            await interaction.response.send_message(f"Le raid '{nom}' n'existe pas.", ephemeral=True)
            return

        if not raid["joueurs"]:
            await interaction.response.send_message(f"Le raid '{nom}' n'a aucun participant pour le moment.")
            return

        membres = []
        for user_id in raid["joueurs"]:
            user = self.bot.get_user(user_id)
            membres.append(user.display_name if user else f"Utilisateur {user_id}")

        await interaction.response.send_message(f"Participants au raid '{nom}' ({len(membres)}/{raid['limite']}):\n" + "\n".join(membres))

    @app_commands.command(name="delete_raid", description="Supprimer un raid")
    @app_commands.describe(nom="Nom du raid à supprimer")
    async def supprimer_raid(self, interaction: discord.Interaction, nom: str):
        if nom not in self.raids:
            await interaction.response.send_message(f"Le raid '{nom}' n'existe pas.", ephemeral=True)
            return

        del self.raids[nom]
        await interaction.response.send_message(f"Le raid '{nom}' a été supprimé.")
    
    @app_commands.command(name="actif_raid", description="Afficher tous les raids actifs")
    async def liste_raids(self, interaction: discord.Interaction):
        if not self.raids:
            await interaction.response.send_message("Il n'y a aucun raid actif pour le moment.")
            return
        
        message = "**Raids actifs :**\n"
        for nom, raid in self.raids.items():
            message += f"- {nom} : {len(raid['joueurs'])}/{raid['limite']} participants\n"
        
        await interaction.response.send_message(message)


async def setup(bot: commands.Bot):
    await bot.add_cog(RaidHelper(bot))