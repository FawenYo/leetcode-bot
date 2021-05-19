import sys

from linebot import LineBotApi
from linebot.models import TextMessage, TextSendMessage

from . import flex_template

sys.path.append(".")

import config
import cron
from leetcode import info

line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)


def handle_message(event):
    """Event - User message

    Args:
        event (LINE Event Object): Refer to https://developers.line.biz/en/reference/messaging-api/#message-event
    """
    can_reply = True
    user_id = event.source.user_id
    reply_token = event.reply_token

    # LINE Text message
    if isinstance(event.message, TextMessage):
        user_message = event.message.text
        try:
            if user_message == "帳號操作":
                user_data = config.db.user.find_one({"user_id": user_id})
                LEETCODE_SESSION = user_data["account"]["LeetCode"]["LEETCODE_SESSION"]
                is_login, response, leetcode_session = info.login(
                    LEETCODE_SESSION=LEETCODE_SESSION
                )
                if not is_login:
                    user_data["account"]["LeetCode"]["LEETCODE_SESSION"] = ""
                    config.db.user.update_one(
                        {"_id": user_data["_id"]}, {"$set": user_data}
                    )
                debit = user_data["debit"]
                messages = flex_template.info(user_id=user_id, debit=debit)
            elif user_message == "登入":
                messages = TextSendMessage(
                    text=f"登入網址：\nhttps://liff.line.me/1655767329-J571PLN4"
                )
            elif user_message == "查看結果":
                messages = cron.week_check(replyable=True)
            elif user_message == "查看題目":
                messages = flex_template.check_questions()
            elif user_message == "本週題目":
                user_data = config.db.user.find_one({"user_id": user_id})
                LEETCODE_SESSION = user_data["account"]["LeetCode"]["LEETCODE_SESSION"]
                if LEETCODE_SESSION != "":
                    question_data = config.db.questions.find_one({})
                    question_date = question_data["latest"]["check_date"]
                    required_questions = info.find_question_status(
                        LEETCODE_SESSION=LEETCODE_SESSION,
                        questions=question_data["history"][question_date]["questions"]["required"],
                    )
                    optional_questions = info.find_question_status(
                        LEETCODE_SESSION=LEETCODE_SESSION,
                        questions=question_data["history"][question_date]["questions"]["optional"],
                    )
                    if not required_questions or not optional_questions:
                        user_data["account"]["LeetCode"]["LEETCODE_SESSION"] = ""
                        config.db.user.update_one(
                            {"_id": user_data["_id"]}, {"$set": user_data}
                        )
                        messages = [
                            TextSendMessage(text="LeetCode連線已過期，請重新再登入！"),
                            flex_template.info(
                                user_id=user_id, debit=user_data["debit"]
                            ),
                        ]
                    else:
                        end_date = question_data["latest"]["end_date"]
                        messages = flex_template.set_question(
                            required_questions=required_questions,
                            optional_questions=optional_questions,
                            end_date=end_date,
                        )
                else:
                    messages = TextSendMessage(f"尚未綁定 LeetCode 帳號，請先綁定！")
            else:
                # To single user
                if event.source.type == "user":
                    messages = TextSendMessage(text="不好意思，我聽不懂你在說什麼呢QwQ")
                else:
                    can_reply = False
        except Exception as e:
            can_reply = False
            config.console.print_exception()

        if can_reply:
            line_bot_api.reply_message(reply_token=reply_token, messages=messages)
