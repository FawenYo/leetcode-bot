import sys
from datetime import datetime

import pytz
from linebot import LineBotApi
from linebot.models import *

sys.path.append(".")

import config

line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)


def handle_follow(event):
    """Event - New user add to LINE Bot

    Args:
        event (LINE Event Object): Refer to https://developers.line.biz/en/reference/messaging-api/#follow-event
    """
    profile = line_bot_api.get_profile(event.source.user_id)
    display_name = profile.display_name
    now = datetime.now(tz=pytz.timezone("Asia/Taipei"))
    data = {
        "user_id": event.source.user_id,
        "display_name": display_name,
        "debit": 0,
        "add_time": now,
        "account": {"LeetCode": {"LEETCODE_SESSION": ""}},
        "LeetCode": {},
    }
    config.db.user.insert_one(data)


def handle_unfollow(event):
    """Event - User ban LINE Bot

    Args:
        event (LINE Event Object): Refer to https://developers.line.biz/en/reference/messaging-api/#unfollow-event
    """
    config.db.user.delete_one({"user_id": event.source.user_id})
