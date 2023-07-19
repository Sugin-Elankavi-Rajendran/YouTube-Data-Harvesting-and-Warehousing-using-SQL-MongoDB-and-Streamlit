import googleapiclient.discovery
import pymongo
from pymongo import MongoClient
import mysql
from config import API_KEY
import streamlit as st

api_service_name = "youtube"
api_version = "v3"

youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=API_KEY)

myclient = MongoClient("mongodb://localhost:27017/")
mydatabase = myclient["youtube"]
mycollection = mydatabase["details"]


def get_channel_data(channel_id):
    response = youtube.channels().list(part='snippet,statistics,ContentDetails', id=channel_id).execute()
    channel_data = response['items'][0]

    channel_title = channel_data['snippet']['title']
    channel_subscribers = int(channel_data['statistics']['subscriberCount'])
    channel_views = int(channel_data['statistics']['viewCount'])
    channel_description = channel_data['snippet']['description']
    channel_playlist_id = channel_data['contentDetails']['relatedPlaylists']['uploads']

    return {
        "Channel_Name": {
            "Channel_Name": channel_title,
            "Channel_Id": channel_id,
            "Subscription_Count": channel_subscribers,
            "Channel_Views": channel_views,
            "Channel_Description": channel_description,
            "Playlist_Id": channel_playlist_id
        }
    }


def get_playlist_data(playlist_id):
    playlist_response = youtube.playlists().list(part='snippet', playlistId=playlist_id, maxResults=5).execute()
    playlists = playlist_response['items']

    # while 'nextPageToken' in playlist_response:
    #     next_page_token = playlist_response['nextPageToken']
    #     playlist_response = youtube.playlists().list(part='snippet', playlistId=playlist_id, maxResults=5, pageToken=next_page_token).execute()
    #     playlists.extend(playlist_response['items'])

    return playlists


def get_video_data(channel_id):
    video_response = youtube.search().list(part='snippet', channelId=channel_id, type='video', maxResults=5).execute()
    videos = video_response['items']

    # while 'nextPageToken' in video_response:
    #     next_page_token = video_response['nextPageToken']
    #     video_response = youtube.search().list(part='snippet', channelId=channel_id, type='video', maxResults=5, pageToken=next_page_token).execute()
    #     videos.extend(video_response['items'])

    return videos


def main():
    st.title("YouTube Channel Migration")

    channel_ids = st.text_area("Enter YouTube Channel IDs (one per line):")
    channel_ids = channel_ids.strip().split("\n") if channel_ids else []

    for channel_id in channel_ids:
        channel_data = get_channel_data(channel_id)
        playlists = get_playlist_data(channel_data["Channel_Name"]["Playlist_Id"])
        videos = get_video_data(channel_id)

        
        mycollection.insert_one(channel_data["Channel_Name"])
        for playlist in playlists:
            mycollection.insert_one({"Playlist": playlist})
        for video in videos:
            mycollection.insert_one({"Video": video})

        
        st.write(f"Channel Name: {channel_data['Channel_Name']['Channel_Name']}")
        st.write(f"Channel ID: {channel_data['Channel_Name']['Channel_Id']}")
        st.write(f"Channel Subscribers: {channel_data['Channel_Name']['Subscription_Count']}")
        st.write(f"Channel Views: {channel_data['Channel_Name']['Channel_Views']}")
        st.write(f"Channel Description: {channel_data['Channel_Name']['Channel_Description']}")
        for playlist in playlists:
            st.write(f"Playlist Title: {playlist['snippet']['title']}")
            st.write(f"Playlist ID: {playlist['id']}")
        for video in videos:
            st.write(f"Video Title: {video['snippet']['title']}")
            st.write(f"Video ID: {video['id']['videoId']}")

        st.write("Data stored in MongoDB!")

if __name__ == "__main__":
    main()
