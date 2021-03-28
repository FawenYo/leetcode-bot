import sys
import threading
from typing import List

from linebot import LineBotApi

sys.path.append(".")
import config

line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)


def update_user_profile() -> None:
    """更新使用者名稱"""
    threads: List[threading.Thread] = []
    for user_data in config.db.user.find({}):
        thread = threading.Thread(target=update_database, args=(user_data,))
        threads.append(thread)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


def update_database(user_data: dict) -> None:
    user_id = user_data["user_id"]
    try:
        profile = line_bot_api.get_profile(user_id)
        display_name = profile.display_name

        user_data["display_name"] = display_name
        config.db.user.update_one({"_id": user_data["_id"]}, {"$set": user_data})
    except:
        pass
