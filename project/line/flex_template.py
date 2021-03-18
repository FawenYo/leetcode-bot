import json
import re
import sys
from datetime import datetime, timedelta
from typing import List, Tuple

from linebot import LineBotApi
from linebot.models import FlexSendMessage

sys.path.append(".")
import config

line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)


def complete_result(data: List[Tuple[int, List[str]]]) -> FlexSendMessage:
    """本週AC狀況

    Args:
        data (List[Tuple[int, List[str]]]): AC 資料

    Returns:
        FlexSendMessage: 本週AC狀況
    """
    with open("line/model/complete_result.json") as json_file:
        contents = json.load(json_file)
    champions = []
    for user_id in data[0][1]:
        profile = line_bot_api.get_profile(user_id)
        display_name = profile.display_name
        champions.append(display_name)
    contents["body"]["contents"][1]["contents"][0]["contents"][1]["text"] = "\n".join(
        champions
    )
    contents["body"]["contents"][1]["contents"][1]["contents"][1][
        "text"
    ] = f"{data[0][0]}"

    user_count = count_all_users(data=data)
    for each in data:
        count = each[0]
        users = len(each[1])
        try:
            percentage = users / user_count * 100
        except ZeroDivisionError:
            percentage = 0
        template = {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"{count}題 ({percentage}%)",
                    "size": "xs",
                    "margin": "md",
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [{"type": "filler"}],
                            "width": f"{percentage}%",
                            "backgroundColor": "#fac209",
                            "height": "6px",
                        }
                    ],
                    "height": "6px",
                    "backgroundColor": "#fdebae",
                },
            ],
        }
        contents["body"]["contents"].append(template)
    message = FlexSendMessage(alt_text="本週AC狀況", contents=contents)
    return message


def undo_result(data: List[dict]) -> FlexSendMessage:
    """本週未作答狀況

    Args:
        data (List[dict]): 未作答資料

    Returns:
        FlexSendMessage: 本週未作答狀況
    """
    with open("line/model/undo_result.json") as json_file:
        contents = json.load(json_file)
    for each in data:
        template = {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": each["user"], "flex": 5},
                {
                    "type": "text",
                    "text": f"欠 {each['debit']} 元",
                    "flex": 5,
                    "align": "center",
                },
            ],
            "margin": "md",
        }
        contents["body"]["contents"].append(template)
    message = FlexSendMessage(alt_text="本週未作答狀況", contents=contents)
    return message


def count_all_users(data: List[Tuple[int, List[str]]]) -> int:
    """計算使用者總數

    Args:
        data (List[Tuple[int, List[str]]]): AC 資料

    Returns:
        int: 使用者總數
    """
    user_count = 0
    for each in data:
        user_count += len(each[1])
    return user_count
