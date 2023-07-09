import googleapiclient.discovery
import googleapiclient.errors

api_name = "youtube"
api_version = "v3"
youtube_api_key = ""

youtube = googleapiclient.discovery(api_name,api_version,developerKey=youtube_api_key)