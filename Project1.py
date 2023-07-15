import googleapiclient.discovery
import googleapiclient.errors
from pymongo import MongoClient
import pymongo
import mysql.connector
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer
import streamlit as st
import pandas as pd


api_service_name = "youtube"
api_version = "v3"
api_key = input("Enter API Key: ")

youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=api_key)


myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydatabase = myclient["youtube"]
mycollection = mydatabase["details"]

def store_channel_data(channel_data):
    result = mycollection.insert_one(channel_data)
    print("Channel data stored in MongoDB with ID:", result.inserted_id)


connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="12345",
    database="project1"
)

cursor = connection.cursor()

def migrate_channel_data(channel_data):
    channel_id = channel_data["id"]
    title = channel_data["snippet"]["title"]
    description = channel_data["snippet"]["description"]
    subscribers = channel_data["statistics"]["subscriberCount"]
    views = channel_data["statistics"]["viewCount"]
    videos = channel_data["statistics"]["videoCount"]

    sql_create_table = """
    CREATE TABLE IF NOT EXISTS channel (
        id INT PRIMARY KEY AUTO_INCREMENT,
        channel_id VARCHAR(255),
        title VARCHAR(255),
        description VARCHAR(255),
        subscribers INT,
        views INT,
        videos INT
    )
    """
    cursor.execute(sql_create_table)

    sql_insert_data = """
    INSERT INTO channel (channel_id, title, description, subscribers, views, videos)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = (channel_id, title, description, subscribers, views, videos)
    cursor.execute(sql_insert_data, values)
    connection.commit()

connection_string = "mysql+mysqlconnector://root:12345@localhost/project1"
engine = create_engine(connection_string)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

class Channel(Base):
    __tablename__ = "channel"

    id = Column(Integer, primary_key=True)
    channel_id = Column(String(255))
    title = Column(String(255))
    description = Column(String(255))
    subscribers = Column(Integer)
    views = Column(Integer)
    videos = Column(Integer)

def fetch_channel_data(channel_id):
    query = f"SELECT * FROM channel WHERE channel_id = '{channel_id}'"
    df = pd.read_sql_query(query, engine)
    return df

def get_channel_details(channel_id):
    response = youtube.channels().list(
        part="snippet,statistics",
        id=channel_id
    ).execute()

    if "items" in response:
        channel = response["items"][0]
        return channel
    else:
        return None

def main():
    st.title("YouTube Channel Migration")
    
    channel_id = st.text_input("Enter YouTube Channel ID")

    if channel_id:
        channel = get_channel_details(channel_id)
        if channel:
            st.subheader("Channel Details")
            st.write("Title:", channel["snippet"]["title"])
            st.write("Description:", channel["snippet"]["description"])
            st.write("Subscribers:", channel["statistics"]["subscriberCount"])
            st.write("Total Views:", channel["statistics"]["viewCount"])
            st.write("Total Videos:", channel["statistics"]["videoCount"])

            migrate_channel = st.checkbox("Migrate this channel")

            if migrate_channel:
                st.write("Channel", channel["snippet"]["title"], "is selected for migration!")
                store_channel_data(channel)
                migrate_channel_data(channel)

        else:
            st.write("Invalid channel ID. Please enter a valid YouTube channel ID.")
    
    
    if st.button("Fetch Channel Data"):
        if channel_id:
            df = fetch_channel_data(channel_id)
            st.subheader("Channel Data")
            st.dataframe(df)

            
            st.subheader("Subscribers vs Views")
            st.bar_chart(df[["subscribers", "views"]])
        else:
            st.warning("Please enter a YouTube channel ID first.")

if __name__ == "__main__":
    main()
