import sys

from linebot import LineBotApi
from linebot.models import *

from . import flex_template

sys.path.append(".")

import config
import leetcode.info

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
        user_message = user_message.replace("＠", "@")
        try:
            if "測試" in user_message:
                message = TextSendMessage(text=user_message)
                line_bot_api.reply_message(reply_token, message)

            else:
                # 面對單一使用者
                if event.source.type == "user":
                    message = TextSendMessage(
                        text="不好意思，我聽不懂你在說什麼呢QwQ\n如需要幫助，請輸入「客服」尋求幫忙"
                    )
                else:
                    can_reply = False
        except Exception as e:
            can_reply = False
            config.console.print_exception()

        if can_reply:
            line_bot_api.reply_message(reply_token, message)
