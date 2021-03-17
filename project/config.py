import json
import os
import threading

import pymongo
from dotenv import load_dotenv
from rich.console import Console

# Load environment variables
load_dotenv()

console = Console()

# LINE Bot 設定
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

# MongoDB
MONGO_USER = os.environ.get("MONGO_USER")
MONGO_PWD = os.environ.get("MONGO_PWD")

client = pymongo.MongoClient(
    f"mongodb+srv://{MONGO_USER}:{MONGO_PWD}@cluster0.1u1l3.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
)

db = client.db
