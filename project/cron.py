import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from linebot import LineBotApi
from linebot.models import *

import config
from line import flex_template

cron = APIRouter()
line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)


# Home Page
@cron.get("/init", response_class=JSONResponse)
async def init():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        check_all_status,
        "cron",
        day_of_week="sun",
        hour=00,
        minute=00,
        second=00,
        timezone=pytz.timezone("Asia/Taipei"),
    )
    message = {"stauts": "success", "message": "已開始定時任務！"}
    return JSONResponse(content=message)


def check_all_status():
    for user in config.db.user.find():
        LEETCODE_SESSION = user["account"]["LeetCode"]["LEETCODE_SESSION"]

        user["question"]["required"]
    return True