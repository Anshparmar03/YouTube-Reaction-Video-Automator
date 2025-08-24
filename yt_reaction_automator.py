import os
import subprocess
import sys
import time
import cv2
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow
import httplib2

# YouTube API constants
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
YOUTUBE_UPLOAD_SCOPE = 'https://www.googleapis.com/auth/youtube.upload'
CLIENT_SECRETS_FILE = 'client_secrets.json'  # Your OAuth file
MISSING_CLIENT_SECRETS_MESSAGE = 'WARNING: Configure client_secrets.json'

# Fetching settings
API_KEY = 'YOUR_API_KEY'  # Your YouTube API key
REGION_CODE = 'US'  # Change to your region, e.g., 'Ir'

# Retry settings (from Google sample)
httplib2.RETRIES = 1
MAX_RETRIES = 10
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
                        httplib.IncompleteRead, httplib.ImproperConnectionState,
                        httplib.CannotSendRequest, httplib.CannotSendHeader,
                        httplib.ResponseNotReady, httplib.BadStatusLine)
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

def get_authenticated_service():
    args = argparser.parse_args()
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=YOUTUBE_UPLOAD_SCOPE,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)
    storage = Storage(f"{sys.argv[0]}-oauth2.json")
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                 http=credentials.authorize(httplib2.Http()))

def upload_video(youtube, file_path, title, description, category='22', keywords='', privacy='private'):
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': keywords.split(','),
            'categoryId': category
        },
        'status': {'privacyStatus': privacy}
    }
    insert_request = youtube.videos().insert(part=','.join(body.keys()),
                                             body=body,
                                             media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True))
    resumable_upload(insert_request)

def resumable_upload(request):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            print('Uploading file...')
            status, response = request.next_chunk()
            if response is not None:
                if 'id' in response:
                    print(f"Video uploaded: https://youtu.be/{response['id']}")
                else:
                    sys.exit('Upload failed.')
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = f"Retriable HTTP error {e.resp.status}"
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = f"Retriable error: {e}"
        if error is not None:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                sys.exit('Max retries exceeded.')
            time.sleep(5 ** retry)  # Exponential backoff

def fetch_trending_videos():
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    request = youtube.videos().list(
        part='snippet',
        chart='mostPopular',
        maxResults=10,
        regionCode=REGION_CODE
    )
    response = request.execute()
    return [(item['snippet']['title'], item['id']) for item in response['items']]

def download_video(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    file_path = f"{video_id}.mp4"
    subprocess.run(['yt-dlp', '-f', 'best', '-o', file_path, url])
    return file_path

def record_reaction_while_playing(original_path):
    cap_video = cv2.VideoCapture(original_path)
    cap_webcam = cv2.VideoCapture(0)  # 0 for default webcam
    
    if not cap_video.isOpened() or not cap_webcam.isOpened():
        print("Error opening video or webcam.")
        return None
    
    fps = cap_video.get(cv2.CAP_PROP_FPS)
    width = int(cap_webcam.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap_webcam.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    reaction_path = original_path.replace('.mp4', '_reaction.mp4')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(reaction_path, fourcc, fps, (width, height))
    
    print("Press 'q' to stop recording early.")
    while cap_video.isOpened():
        ret_video, frame_video = cap_video.read()
        ret_web, frame_web = cap_webcam.read()
        
        if ret_video and ret_web:
            cv2.imshow('Playing Video - React Now!', frame_video)
            out.write(frame_web)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            break
    
    cap_video.release()
    cap_webcam.release()
    out.release()
    cv2.destroyAllWindows()
    return reaction_path

def create_split_screen(original_path, reaction_path):
    output_path = original_path.replace('.mp4', '_split.mp4')
    # Scale to half width (assuming same height; adjust if needed)
    cmd = [
        'ffmpeg',
        '-i', original_path,
        '-i', reaction_path,
        '-filter_complex', '[0:v]scale=iw/2:-1[vid1];[1:v]scale=iw/2:-1[vid2];[vid1][vid2]hstack=inputs=2[v];[0:a][1:a]amerge[a]',
        '-map', '[v]',
        '-map', '[a]',
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-strict', 'experimental',
        output_path
    ]
    subprocess.run(cmd)
    return output_path

# Main execution
if __name__ == '__main__':
    print("Fetching top 10 trending videos...")
    videos = fetch_trending_videos()
    
    youtube = get_authenticated_service()  # Auth for upload
    
    for title, video_id in videos:
        print(f"\nProcessing: {title} ({video_id})")
        
        # Step 1: Download (warn: against terms)
        original_path = download_video(video_id)
        
        # Step 2: Record reaction
        reaction_path = record_reaction_while_playing(original_path)
        if not reaction_path:
            continue
        
        # Step 3: Composite split-screen
        split_path = create_split_screen(original_path, reaction_path)
        
        # Step 4: Upload
        upload_title = f"My Reaction to Trending Video: {title}"
        upload_desc = f"Reacting to the trending video '{title}'. Original: https://youtu.be/{video_id}\n#reaction #trending"
        upload_video(youtube, split_path, upload_title, upload_desc, keywords='reaction,trending,youtube')
        