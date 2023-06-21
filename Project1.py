import googleapiclient.discovery
import googleapiclient.errors
from pymongo import MongoClient
import pymongo

api_service_name = "youtube"
api_version = "v3"
api_key = "AIzaSyAVnIpAcy75VNtFRd1avocxjfOVOubbres"
youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=api_key)

channel_id = "UCS2pJAOOJYak8PpB9oV1LdA"  
video_id = "TtgNEPYnmFI"  

channel_request = youtube.channels().list(part="snippet,statistics", id=channel_id)
channel_response = channel_request.execute()

video_request = youtube.videos().list(part="snippet,statistics", id=video_id)
video_response = video_request.execute()

channel_title = channel_response["items"][0]["snippet"]["title"]
channel_view_count = channel_response["items"][0]["statistics"]["viewCount"]

video_title = video_response["items"][0]["snippet"]["title"]
video_view_count = video_response["items"][0]["statistics"]["viewCount"]

myclient = pymongo.MongoClient("mongodb://localhost:27017/")

mydatabase = myclient["youtube"]

mycollection = mydatabase["details"]

youtube_data = {
    "title": video_title,
    "view_count": video_view_count,
    
}

mycollection.insert_one(youtube_data)

myclient.close()

