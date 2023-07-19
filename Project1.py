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
        channel_data = response['items'][0]
            
        channel_id = channel_data['id']
        channel_title = channel_data['snippet']['title']
        channel_subscribers = int(channel_data['statistics']['subscriberCount'])
        channel_views = int(channel_data['statistics']['viewCount'])
        channel_description = channel_data['snippet']['description']
        
        channel_doc = {
            "Channel_Name": {
                "Channel_Name": channel_title,
                "Channel_Id": channel_id,
                "Subscription_Count": channel_subscribers,
                "Channel_Views": channel_views,
                "Channel_Description": channel_description,
                "Playlist_Id": None
            }
        }       
        
        st.write(f'Channel Name: {channel_title}')
        st.write(f'Channel ID: {channel_id}')
        st.write(f'Channel Subscribers: {channel_subscribers}')
        st.write(f'Channel Views: {channel_views}')
        st.write(f'Channel Description: {channel_description}')
        
        playlist_response = youtube.playlists().list(part='snippet',channelId=channel,maxResults=5).execute()
        playlists = playlist_response['items']

        while 'nextPageToken' in playlist_response:
            next_page_token = playlist_response['nextPageToken']
            playlist_response = youtube.playlists().list(part='snippet', channelId=channel, maxResults=5, pageToken=next_page_token).execute()
            playlists.extend(playlist_response['items'])

        for playlist in playlists:
            playlist_title = playlist['snippet']['title']
            playlist_id = playlist['id']
            
            playlist_doc = {
                "Playlist_Id": playlist_id,
                "Playlist_Title": playlist_title,
                "Videos": {}
            }
            
            channel_doc["Channel_Name"]["Playlist_Id"] = playlist_id
                
            st.write(f'Playlist Title: {playlist_title}')
            st.write(f'Playlist ID: {playlist_id}')
                    
            video_response = youtube.playlistItems().list(part='snippet', playlistId=playlist_id, maxResults=50).execute()
            videos = video_response['items']
            
            while 'nextPageToken' in video_response:
                next_page_token = video_response['nextPageToken']
                video_response = youtube.playlistItems().list(part='snippet', playlistId=playlist_id, maxResults=50,pageToken=next_page_token).execute()
                videos.extend(video_response['items'])
            
            for video in videos:
                video_data = video['snippet']
                video_id = video_data['resourceId']['videoId']
                video_title = video_data['title']
                video_description = video_data['description']
                tags = video_data.get('tags', [])
                published_at = video_data['publishedAt']
                view_count = int(video_data['statistics']['viewCount'])
                like_count = int(video_data['statistics']['likeCount'])
                dislike_count = int(video_data['statistics']['dislikeCount'])
                favorite_count = int(video_data['statistics']['favoriteCount'])
                comment_count = int(video_data['statistics']['commentCount'])
                duration = video_data['contentDetails']['duration']
                thumbnail = video_data['thumbnails']['default']['url']
                caption_status = video_data['contentDetails'].get('caption', 'Not Available')
                
                
                video_doc = {
                    "Video_Id": video_id,
                    "Video_Name": video_title,
                    "Video_Description": video_description,
                    "Tags": tags,
                    "PublishedAt": published_at,
                    "View_Count": view_count,
                    "Like_Count": like_count,
                    "Dislike_Count": dislike_count,
                    "Favorite_Count": favorite_count,
                    "Comment_Count": comment_count,
                    "Duration": duration,
                    "Thumbnail": thumbnail,
                    "Caption_Status": caption_status,
                    "Comments": {}
                }
                
                
                playlist_doc["Videos"][video_id] = video_doc
                
                st.write(f'Video Title: {video_title}')
                st.write(f'Video ID: {video_id}')
                
                comment_response = youtube.commentThreads().list(part='snippet', videoId=video_id,
                                                                      maxResults=20).execute()
                comments = comment_response['items']

                for comment in comments:
                    comment_data = comment['snippet']['topLevelComment']['snippet']
                    comment_id = comment['id']
                    comment_text = comment_data['textDisplay']
                    comment_author = comment_data['authorDisplayName']
                    comment_published_at = comment_data['publishedAt']

                    
                    comment_doc = {
                        "Comment_Id": comment_id,
                        "Comment_Text": comment_text,
                        "Comment_Author": comment_author,
                        "Comment_PublishedAt": comment_published_at
                    }

                    
                    video_doc["Comments"][comment_id] = comment_doc

                    st.write(f'Comment: {comment_text}')
                    st.write(f'Author: {comment_author}')
                    st.write(f'Published At: {comment_published_at}')
                
                mycollection.insert_one(video_doc)
            
            mycollection.insert_one(playlist_doc)   
        
        mycollection.insert_one(channel_doc)
                        
        migrate_channel = st.checkbox("Migrate this channel")
        
        if migrate_channel:
            st.write(f"Channel {channel_title} is selected for migration!")
    
    else:
        st.write("Invalid channel ID. Please enter a valid YouTube channel ID.")
        
if __name__ == "__main__":
    main()