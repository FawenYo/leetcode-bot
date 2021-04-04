import json
import sys
from datetime import date, datetime
from typing import List, Tuple

from linebot import LineBotApi
from linebot.models import FlexSendMessage

sys.path.append(".")
import config

line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)


weekday_text_map = {0: "一", 1: "二", 2: "三", 3: "四", 4: "五", 5: "六", 6: "日"}


def set_question(
    required_questions: List[str],
    optional_questions: List[str],
    end_date: str,
    date_status: str = "本週",
) -> FlexSendMessage:
    with open("line/model/set_question.json") as json_file:
        contents = json.load(json_file)

    contents["body"]["contents"][0]["text"] = f"{date_status}題目"
    for question_data in required_questions:
        question_title, question_slug = question_data.split("__||__")
        if "未完成" in question_title:
            text_color = "#ff0000"
        elif "已完成" in question_title:
            text_color = "#009100"
        else:
            text_color = "#666666"
        temp = {
            "type": "text",
            "text": question_title,
            "wrap": True,
            "color": text_color,
            "size": "sm",
            "decoration": "underline",
            "action": {
                "type": "uri",
                "label": "action",
                "uri": f"https://leetcode.com/problems/{question_slug}/",
            },
        }
        contents["body"]["contents"][1]["contents"][0]["contents"][1][
            "contents"
        ].append(temp)

    for question_data in optional_questions:
        question_title, question_slug = question_data.split("__||__")
        if "未完成" in question_title:
            text_color = "#ff0000"
        elif "已完成" in question_title:
            text_color = "#009100"
        else:
            text_color = "#666666"
        temp = {
            "type": "text",
            "text": question_title,
            "wrap": True,
            "color": text_color,
            "size": "sm",
            "decoration": "underline",
            "action": {
                "type": "uri",
                "label": "action",
                "uri": f"https://leetcode.com/problems/{question_slug}/",
            },
        }
        contents["body"]["contents"][1]["contents"][2]["contents"][1][
            "contents"
        ].append(temp)
    end_date_format = datetime.strptime(end_date, "%Y/%m/%d")
    contents["footer"]["contents"][0][
        "text"
    ] = f"截止日期：{end_date_format.month}/{end_date_format.day}（{weekday_text_map[end_date_format.weekday()]}）18:00:00"
    message = FlexSendMessage(alt_text=f"{date_status}題目", contents=contents)
    return message


def info(user_id: str, debit: int) -> FlexSendMessage:
    """User info summary

    Args:
        user_id (str): User's LINE ID.

    Returns:
        FlexSendMessage: 使用者資訊
    """
    with open("line/model/info.json") as json_file:
        contents = json.load(json_file)

    profile = line_bot_api.get_profile(user_id)
    display_name = profile.display_name
    contents["body"]["contents"][1]["contents"][0]["contents"][1]["text"] = display_name

    user_data = config.db.user.find_one({"user_id": user_id})
    if user_data["account"]["LeetCode"]["LEETCODE_SESSION"] != "":
        contents["footer"]["contents"] = [contents["footer"]["contents"][1]]
        login_text = "已經登入"
        login_color = "#00FF00"
    else:
        login_text = "尚未登入"
        login_color = "#FF0000"
    contents["body"]["contents"][1]["contents"][1]["contents"][1]["text"] = login_text
    contents["body"]["contents"][1]["contents"][1]["contents"][1]["color"] = login_color

    contents["body"]["contents"][1]["contents"][2]["contents"][1]["text"] = f"{debit}元"
    message = FlexSendMessage(alt_text="使用者資訊", contents=contents)
    return message


def complete_result(data: List[Tuple[int, List[str]]]) -> FlexSendMessage:
    """Week Accepted result

    Args:
        data (List[Tuple[int, List[str]]]): Accepted data.

    Returns:
        FlexSendMessage: 本週AC狀況
    """
    with open("line/model/complete_result.json") as json_file:
        contents = json.load(json_file)
    user_count = count_all_users(data=data)
    for count, users in data:
        try:
            percentage = len(users) / user_count * 100
        except ZeroDivisionError:
            percentage = 0
        template = {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"{count}題 ({len(users)}人，佔{round(percentage, 4)}%)",
                    "size": "xs",
                    "margin": "md",
                },
                {"type": "text", "text": ", ".join(users), "size": "xxs", "wrap": True},
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

    contents["body"]["contents"][1]["contents"][0]["contents"][1]["text"] = "\n".join(
        data[0][1]
    )
    contents["body"]["contents"][1]["contents"][1]["contents"][1][
        "text"
    ] = f"{data[0][0]}"
    message = FlexSendMessage(alt_text="本週AC狀況", contents=contents)
    return message


def undo_result(data: List[dict]) -> FlexSendMessage:
    """Week undo result

    Args:
        data (List[dict]): Undo data.

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
                    "text": f"貢獻{each['debit']}元",
                    "flex": 5,
                    "align": "center",
                },
            ],
            "margin": "md",
        }
        contents["body"]["contents"].append(template)
    message = FlexSendMessage(alt_text="本週未作答狀況", contents=contents)
    return message


def unbound_users(data: List[dict]) -> FlexSendMessage:
    """Unbound users

    Args:
        data (List[dict]): Unbound users' data.

    Returns:
        FlexSendMessage: 帳號綁定狀況
    """
    with open("line/model/unbound_users.json") as json_file:
        contents = json.load(json_file)
    for each in data:
        template = {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": each["user"]},
            ],
            "margin": "md",
        }
        contents["body"]["contents"].append(template)
    message = FlexSendMessage(alt_text="帳號綁定狀況", contents=contents)
    return message


def count_all_users(data: List[Tuple[int, List[str]]]) -> int:
    """Count all users

    Args:
        data (List[Tuple[int, List[str]]]): Accepted data.

    Returns:
        int: Total users count.
    """
    user_count = 0
    for each in data:
        user_count += len(each[1])
    return user_count


def check_questions() -> FlexSendMessage:
    """Select LeetCode history date

    Returns:
        FlexSendMessage: 查看題目
    """
    with open("line/model/check_questions.json") as json_file:
        contents = json.load(json_file)
    message = FlexSendMessage(alt_text="查看題目", contents=contents)
    return message
