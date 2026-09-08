import os, requests
from dotenv import load_dotenv
load_dotenv()

FB_PAGE_ID = os.environ['FB_PAGE_ID']
TOKEN = os.environ['FB_PAGE_ACCESS_TOKEN']
VIDEO_URL = 'https://cdn.jsdelivr.net/gh/enigmarealism99/ig-movie-bot@main/media/polling_4a0089f14c454928bbc6b8c2555957d7.mp4'
base = f'https://graph.facebook.com/v25.0/{FB_PAGE_ID}/video_reels'

start = requests.post(base, data={'upload_phase': 'start', 'access_token': TOKEN}, timeout=30)
print('START:', start.status_code, start.text)
start_data = start.json()
video_id, upload_url = start_data['video_id'], start_data['upload_url']

transfer = requests.post(
    upload_url,
    headers={
        'Authorization': f'OAuth {TOKEN}',
        'offset': '0',
        'file_url': VIDEO_URL,
    },
    timeout=60,
)
print('TRANSFER:', transfer.status_code, transfer.text)
