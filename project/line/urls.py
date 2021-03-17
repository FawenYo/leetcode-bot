import sys

from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *

from . import message_event

sys.path.append(".")

import config

line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.LINE_CHANNEL_SECRET)

line_app = APIRouter()
templates = Jinja2Templates(directory="templates")


@line_app.post("/callback")
async def callback(request: Request) -> str:
    """LINE Bot Webhook Callback

    Args:
        request (Request): Request Object.

    Raises:
        HTTPException: Signature 驗證失敗

    Returns:
        str: OK
    """
    signature = request.headers["X-Line-Signature"]
    body = await request.body()
    # handle webhook body
    try:
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Missing Parameter")
    return "OK"


@handler.add(MessageEvent, message=(TextMessage))
def handle_message(event):
    """事件 - 訊息

    Args:
        event (LINE Event Object): Refer to https://developers.line.biz/en/reference/messaging-api/#message-event
    """
    message_event.handle_message(event=event)
