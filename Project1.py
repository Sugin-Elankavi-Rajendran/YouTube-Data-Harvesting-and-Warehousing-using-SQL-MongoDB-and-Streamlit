import googleapiclient.discovery
import pymongo
from pymongo import MongoClient
import mysql
from config import API_KEY
import streamlit as st
import mysql.connector
import matplotlib.pyplot as plt
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError
from datetime import datetime
from dateutil import parser as date_parser

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

    
    for video in videos:
        video_id = video["id"]["videoId"]
        video_details_response = youtube.videos().list(part='snippet,statistics,contentDetails', id=video_id).execute()
        video_details = video_details_response['items'][0]
        
        snippet = video_details.get('snippet', {})
        statistics = video_details.get('statistics', {})
        content_details = video_details.get('contentDetails', {})
        
        video["snippet"]["title"] = snippet.get("title", "Title Not Available")
        video["snippet"]["description"] = snippet.get("description", "Description Not Available")
        video["snippet"]["publishedAt"] = snippet.get("publishedAt", "Published Date Not Available")
        video["snippet"]["tags"] = snippet.get("tags", [])
        
        video["statistics"] = {
            "viewCount": int(statistics.get("viewCount", 0)),
            "likeCount": int(statistics.get("likeCount", 0)),
            "dislikeCount": int(statistics.get("dislikeCount", 0)),
            "favoriteCount": int(statistics.get("favoriteCount", 0)),
            "commentCount": int(statistics.get("commentCount", 0))
        }
        
        video["contentDetails"] = {
            "duration": content_details.get("duration", "Duration Not Available"),
            "caption": content_details.get("caption", "Not Available")
        }

    return videos

def create_mysql_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="12345",
        database="project1"
    )
    cursor = connection.cursor()

    create_channels_table = """
        CREATE TABLE IF NOT EXISTS channels (
            id INT AUTO_INCREMENT PRIMARY KEY,
            channel_id VARCHAR(255) UNIQUE,
            channel_name VARCHAR(255),
            subscription_count INT,
            channel_views BIGINT,
            channel_description TEXT
        ) ENGINE=InnoDB
    """
    cursor.execute(create_channels_table)

    create_playlists_table = """
        CREATE TABLE IF NOT EXISTS playlists (
            id INT AUTO_INCREMENT PRIMARY KEY,
            channel_id VARCHAR(255),
            playlist_id VARCHAR(255) UNIQUE,
            playlist_title VARCHAR(255)
        ) ENGINE=InnoDB
    """
    cursor.execute(create_playlists_table)
    
    create_videos_table = """
        CREATE TABLE IF NOT EXISTS videos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            channel_id VARCHAR(255), 
            video_id VARCHAR(255) UNIQUE,
            video_title VARCHAR(255),
            video_description TEXT,
            tags TEXT,
            published_at DATETIME,
            view_count INT,
            like_count INT,
            dislike_count INT,
            favorite_count INT,
            comment_count INT,
            duration VARCHAR(50),
            thumbnail TEXT,
            caption_status VARCHAR(50)
        ) ENGINE=InnoDB
    """

    cursor.execute(create_videos_table)

    connection.commit()

    return connection, cursor

def migrate_to_mongodb(channel_data, playlists, videos):
    channel_id = channel_data["Channel_Name"]["Channel_Id"]
    existing_channel = mycollection.find_one({"_id": channel_id})
    
    if not existing_channel:
        try:
            channel_data["_id"] = channel_id
            mycollection.insert_one(channel_data)
        except DuplicateKeyError:
            # If the _id already exists, update the existing document
            mycollection.update_one({"_id": channel_id}, {"$set": channel_data})
    else:
        mycollection.update_one({"_id": channel_id}, {"$set": channel_data})

    for playlist in playlists:
        playlist_id = playlist["id"]
        existing_playlist = mycollection.find_one({"_id": playlist_id})
        if not existing_playlist:
            try:
                playlist["_id"] = playlist_id
                mycollection.insert_one({"_id": playlist_id, "Playlist": playlist})
            except DuplicateKeyError:
                # If the _id already exists, update the existing document
                mycollection.update_one({"_id": playlist_id}, {"$set": {"Playlist": playlist}})
        else:
            mycollection.update_one({"_id": playlist_id}, {"$set": {"Playlist": playlist}})
    
    for video in videos:
        video_id = video["id"]["videoId"]
        existing_video = mycollection.find_one({"_id": video_id})
        if not existing_video:
            try:
                video["_id"] = video_id
                mycollection.insert_one({"_id": video_id, "Video": video})
            except DuplicateKeyError:
                # If the _id already exists, update the existing document
                mycollection.update_one({"_id": video_id}, {"$set": {"Video": video}})
        else:
            mycollection.update_one({"_id": video_id}, {"$set": {"Video": video}})

