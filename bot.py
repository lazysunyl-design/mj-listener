import discord
import aiohttp
import asyncio
import os
from flask import Flask, request, jsonify
import threading

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
CHANNEL_ID = int(os.environ.get('CHANNEL_ID'))
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
client = discord.Client(intents=intents)

app = Flask(__name__)

@app.route('/imagine', methods=['POST'])
def imagine():
    data = request.json
    prompt = data.get('prompt')
    asyncio.run_coroutine_threadsafe(send_imagine(prompt), client.loop)
    return jsonify({'status': 'sent'})

async def send_imagine(prompt):
    channel = client.get_channel(CHANNEL_ID)
    await channel.send(f'/imagine prompt: {prompt}')

@client.event
async def on_ready():
    print(f'Bot上线：{client.user}')

@client.event
async def on_message(message):
    if message.author.bot and message.attachments: