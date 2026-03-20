import aiohttp
import asyncio
import os
from flask import Flask, request, jsonify
import threading

USER_TOKEN = os.environ.get('USER_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL')
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')

app = Flask(__name__)

async def send_imagine(prompt):
    headers = {
        'Authorization': USER_TOKEN,
        'Content-Type': 'application/json'
    }
    payload = {
        'type': 2,
        'application_id': '936929561302675456',
        'guild_id': None,
        'channel_id': CHANNEL_ID,
        'session_id': 'automation',
        'data': {
            'version': '1166847114203123795',
            'id': '938956540159881230',
            'name': 'imagine',
            'type': 1,
            'options': [{'type': 3, 'name': 'prompt', 'value': prompt}]
        }
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'https://discord.com/api/v9/interactions',
            headers=headers,
            json=payload
        ) as resp:
            print(f'MJ响应状态: {resp.status}')

async def listen_for_image(prompt_keyword):
    headers = {'Authorization': USER_TOKEN}
    for _ in range(20):
        await asyncio.sleep(10)
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'https://discord.com/api/v9/channels/{CHANNEL_ID}/messages?limit=10',
                headers=headers
            ) as resp:
                messages = await resp.json()
                for msg in messages:
                    if msg.get('author', {}).get('id') == '936929561302675456':
                        attachments = msg.get('attachments', [])
                        if attachments:
                            image_url = attachments[0]['url']
                            async with aiohttp.ClientSession() as s:
                                await s.post(N8N_WEBHOOK_URL, json={
                                    'image_url': image_url,
                                    'message_id': msg['id']
                                })
                            return

@app.route('/imagine', methods=['POST'])
def imagine():
    data = request.json
    prompt = data.get('prompt')
    loop = asyncio.new_event_loop()
    threading.Thread(target=lambda: loop.run_until_complete(run_tasks(prompt))).start()
    return jsonify({'status': 'sent'})

async def run_tasks(prompt):
    await send_imagine(prompt)
    await listen_for_image(prompt)

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

threading.Thread(target=run_flask).start()

import discord
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Bot上线：{client.user}')

client.run(DISCORD_TOKEN)
