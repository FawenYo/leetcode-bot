import sys

from linebot import LineBotApi
from linebot.models import *

from . import flex_template

sys.path.append(".")

import config
import cron

line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)


def handle_message(event):
    """事件 - 訊息

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
            if user_message == "查看結果":
                message = cron.check_all_status(replyable=True)
            elif user_message == "查看負債":
                user_data = config.db.user.find_one({"user_id": user_id})
                debit = user_data["debit"]
                message = TextSendMessage(text=f"目前總負債金額：{debit}元")
            else:
                # 面對單一使用者
                if event.source.type == "user":
                    message = TextSendMessage(text="不好意思，我聽不懂你在說什麼呢QwQ")
                else:
                    can_reply = False
        except Exception as e:
            can_reply = False
            config.console.print_exception()

        if can_reply:
            line_bot_api.reply_message(reply_token, message)
