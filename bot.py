import os
import requests
import discord
from yt_dlp import YoutubeDL
from config import DISCORD_BOT_TOKEN, UPLOADBOT_USERNAME, UPLOADBOT_PASSWORD, BACKEND_URL, CLIP_CHANNEL_ID

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def get_backend_token():
    response = requests.post(f'{BACKEND_URL}/api/users/login', json={
        'username': UPLOADBOT_USERNAME,
        'password': UPLOADBOT_PASSWORD
    })
    response.raise_for_status()
    return response.json()['token']

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    global BACKEND_TOKEN
    BACKEND_TOKEN = get_backend_token()
    await client.change_presence(activity=discord.CustomActivity(name='Fetching your clips...'))

@client.event
async def on_message(message):
    if message.author == client.user or message.channel.id != CLIP_CHANNEL_ID:
        return

    if 'youtube.com' in message.content or 'youtu.be' in message.content or 'twitch.tv' in message.content:
        await message.add_reaction('🔄')
        url = message.content.strip()
        ydl_opts = {
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'ratelimit': 20 * 1024 * 1024,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            print(info)
            filename = ydl.prepare_filename(info)
            streamer = info.get('creator', info.get('channel'))

    elif message.attachments and 'cdn.discordapp.com' in message.attachments[0].url:
        await message.add_reaction('🔄')
        split_v1 = str(message.attachments).split("filename='")[1]
        filename = str(split_v1).split("' ")[0]
        if filename.endswith(".mp4"):
            filename = "downloads/{}".format(filename)

            os.makedirs(os.path.dirname(filename), exist_ok=True)

            await message.attachments[0].save(fp=filename)
            streamer = message.author.name

    # Upload to backend
    with open(filename, 'rb') as f:
        files = {'clip': f}
        data = {'streamer': streamer}
        headers = {'Authorization': f'Bearer {BACKEND_TOKEN}'}
        response = requests.post(f'{BACKEND_URL}/api/clips/upload', files=files, data=data, headers=headers)
        await message.clear_reaction('🔄')

    if response.status_code == 200:
        await message.add_reaction('✅')
        os.remove(filename)
    else:
        await message.add_reaction('❌')
        os.remove(filename)

client.run(DISCORD_BOT_TOKEN)