import sys

from linebot import LineBotApi
from linebot.models import *

from . import flex_template

sys.path.append(".")

import config
from leetcode import info

line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)


def handle_postback(event):
    """Event - Postback

    Args:
        event (LINE Event Object): Refer to https://developers.line.biz/en/reference/messaging-api/#postback-event
    """
    user_id = event.source.user_id
    reply_token = event.reply_token
    postback_data = event.postback.data

    if postback_data == "歷史題目":
        history_date = event.postback.params["date"]
        history_date = history_date.replace("-", "/")
        question_data = config.db.questions.find_one({})

        if history_date in question_data["history"]:
            user_data = config.db.user.find_one({"user_id": user_id})
            LEETCODE_SESSION = user_data["account"]["LeetCode"]["LEETCODE_SESSION"]
            csrftoken = user_data["account"]["LeetCode"]["csrftoken"]
            if LEETCODE_SESSION != "":
                question_data = config.db.questions.find_one({})
                required_questions = info.find_question_status(
                    LEETCODE_SESSION=LEETCODE_SESSION,
                    csrftoken=csrftoken,
                    questions=question_data["history"][history_date]["questions"][
                        "required"
                    ],
                )
                optional_questions = info.find_question_status(
                    LEETCODE_SESSION=LEETCODE_SESSION,
                    csrftoken=csrftoken,
                    questions=question_data["history"][history_date]["questions"][
                        "optional"
                    ],
                )
                end_date = question_data["latest"]["end_date"]
                messages = flex_template.set_question(
                    required_questions=required_questions,
                    optional_questions=optional_questions,
                    end_date=history_date,
                    date_status="歷史",
                )
            else:
                messages = TextSendMessage("尚未綁定 LeetCode 帳號，請先綁定！")
        else:
            messages = TextSendMessage("查無題目，請確認日期是否選擇正確！")
    else:
        messages = TextSendMessage(text=f"我不知道你在幹嘛QwQ")
    line_bot_api.reply_message(reply_token=reply_token, messages=messages)
