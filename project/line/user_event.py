import sys
from datetime import datetime

import pytz
from linebot import LineBotApi
from linebot.models import *

from . import flex_template

sys.path.append(".")

import config

line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)


def handle_follow(event):
    """Event - New user add to LINE Bot

    Args:
        event (LINE Event Object): Refer to https://developers.line.biz/en/reference/messaging-api/#follow-event
    """
    user_id = event.source.user_id
    profile = line_bot_api.get_profile(user_id)
    display_name = profile.display_name
    now = datetime.now(tz=pytz.timezone("Asia/Taipei"))
    data = {
        "user_id": user_id,
        "display_name": display_name,
        "debit": 0,
        "add_time": now,
        "account": {"LeetCode": {"LEETCODE_SESSION": ""}},
        "LeetCode": {},
    }
    config.db.user.insert_one(data)

    messages = flex_template.info(user_id=user_id, debit=0)
    line_bot_api.push_message(to=user_id, messages=messages)


def handle_unfollow(event):
    """Event - User ban LINE Bot

    Args:
        event (LINE Event Object): Refer to https://developers.line.biz/en/reference/messaging-api/#unfollow-event
    """
    config.db.user.delete_one({"user_id": event.source.user_id})