def migrate_to_mysql(channel_data, playlists, videos, connection, cursor):
    channel_id = channel_data["Channel_Name"]["Channel_Id"]
    
    existing_channel_sql = f"""
    SELECT *
    FROM channels
    WHERE channel_id = '{channel_id}'
    """
    cursor.execute(existing_channel_sql)
    existing_channel = cursor.fetchone()

    if existing_channel:
        # Existing channel, update its attributes
        update_channel_sql = f"""
        UPDATE channels
        SET channel_name = %s,
            subscription_count = %s,
            channel_views = %s,
            channel_description = %s
        WHERE channel_id = %s
        """
        update_channel_values = (
            channel_data["Channel_Name"]["Channel_Name"],
            channel_data["Channel_Name"]["Subscription_Count"],
            channel_data["Channel_Name"]["Channel_Views"],
            channel_data["Channel_Name"]["Channel_Description"],
            channel_id
        )
        cursor.execute(update_channel_sql, update_channel_values)
    else:
        # New channel, insert a new record
        channel_sql = """
        INSERT INTO channels (channel_id, channel_name, subscription_count, channel_views, channel_description)
        VALUES (%s, %s, %s, %s, %s)
        """
        channel_values = (
            channel_id,
            channel_data["Channel_Name"]["Channel_Name"],
            channel_data["Channel_Name"]["Subscription_Count"],
            int(channel_data["Channel_Name"]["Channel_Views"]),
            channel_data["Channel_Name"]["Channel_Description"]
        )
        cursor.execute(channel_sql, channel_values)

    connection.commit()

    for playlist in playlists:
        playlist_id = f"playlist_{playlist['id']}"
        
        existing_playlist_sql = f"""
        SELECT *
        FROM playlists
        WHERE playlist_id = '{playlist_id}'
        """
        cursor.execute(existing_playlist_sql)
        existing_playlist = cursor.fetchone()

        if existing_playlist:
            # Existing playlist, update its attributes
            update_playlist_sql = f"""
            UPDATE playlists
            SET playlist_title = %s
            WHERE playlist_id = %s
            """
            update_playlist_values = (
                playlist['snippet']['title'],
                playlist_id
            )
            cursor.execute(update_playlist_sql, update_playlist_values)
        else:
            # New playlist, insert a new record
            playlist_sql = """
            INSERT INTO playlists (playlist_id, playlist_title)
            VALUES (%s, %s)
            """
            playlist_values = (
                playlist_id,
                playlist['snippet']['title']
            )
            cursor.execute(playlist_sql, playlist_values)

    connection.commit()

    for video in videos:
        video_id = video["id"]["videoId"]
        video["channel_id"] = channel_id
        
        existing_video_sql = f"SELECT * FROM videos WHERE video_id = '{video_id}' AND channel_id = '{channel_id}'"
        cursor.execute(existing_video_sql)
        existing_video = cursor.fetchone()

        if existing_video:
            # Existing video, update its attributes
            update_video_sql = """
            UPDATE videos
            SET video_title = %s,
                video_description = %s,
                tags = %s,
                published_at = %s,
                view_count = %s,
                like_count = %s,
                dislike_count = %s,
                favorite_count = %s,
                comment_count = %s,
                duration = %s,
                thumbnail = %s,
                caption_status = %s
            WHERE video_id = %s AND channel_id = %s
            """
            update_video_values = (
                video["snippet"]["title"],
                video["snippet"]["description"],
                ",".join(video["snippet"].get("tags", [])),
                date_parser.parse(video["snippet"]["publishedAt"]).strftime('%Y-%m-%d %H:%M:%S'),
                video["statistics"]["viewCount"],
                video["statistics"]["likeCount"],
                video["statistics"]["dislikeCount"],
                video["statistics"]["favoriteCount"],
                video["statistics"]["commentCount"],
                video["contentDetails"]["duration"],
                video["snippet"]["thumbnails"]["default"]["url"],
                video["contentDetails"].get("caption", "Not Available"),
                video_id,
                channel_id
            )
            cursor.execute(update_video_sql, update_video_values)
        else:
            # New video, insert a new record
            video_sql = """
            INSERT INTO videos (channel_id, video_id, video_title, video_description, tags, published_at, view_count,
                                like_count, dislike_count, favorite_count, comment_count, duration, thumbnail, caption_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            video_values = (
                channel_id,
                video_id,
                video["snippet"]["title"],
                video["snippet"]["description"],
                ",".join(video["snippet"].get("tags", [])),
                date_parser.parse(video["snippet"]["publishedAt"]).strftime('%Y-%m-%d %H:%M:%S'),
                video["statistics"]["viewCount"],
                video["statistics"]["likeCount"],
                video["statistics"]["dislikeCount"],
                video["statistics"]["favoriteCount"],
                video["statistics"]["commentCount"],
                video["contentDetails"]["duration"],
                video["snippet"]["thumbnails"]["default"]["url"],
                video["contentDetails"].get("caption", "Not Available")
            )
            cursor.execute(video_sql, video_values)
        connection.commit()

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
    st.write("Channels with videos published in the year 2022:")
    st.table(result8)

    query9 = """
    SELECT channel_name, AVG(duration_seconds) AS average_duration
    FROM videos
    INNER JOIN channels ON videos.channel_id = channels.channel_id
    GROUP BY channel_name
    """
    cursor.execute(query9)
    result9 = cursor.fetchall()
    st.write("Average duration of videos in each channel:")
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
    st.write("Videos with the highest number of comments and their corresponding channels:")
    st.table(result10)

def main():
    st.title("YouTube Channel Migration")

    channel_ids = st.text_area("Enter YouTube Channel IDs (one per line):")
    channel_ids = channel_ids.strip().split("\n") if channel_ids else []

    if not channel_ids:
        st.write("No YouTube Channel IDs provided.")
        return

    connection, cursor = create_mysql_connection()
    channels_data = []

    for channel_id in channel_ids:
        channel_data = get_channel_data(channel_id)
        playlists = get_playlist_data(channel_id)
        videos = get_video_data(channel_id)

        channel_data["_id"] = ObjectId()

        for playlist in playlists:
            playlist["_id"] = ObjectId()
        for video in videos:
            video["_id"] = ObjectId()

        try:
            mycollection.insert_one({"_id": channel_id, **channel_data["Channel_Name"]})
            for playlist in playlists:
                playlist_id = f"playlist_{playlist['id']}"
                mycollection.insert_one({"_id": playlist_id, "Playlist": playlist})
            for video in videos:
                video_id = f"video_{video['id']['videoId']}"
                mycollection.insert_one({"_id": video_id, "Video": video})
        except DuplicateKeyError as e:
            st.write(f"Skipping insertion of channel {channel_data['Channel_Name']['Channel_Name']} "
                     f"({channel_data['Channel_Name']['Channel_Id']}) as it already exists in MongoDB.")

        migrate_to_mysql(channel_data, playlists, videos, connection, cursor)

        st.write("Data stored in MongoDB and MySQL!")

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

        st.write("Data stored in MongoDB and MySQL!")

        channels_data.append({
            "Channel": channel_data,
            "Playlists": playlists,
            "Videos": videos
        })

    connection.close()
    cursor.close()
    myclient.close()

    connection, cursor = create_mysql_connection()
    channels_data = retrieve_data_for_channels(channel_ids, connection, cursor)
    
    execute_sql_queries(connection, cursor)

    st.write("--------------------------------------------------")
    st.write("Query Results:")
    st.write("--------------------------------------------------")

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

    cursor.close()
    connection.close()

if __name__ == "__main__":
    main()
