import os
import asyncio
import threading
import aiohttp
from flask import Flask, request, jsonify

LEGNEXT_API_KEY = os.environ.get('LEGNEXT_API_KEY')
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL')
BASE_URL = 'https://api.legnext.ai/api/v1'

app = Flask(__name__)

async def generate_image(prompt, callback_url):
    headers = {
        'x-api-key': LEGNEXT_API_KEY,
        'Content-Type': 'application/json'
    }
    payload = {
        'text': prompt,
        'callback': callback_url
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{BASE_URL}/diffusion', headers=headers, json=payload) as resp:
            result = await resp.json()
            print(f'LegNext 响应: {resp.status} {result}')
            return result

@app.route('/imagine', methods=['POST'])
def imagine():
    data = request.json
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({'status': 'error', 'message': 'prompt is required'}), 400

    # callback 地址指向本服务自身的 /callback 端点
    port = int(os.environ.get('PORT', 5000))
    callback_url = os.environ.get('SELF_URL', f'http://localhost:{port}') + '/callback'

    loop = asyncio.new_event_loop()
    threading.Thread(
        target=lambda: loop.run_until_complete(generate_image(prompt, callback_url))
    ).start()

    return jsonify({'status': 'sent'})

@app.route('/callback', methods=['POST'])
def callback():
    data = request.json
    print(f'LegNext 回调数据: {data}')

    image_url = None
    if data:
        image_url = (
            data.get('url') or
            data.get('image_url') or
            data.get('output') or
            (data.get('images') or [None])[0]
        )

    if image_url and N8N_WEBHOOK_URL:
        async def send_to_n8n():
            async with aiohttp.ClientSession() as session:
                await session.post(N8N_WEBHOOK_URL, json={
                    'image_url': image_url,
                    'job_id': data.get('id', '')
                })
        loop = asyncio.new_event_loop()
        threading.Thread(target=lambda: loop.run_until_complete(send_to_n8n())).start()

    return jsonify({'status': 'ok'})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
```
