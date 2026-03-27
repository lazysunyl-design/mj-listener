import os
import asyncio
import threading
import time
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
    try:
        image_url = data['data']['output']['image_url']
    except (KeyError, TypeError):
        image_url = None

    if image_url:
        async def download_image():
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status == 200:
                        filename = f'/data/mj-images/{int(time.time()*1000)}.png'
                        content = await resp.read()
                        with open(filename, 'wb') as f:
                            f.write(content)
                        print(f'图片已保存: {filename}')

        async def send_to_n8n():
            async with aiohttp.ClientSession() as session:
                await session.post(N8N_WEBHOOK_URL, json={
                    'image_url': image_url,
                    'job_id': data['data'].get('job_id', '')
                })

        loop = asyncio.new_event_loop()
        threading.Thread(target=lambda: loop.run_until_complete(download_image())).start()

        if N8N_WEBHOOK_URL:
            loop2 = asyncio.new_event_loop()
            threading.Thread(target=lambda: loop2.run_until_complete(send_to_n8n())).start()

    return jsonify({'status': 'ok'})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
