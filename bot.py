import discord
from discord.ext import commands
import requests
import os
from dotenv import load_dotenv

# 1. Load the hidden keys from your .env file
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
NEWSDATA_TOKEN = os.getenv('NEWSDATA_TOKEN')

# 2. Set up the Discord bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    # Sync the slash commands to Discord when the bot boots up
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(e)
    print(f'Bot is online as {bot.user}')

# 3. Create the /news slash command
@bot.tree.command(name="news", description="Fetch the latest news for a specific crypto ticker")
async def news(interaction: discord.Interaction, coin: str):
    # Tell Discord to "think" while we wait for the API response
    await interaction.response.defer()
    
    # Hit the NewsData.io Crypto API endpoint
    url = f"https://newsdata.io/api/1/crypto?apikey={NEWSDATA_TOKEN}&coin={coin.lower()}&language=en"

    try:
        response = requests.get(url).json()
    except Exception as e:
        await interaction.followup.send("🚨 The News API is currently down or unresponsive.")
        return
    
    # Catch API errors (like rate limits) before they crash the bot
    if response.get('status') == 'error':
        # Safely grab the error message the API sent back
        error_info = response.get('results', {}).get('message', 'Unknown API Error')
        await interaction.followup.send(f"⚠️ **API Error:** {error_info}")
        return

    results = response.get('results', [])
    
    # Make 100% sure 'results' is actually a list and has at least 1 item
    if not isinstance(results, list) or len(results) == 0:
        await interaction.followup.send(f"Could not find any recent English news for `{coin.upper()}`.")
        return
        
    # Now it is safe to grab the top article
    article = results[0] 
    title = article.get('title', 'No Title')
    link = article.get('link', 'No Link Available')
    source = article.get('source_id', 'Unknown Source').capitalize()
    
    # Send the final embedded message back to the Discord channel
    await interaction.followup.send(f"🗞️ **Latest {coin.upper()} News (via {source}):**\n**{title}**\n{link}")

# 4. Run the bot
bot.run(DISCORD_TOKEN)