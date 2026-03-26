import aiohttp
import asyncio
import os
from flask import Flask, request, jsonify
import threading
import discord

USER_TOKEN = os.environ.get('USER_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL')
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
GUILD_ID = '1484333340315095062'

app = Flask(__name__)

async def send_imagine(prompt):
    headers = {
        'Authorization': USER_TOKEN,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
        'X-Super-Properties': 'eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6InpoLUNOIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzE0Ni4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTQ2LjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiIiLCJyZWZlcnJpbmdfZG9tYWluIjoiIiwicmVmZXJyZXJfY3VycmVudCI6IiIsInJlZmVycmluZ19kb21haW5fY3VycmVudCI6IiIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjUxNTQyNSwiY2xpZW50X2V2ZW50X3NvdXJjZSI6bnVsbCwiaGFzX2NsaWVudF9tb2RzIjpmYWxzZSwiY2xpZW50X2xhdW5jaF9pZCI6IjJiNzNjZjVlLTAzMDAtNDQ1ZS04NzJiLWM5MzZiYTQzOWYzZiIsImxhdW5jaF9zaWduYXR1cmUiOiI2MTIyYWJhMi1hMmUxLTQwNGItODU3Yy1hMTA2MzRkMzk2YWIiLCJjbGllbnRfaGVhcnRiZWF0X3Nlc3Npb25faWQiOiI4OTg3NDNhMi1iOWE4LTQyNDQtYWNjYS1kMzE0NjczNDBmZDEiLCJjbGllbnRfYXBwX3N0YXRlIjoidW5mb2N1c2VkIn0=',
        'X-Discord-Locale': 'zh-CN',
        'Origin': 'https://discord.com',
        'Referer': 'https://discord.com/channels/' + GUILD_ID + '/' + str(CHANNEL_ID),
    }
    payload = {
        'type': 2,
        'application_id': '936929561302675456',
        'guild_id': GUILD_ID,
        'channel_id': str(CHANNEL_ID),
        'session_id': 'automation',
        'data': {
            'version': '1237876415471554623',
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
            text = await resp.text()
            print(f'MJ响应内容: {text}')

async def listen_for_image():
    headers = {'Authorization': USER_TOKEN}
    for _ in range(20):
        await asyncio.sleep(10)
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'https://discord.com/api/v9/channels/{CHANNEL_ID}/messages?limit=10',
                headers=headers
            ) as resp:
                messages = await resp.json()
                if not isinstance(messages, list):
                    print(f'消息获取失败: {messages}')
                    continue
                for msg in messages:
                    if not isinstance(msg, dict):
                        continue
                    if msg.get('author', {}).get('id') == '936929561302675456':
                        attachments = msg.get('attachments', [])
                        if attachments:
                            image_url = attachments[0]['url']
                            print(f'找到图片: {image_url}')
                            async with aiohttp.ClientSession() as s:
                                await s.post(N8N_WEBHOOK_URL, json={
                                    'image_url': image_url,
                                    'message_id': msg['id']
                                })
                            return

async def run_tasks(prompt):
    await send_imagine(prompt)
    await listen_for_image()

@app.route('/imagine', methods=['POST'])
def imagine():
    data = request.json
    prompt = data.get('prompt')
    loop = asyncio.new_event_loop()
    threading.Thread(target=lambda: loop.run_until_complete(run_tasks(prompt))).start()
    return jsonify({'status': 'sent'})

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

threading.Thread(target=run_flask).start()

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Bot上线：{client.user}')

client.run(DISCORD_TOKEN)
