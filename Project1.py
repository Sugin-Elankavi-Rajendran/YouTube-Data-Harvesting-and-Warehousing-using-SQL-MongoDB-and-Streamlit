import googleapiclient.discovery
import pymongo
from pymongo import MongoClient
import mysql

api_service_name = "youtube"
api_version = "v3"
api_key = input("Enter API Key: ")

youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=api_key)

myclient = MongoClient("mongodb://localhost:27017/")
mydatabase = myclient["youtube"]
mycollection = mydatabase["details"]


