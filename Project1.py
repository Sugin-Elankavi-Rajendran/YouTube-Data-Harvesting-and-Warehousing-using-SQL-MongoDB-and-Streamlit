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

if __name__ == "__main__":
    main()