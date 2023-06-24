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

#streamlit

api_service_name = "youtube"
api_version = "v3"
api_key = "AIzaSyAVnIpAcy75VNtFRd1avocxjfOVOubbres"
youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=api_key)


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
        else:
            st.write("Invalid channel ID. Please enter a valid YouTube channel ID.")

if __name__ == "__main__":
    main()

#mongoDb

myclient = pymongo.MongoClient("mongodb://localhost:27017/")

mydatabase = myclient["youtube"]

mycollection = mydatabase["details"]

def store_channel_data(channel_data):
    
    result = collection.insert_one(channel_data)
    print("Channel data stored in MongoDB with ID:", result.inserted_id)

#sql

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="12345",
    database="project1"
)

cursor = connection.cursor()

def migrate_channel_data(channel_data):
    # Extract relevant data from the channel_data dictionary
    channel_id = channel_data["id"]
    title = channel_data["snippet"]["title"]
    description = channel_data["snippet"]["description"]
    subscribers = channel_data["statistics"]["subscriberCount"]
    views = channel_data["statistics"]["viewCount"]
    videos = channel_data["statistics"]["videoCount"]

    # Prepare the SQL INSERT statement
    sql = "INSERT INTO project1 (channel_id, title, description, subscribers, views, videos) " \
          "VALUES (%s, %s, %s, %s, %s, %s)"

    # Execute the SQL INSERT statement with the channel data
    values = (channel_id, title, description, subscribers, views, videos)
    cursor.execute(sql, values)

connection.commit()
cursor.close()
connection.close()

connection_string = "mysql+mysqlconnector://root:12345@localhost/project1"
engine = create_engine(connection_string)
session = Session()

# Create a base class for declarative models
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

def get_channel_details(channel_id):
    channel = session.query(Channel).filter_by(channel_id=channel_id).first()
    return channel

session.close()


# Replace with your MySQL connection details
engine = create_engine(connection_string)

def fetch_channel_data(channel_id):
    query = f"SELECT * FROM channel WHERE channel_id = '{channel_id}'"
    df = pd.read_sql_query(query, engine)
    return df

def main():
    st.title("YouTube Channel Migration")

    # Input for YouTube channel ID
    channel_id = st.text_input("Enter YouTube Channel ID")

    if channel_id:
        df = fetch_channel_data(channel_id)

        if not df.empty:
            # Display channel details
            st.subheader("Channel Details")
            st.write(df)

            # You can further visualize the data using Streamlit's data visualization features
            # For example, create a bar chart of subscribers
            st.subheader("Subscribers")
            st.bar_chart(df["subscribers"])
        else:
            st.write("No data found for the given channel ID.")
    else:
        st.write("Please enter a YouTube channel ID.")

if __name__ == "__main__":
    main()
