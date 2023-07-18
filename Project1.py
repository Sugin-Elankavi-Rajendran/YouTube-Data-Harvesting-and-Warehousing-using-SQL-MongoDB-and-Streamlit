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


def main():
    st.title("YouTube Channel Migration")
    
    channel = st.text_input("Enter Youtube Channel ID: ")
    
    if channel:
        response = youtube.channels().list(part='snippet,statistics,ContentDetails',id=channel).execute()
        channel_name = response['items'][0]

        channel_title = channel_name['snippet']['title']
        channel_subscribers = channel_name['statistics']['subscriberCount']
        channel_views = channel_name['statistics']['viewCount']
        channel_description = channel_name ['snippet']['description']
                            
        st.write (f'Channel Name: {channel_title}')
        st.write (f'Channel ID: {channel}')
        st.write (f'Channel Subscribers: {channel_subscribers}')
        st.write (f'Channel Views: {channel_views}')
        st.write (f'Channel Description: {channel_description}')
        
        playlist_response = youtube.playlists().list(part='snippet',channelId=channel,maxResults=5).execute()
        playlists = playlist_response['items']

        while 'nextPageToken' in playlist_response:
            next_page_token = playlist_response['nextPageToken']
            playlist_response = youtube.playlists().list(part='snippet', channelId=channel, maxResults=50, pageToken=next_page_token).execute()
            playlists.extend(playlist_response['items'])

        for playlist in playlists:
            playlist_title = playlist['snippet']['title']
            playlist_id = playlist['id']
            #st.write(f'Playlist Title: {playlist_title}')
            #st.write(f'Playlist ID: {playlist_id}')
        
        video_response = youtube.search().list(part='snippet',channelId=channel,type='video').execute()
        for video in video_response ['items']:
                video_title = video['snippet']['title']
                video_id = video['id']['videoId']
                st.write(f'Video Title: {video_title}')
                st.write(f'Video ID: {video_id}')
        

if __name__ == "__main__":
    main()