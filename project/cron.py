from datetime import datetime
from typing import List, Tuple

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from linebot import LineBotApi
from linebot.models import *

import config
from leetcode.info import check_work_status, update_status
from line import flex_template

cron = APIRouter()
line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)


@cron.get("/init", response_class=JSONResponse)
async def init() -> JSONResponse:
    """Init Cron jobs

    Returns:
        JSONResponse: Job status
    """
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


def check_all_status(
    replyable: bool = False,
    current_date: str = datetime.strftime(datetime.now(), "%Y/%m/%d"),
):
    """週末清算

    Args:
        replyable (bool, optional): 是否可以使用 reply 回覆. Defaults to False.
        current_date (str, optional): 結算日期. Defaults to datetime.strftime(datetime.now(), "%Y/%m/%d").
    """
    update_user_profile()
    user_status = {}
    undo_users = []

    question_data = config.db.questions.find_one({})
    required_question = question_data["latest"]

    for user in config.db.user.find():
        work_status = check_work_status(
            user_id=user["user_id"], required_question=required_question
        )
        user_status[user["user_id"]] = {
            "display_name": user["display_name"],
            "result": work_status,
        }

        if not work_status["complete"]:
            undo_users.append(
                {
                    "user_id": user["user_id"],
                    "user": user["display_name"],
                    "debit": work_status["debit"],
                }
            )
            if not replyable:
                update_user_debit(user_id=user["user_id"], debit=work_status["debit"])
    if not replyable:
        # Update Question history result
        question_data = config.db.questions.find_one({})
        question_data["history"][current_date]["result"] = user_status
        config.db.questions.update_one({}, {"$set": question_data})

    sorted_status = sort_complete_status(user_status=user_status)

    message = [
        flex_template.complete_result(data=sorted_status),
        flex_template.undo_result(data=undo_users),
    ]
    if replyable:
        return message
    else:
        line_bot_api.push_message(
            to="C39d4dd7d542f3ce98cc69402a3dda664", messages=message
        )
        update_status()


def sort_complete_status(user_status: dict) -> List[Tuple[int, List[str]]]:
    """排序AC資料

    Args:
        user_status (dict): AC資料

    Returns:
        List[Tuple[int, List[str]]]: 排序結果
    """
    count_user_pairs = {}
    for user_id, user_data in user_status.items():
        new_ac_count = len(user_data["result"]["new_ac"])
        if new_ac_count in count_user_pairs:
            count_user_pairs[new_ac_count].append(user_id)
        else:
            count_user_pairs[new_ac_count] = [user_id]
    sorted_status = sorted(count_user_pairs.items(), key=lambda x: -x[0])
    return sorted_status


def update_user_debit(user_id: str, debit: int):
    """更新使用者負債

    Args:
        user_id (str): 使用者 LINE ID
        debit (int): 負債金額
    """
    debit -= check_last_week(user_id=user_id)
    user_data = config.db.user.find_one({"user_id": user_id})
    user_data["debit"] -= debit
    config.db.user.update_one({"_id": user_data["_id"]}, {"$set": user_data})


def check_last_week(user_id: str) -> int:
    """檢查上週補全進度

    Args:
        user_id (str): 使用者 LINE ID

    Returns:
        int: 負債金額
    """
    debit = 0
    question_data = config.db.questions.find_one({})
    last_week = question_data["last_week"]
    last_week_questions = question_data["history"][last_week]["questions"]

    user_data = question_data["history"][last_week]["result"][user_id]["result"]
    if user_data["debit"] > 0:
        work_status = check_work_status(
            user_id=user_id, required_question=last_week_questions, first_week=False
        )
        debit = (user_data["debit"] - work_status["debit"]) / 2
        question_data["history"][last_week]["result"][user_id]["result"] = work_status
        config.db.questions.update_one({}, {"$set": question_data})
    return debit


def update_user_profile():
    """更新使用者名稱"""
    for user_data in config.db.user.find({}):
        user_id = user_data["user_id"]
        profile = line_bot_api.get_profile(user_id)
        display_name = profile.display_name

        user_data["display_name"] = display_name
        config.db.user.update_one({"_id": user_data["_id"]}, {"$set": user_data})


def update_user_leetcode():
    """更新使用者 LeetCode"""
    for user_data in config.db.user.find({}):
        LEETCODE_SESSION = user_data["account"]["LeetCode"]["LEETCODE_SESSION"]
        config.db.user.update_one({"_id": user_data["_id"]}, {"$set": user_data})
