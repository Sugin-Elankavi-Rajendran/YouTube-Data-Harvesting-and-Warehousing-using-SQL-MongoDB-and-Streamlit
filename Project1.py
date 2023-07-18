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
        response = youtube.channels().list(part='snippet,statistics',id=channel).execute()
        channel_name = response['items'][0]
        channel_title = channel_name['snippet']['title']
        channel_subscribers = channel_name['statistics']['subscriberCount']
        channel_videos = channel_name['statistics']['videoCount']
        channel_description = channel_name ['snippet']['description']
        
        st.write (f'Channel Title: {channel_title}')
        st.write (f'Channel Subscribers: {channel_subscribers}')
        st.write (f'Channel Videos: {channel_videos}')
        st.write (f'Channel Description: {channel_description}')

if __name__ == "__main__":
    main()