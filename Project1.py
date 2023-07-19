import googleapiclient.discovery
import pymongo
from pymongo import MongoClient
import mysql
from config import API_KEY
import streamlit as st
import mysql.connector
import matplotlib.pyplot as plt

api_service_name = "youtube"
api_version = "v3"

youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=API_KEY)

myclient = MongoClient("mongodb://localhost:27017/")
mydatabase = myclient["youtube"]
mycollection = mydatabase["details"]


def get_channel_data(channel_id):
    response = youtube.channels().list(part='snippet,statistics', id=channel_id).execute()
    channel_data = response['items'][0]

    channel_title = channel_data['snippet']['title']
    channel_subscribers = int(channel_data['statistics']['subscriberCount'])
    channel_views = int(channel_data['statistics']['viewCount'])
    channel_description = channel_data['snippet']['description']

    return {
        "Channel_Name": {
            "Channel_Name": channel_title,
            "Channel_Id": channel_id,
            "Subscription_Count": channel_subscribers,
            "Channel_Views": channel_views,
            "Channel_Description": channel_description,
            "Playlist_Id": None
        }
    }


def get_playlist_data(channel_id):
    playlist_response = youtube.playlists().list(part='snippet', channelId=channel_id, maxResults=5).execute()
    playlists = playlist_response['items']

    # while 'nextPageToken' in playlist_response:
    #     next_page_token = playlist_response['nextPageToken']
    #     playlist_response = youtube.playlists().list(part='snippet', channelId=channel_id, maxResults=5, pageToken=next_page_token).execute()
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

def create_mysql_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="12345",
        database="project1"
    )
    cursor = connection.cursor()
    return connection, cursor


