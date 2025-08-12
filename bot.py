import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

import keepAlive

load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

EXTENSIONS = [
    "cogs.events",
    "cogs.rsvp",
    "cogs.raid_helper"
]

# Démarage du bot (quand le bot est pret)
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔁 {len(synced)} commandes slash synchronisées.")
    except Exception as e:
        print(f"Erreur de sync : {e}")

# Chargement des extentions
@bot.event
async def setup_hook():
    for ext in EXTENSIONS:
        await bot.load_extension(ext)
    await bot.tree.sync()

#keep alive the server
#keepAlive.keep_alive()

# Démarrage du bot
bot.run(os.getenv("DISCORD_TOKEN"))