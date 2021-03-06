import sys

from linebot import LineBotApi
from linebot.models import TextMessage, TextSendMessage

from . import flex_template

sys.path.append(".")

import config
import cron

line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)


def handle_message(event):
    """Event - User message

    Args:
        event (LINE Event Object): Refer to https://developers.line.biz/en/reference/messaging-api/#message-event
    """
    can_reply = True
    user_id = event.source.user_id
    reply_token = event.reply_token

    # 文字訊息
    if isinstance(event.message, TextMessage):
        user_message = event.message.text
        try:
            if user_message == "帳號操作":
                user_data = config.db.user.find_one({"user_id": user_id})
                debit = user_data["debit"]
                messages = flex_template.info(user_id=user_id, debit=debit)
            elif user_message == "查看結果":
                messages = cron.week_check(replyable=True)
            else:
                # 面對單一使用者
                if event.source.type == "user":
                    messages = TextSendMessage(text="不好意思，我聽不懂你在說什麼呢QwQ")
                else:
                    can_reply = False
        except Exception as e:
            can_reply = False
            config.console.print_exception()

        if can_reply:
            line_bot_api.reply_message(reply_token=reply_token, messages=messages)
