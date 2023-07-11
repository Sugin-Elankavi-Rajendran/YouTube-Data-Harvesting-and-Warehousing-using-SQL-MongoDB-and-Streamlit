import googleapiclient.discovery
import googleapiclient.errors
from pymongo import MongoClient
import pymongo

api_name = "youtube"
api_version = "v3"
youtube_api_key = input("Enter API Key:")

youtube = googleapiclient.discovery.build(api_name,api_version,developerKey=youtube_api_key)

myclient = pymongo.MongoClient("mongodb://localhost/27017")
mydatabase = myclient["youtube"]
mycollection = mydatabase ["details"]

