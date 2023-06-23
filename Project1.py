import googleapiclient.discovery
import googleapiclient.errors
from pymongo import MongoClient
import pymongo
import mysql.connector
from sqlalchemy import create_engine, text


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

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="12345",
    database="project1"
)

cursor = connection.cursor()
create_table = """
    CREATE TABLE videos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255),
        view_count INT,
    )
"""
cursor.execute(create_table)

for video_data in youtube_data:
    insert_query = """
        INSERT INTO videos (title, view_count)
        VALUES (%s, %s)
    """
    data = (video_data["title"], video_data["view_count"])  
    cursor.execute(insert_query, data)

connection.commit()
cursor.close()
connection.close()

connection_string = "mysql+mysqlconnector://root:12345@localhost/project1"
engine = create_engine(connection_string)

channel_id = "UCS2pJAOOJYak8PpB9oV1LdA" 

query = text("""
    SELECT v.title, v.view_count, c.channel_name
    FROM videos v
    JOIN channels c ON v.channel_id = c.id
    WHERE c.channel_id = :channel_id
""")

result = engine.execute(query, channel_id=channel_id)

for row in result:
    video_title = row.title
    view_count = row.view_count
    channel_name = row.channel_name

engine.dispose()