def migrate_to_mysql(channel_data, playlists, videos, connection, cursor):
    
    channel_sql = """
    INSERT INTO channels (channel_id, channel_name, subscription_count, channel_views, channel_description)
    VALUES (%s, %s, %s, %s, %s)
    """
    channel_values = (
        channel_data["Channel_Name"]["Channel_Id"],
        channel_data["Channel_Name"]["Channel_Name"],
        channel_data["Channel_Name"]["Subscription_Count"],
        channel_data["Channel_Name"]["Channel_Views"],
        channel_data["Channel_Name"]["Channel_Description"]
    )
    cursor.execute(channel_sql, channel_values)
    connection.commit()

    
    for playlist in playlists:
        playlist_sql = """
        INSERT INTO playlists (playlist_id, playlist_title)
        VALUES (%s, %s)
        """
        playlist_values = (
            playlist["id"],
            playlist["snippet"]["title"]
        )
        cursor.execute(playlist_sql, playlist_values)
        connection.commit()

    
    for video in videos:
        video_sql = """
        INSERT INTO videos (video_id, video_title, video_description, tags, published_at, view_count,
                            like_count, dislike_count, favorite_count, comment_count, duration, thumbnail, caption_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        video_values = (
            video["id"]["videoId"],
            video["snippet"]["title"],
            video["snippet"]["description"],
            ",".join(video["snippet"].get("tags", [])),
            video["snippet"]["publishedAt"],
            int(video["statistics"]["viewCount"]),
            int(video["statistics"]["likeCount"]),
            int(video["statistics"]["dislikeCount"]),
            int(video["statistics"]["favoriteCount"]),
            int(video["statistics"]["commentCount"]),
            video["contentDetails"]["duration"],
            video["snippet"]["thumbnails"]["default"]["url"],
            video["contentDetails"].get("caption", "Not Available")
        )
        cursor.execute(video_sql, video_values)
        connection.commit()

def create_mysql_connection():
    connection = mysql.connector.connect(
        host="your_mysql_host",
        user="your_mysql_username",
        password="your_mysql_password",
        database="your_database_name"
    )
    cursor = connection.cursor()
    return connection, cursor


def retrieve_data_for_channels(channel_ids, connection, cursor):
    channels_data = []

    for channel_id in channel_ids:
        
        channel_sql = f"""
        SELECT *
        FROM channels
        WHERE channel_id = '{channel_id}'
        """
        cursor.execute(channel_sql)
        channel_data = cursor.fetchone()

        
        playlists_sql = f"""
        SELECT *
        FROM playlists
        WHERE channel_id = '{channel_id}'
        """
        cursor.execute(playlists_sql)
        playlists_data = cursor.fetchall()

        
        videos_sql = f"""
        SELECT *
        FROM videos
        WHERE channel_id = '{channel_id}'
        """
        cursor.execute(videos_sql)
        videos_data = cursor.fetchall()

        channels_data.append({
            "Channel": channel_data,
            "Playlists": playlists_data,
            "Videos": videos_data
        })

    return channels_data

def execute_sql_queries(connection, cursor):
    
    query1 = """
    SELECT video_title, channel_name
    FROM videos
    INNER JOIN channels ON videos.channel_id = channels.channel_id
    """
    cursor.execute(query1)
    result1 = cursor.fetchall()
    st.write("Names of all videos and their corresponding channels:")
    st.table(result1)

    
    query2 = """
    SELECT channel_name, COUNT(*) AS num_videos
    FROM videos
    INNER JOIN channels ON videos.channel_id = channels.channel_id
    GROUP BY channel_name
    ORDER BY num_videos DESC
    """
    cursor.execute(query2)
    result2 = cursor.fetchall()
    st.write("Channels with the most number of videos:")
    st.table(result2)

    
    query3 = """
    SELECT video_title, channel_name, view_count
    FROM videos
    INNER JOIN channels ON videos.channel_id = channels.channel_id
    ORDER BY view_count DESC
    LIMIT 10
    """
    cursor.execute(query3)
    result3 = cursor.fetchall()
    st.write("Top 10 most viewed videos and their respective channels:")
    st.table(result3)

    
    query4 = """
    SELECT video_title, COUNT(*) AS num_comments
    FROM comments
    INNER JOIN videos ON comments.video_id = videos.video_id
    GROUP BY video_title
    """
    cursor.execute(query4)
    result4 = cursor.fetchall()
    st.write("Number of comments on each video:")
    st.table(result4)
    
    video_titles = [row[0] for row in result4]
    num_comments = [row[1] for row in result4]

    plt.figure(figsize=(10, 6))
    plt.bar(video_titles, num_comments)
    plt.xlabel('Video Titles')
    plt.ylabel('Number of Comments')
    plt.title('Number of Comments on Each Video')
    plt.xticks(rotation=45)
    st.pyplot()

    
    query5 = """
    SELECT video_title, channel_name, like_count
    FROM videos
    INNER JOIN channels ON videos.channel_id = channels.channel_id
    ORDER BY like_count DESC
    LIMIT 10
    """
    cursor.execute(query5)
    result5 = cursor.fetchall()
    st.write("Videos with the highest number of likes and their corresponding channels:")
    st.table(result5)

    
    query6 = """
    SELECT video_title, SUM(like_count) AS total_likes, SUM(dislike_count) AS total_dislikes
    FROM videos
    GROUP BY video_title
    """
    cursor.execute(query6)
    result6 = cursor.fetchall()
    st.write("Total likes and dislikes for each video:")
    st.table(result6)

    
    query7 = """
    SELECT channel_name, SUM(view_count) AS total_views
    FROM videos
    INNER JOIN channels ON videos.channel_id = channels.channel_id
    GROUP BY channel_name
    """
    cursor.execute(query7)
    result7 = cursor.fetchall()
    st.write("Total views for each channel:")
    st.table(result7)

    
    query8 = """
    SELECT DISTINCT channel_name
    FROM videos
    INNER JOIN channels ON videos.channel_id = channels.channel_id
    WHERE YEAR(published_at) = 2022
    """
    cursor.execute(query8)
    result8 = cursor.fetchall()
    st.write("Question 8: Channels with videos published in the year 2022")
    st.table(result8)

    
    query9 = """
    SELECT channel_name, AVG(duration_seconds) AS average_duration
    FROM videos
    INNER JOIN channels ON videos.channel_id = channels.channel_id
    GROUP BY channel_name
    """
    cursor.execute(query9)
    result9 = cursor.fetchall()
    st.write("Question 9: Average duration of videos in each channel")
    st.table(result9)

    
    query10 = """
    SELECT video_title, channel_name, COUNT(*) AS num_comments
    FROM comments
    INNER JOIN videos ON comments.video_id = videos.video_id
    INNER JOIN channels ON videos.channel_id = channels.channel_id
    GROUP BY video_title, channel_name
    ORDER BY num_comments DESC
    LIMIT 10
    """
    cursor.execute(query10)
    result10 = cursor.fetchall()
    st.write("Question 10: Videos with the highest number of comments and their corresponding channels")
    st.table(result10)

def main():
    st.title("YouTube Channel Migration")

    channel_ids = st.text_area("Enter YouTube Channel IDs (one per line):")
    channel_ids = channel_ids.strip().split("\n") if channel_ids else []

    for channel_id in channel_ids:
        channel_data = get_channel_data(channel_id)
        playlists = get_playlist_data(channel_id)
        videos = get_video_data(channel_id)

        
        mycollection.insert_one(channel_data["Channel_Name"])
        for playlist in playlists:
            mycollection.insert_one({"Playlist": playlist})
        for video in videos:
            mycollection.insert_one({"Video": video})

        st.write("---------------------------------------------------------------")
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

    connection, cursor = create_mysql_connection()

    
    mycollection.insert_one(channel_data["Channel_Name"])
    for playlist in playlists:
        mycollection.insert_one({"Playlist": playlist})
    for video in videos:
        mycollection.insert_one({"Video": video})

    
    migrate_to_mysql(channel_data, playlists, videos, connection, cursor)

    
    st.write("Data stored in MySQL!")

    channel_ids = st.text_area("Enter YouTube Channel IDs (one per line):")
    channel_ids = channel_ids.strip().split("\n") if channel_ids else []

    
    channels_data = retrieve_data_for_channels(channel_ids, connection, cursor)

    
    for channel_data in channels_data:
        channel_info = channel_data["Channel"]
        st.write(f"Channel Name: {channel_info[1]}")
        st.write(f"Channel ID: {channel_info[0]}")
        st.write(f"Channel Subscribers: {channel_info[2]}")
        st.write(f"Channel Views: {channel_info[3]}")
        st.write(f"Channel Description: {channel_info[4]}")

        playlists_info = channel_data["Playlists"]
        st.write("Playlists:")
        for playlist_info in playlists_info:
            st.write(f"Playlist Title: {playlist_info[1]}")
            st.write(f"Playlist ID: {playlist_info[0]}")

        videos_info = channel_data["Videos"]
        st.write("Videos:")
        for video_info in videos_info:
            st.write(f"Video Title: {video_info[1]}")
            st.write(f"Video ID: {video_info[0]}")

        st.write("--------------------------------------------------")

    execute_sql_queries(connection, cursor)
    
    cursor.close()
    connection.close()
    
if __name__ == "__main__":
    main()
