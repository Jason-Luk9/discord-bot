import discord
from discord.ext import commands
from discord import app_commands
import requests
import os
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
NEWSDATA_TOKEN = os.getenv('NEWSDATA_TOKEN')

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    # REPLACE WITH YOUR SERVER ID IF YOU WANT INSTANT UPDATES
    # MY_GUILD = discord.Object(id=1234567890) 
    try:
        # bot.tree.copy_global_to(guild=MY_GUILD)
        # synced = await bot.tree.sync(guild=MY_GUILD)
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(e)
    print(f'Bot is online as {bot.user}')

# --- THE AUTOCOMPLETE FUNCTION ---
# This runs in the background as the user types in the 'coin' box
async def coin_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    # A list of popular coins to suggest
    popular_coins = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'ADA', 'AVAX', 'LINK', 'BNB', 'TON']
    
    # Filter the list based on what they are currently typing
    return [
        app_commands.Choice(name=coin, value=coin)
        for coin in popular_coins if current.lower() in coin.lower()
    ][:25] # Discord only allows a maximum of 25 suggestions at once

# --- THE SLASH COMMAND ---
@bot.tree.command(name="news", description="Fetch the latest crypto news with custom filters")
@app_commands.describe(
    coin="The crypto ticker (e.g., BTC, ETH)",
    language="Choose a language (Defaults to English)",
    country="Enter a 2-letter country code (e.g., us, gb, jp) - Optional"
)
@app_commands.choices(language=[
    app_commands.Choice(name="English", value="en"),
    app_commands.Choice(name="Spanish", value="es"),
    app_commands.Choice(name="French", value="fr"),
    app_commands.Choice(name="German", value="de"),
    app_commands.Choice(name="Japanese", value="jp"),
])
# We link the autocomplete function to the 'coin' parameter here
@app_commands.autocomplete(coin=coin_autocomplete)
async def news(
    interaction: discord.Interaction, 
    coin: str, 
    language: app_commands.Choice[str] = None, 
    country: str = None                        
):
    await interaction.response.defer()
    
    lang_code = language.value if language else "en"
    url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_TOKEN}&q={coin.lower()}%20crypto&language={lang_code}"
    
    if country:
        url += f"&country={country.lower()}"
    
    try:
        response = requests.get(url).json()
    except Exception as e:
        await interaction.followup.send("🚨 The News API is currently down or unresponsive.")
        return
    
    if response.get('status') == 'error':
        error_info = response.get('results', {}).get('message', 'Unknown API Error')
        await interaction.followup.send(f"⚠️ **API Error:** {error_info}")
        return

    results = response.get('results', [])
    
    if not isinstance(results, list) or len(results) == 0:
        await interaction.followup.send(f"Could not find any recent news for `{coin.upper()}` with those filters.")
        return
        
    filter_text = f"(Language: {lang_code.upper()}"
    if country:
        filter_text += f", Country: {country.upper()}"
    filter_text += ")"

    # --- MULTIPLE ARTICLES UPGRADE ---
    # Start building our message
    final_message = f"🗞️ **Latest {coin.upper()} News** {filter_text}:\n\n"
    
    # Loop through the first 5 articles (or fewer if there aren't 5)
    for article in results[:5]:
        title = article.get('title', 'No Title')
        link = article.get('link', 'No Link Available')
        source = article.get('source_id', 'Unknown Source').capitalize()
        
        # Add each article to the final message
        # Wrapping the {link} in < > stops Discord from making giant preview blocks
        final_message += f"🔹 **{title}** (*{source}*)\n<{link}>\n\n"

    # Send the combined message!
    # Discord has a 2000 character limit per message, so keeping it to 5 articles is safe.
    await interaction.followup.send(final_message)

bot.run(DISCORD_TOKEN)