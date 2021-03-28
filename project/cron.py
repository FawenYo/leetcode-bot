import threading
from datetime import datetime
from typing import List, Tuple

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from linebot import LineBotApi

import config
import leetcode.info
from line import actions, flex_template

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
        week_check,
        "cron",
        day_of_week="sun",
        hour=18,
        minute=00,
        second=00,
        timezone=pytz.timezone("Asia/Taipei"),
    )
    message = {"stauts": "success", "message": "已開始定時任務！"}
    return JSONResponse(content=message)


@cron.get("/start", response_class=JSONResponse)
async def quick_start() -> JSONResponse:
    """Start cron jobs

    Returns:
        JSONResponse: Start status
    """
    week_check()
    message = {"stauts": "success", "message": "已完成任務！"}
    return JSONResponse(content=message)


def week_check(
    replyable: bool = False,
) -> None:
    """Week check LeetCode status

    Args:
        replyable (bool, optional): If the message can use reply. Defaults to False.
    """
    actions.update_user_profile()
    user_status, undo_users = fetch_all_leetcode(replyable=replyable)
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
        for user_data in config.db.user.find({}):
            leetcode.info.update_status(user_data=user_data)


def fetch_all_leetcode(
    replyable: bool = False,
    current_date: str = datetime.strftime(datetime.now(), "%Y/%m/%d"),
) -> Tuple[dict, list]:
    """Fetch All Users' LeetCode status

    Args:
        replyable (bool, optional): If the message can use reply. Defaults to False.
        current_date (str, optional): Check date. Defaults to today.

    Returns:
        Tuple[dict, list]: (user_status, undo_users)
    """
    user_status = {}
    undo_users = []
    threads: List[threading.Thread] = []

    question_data = config.db.questions.find_one({})
    check_date = question_data["latest"]["check_date"]
    required_questions = question_data["history"][check_date]["questions"]["required"]
    optional_questions = question_data["history"][check_date]["questions"]["optional"]

    # Remove question ID
    for index, value in enumerate(required_questions):
        required_questions[index] = value.split(". ")[1]
    for index, value in enumerate(optional_questions):
        optional_questions[index] = value.split(". ")[1]

    def fetch_user_result(user_data: dict):
        user_id = user_data["user_id"]
        display_name = user_data["display_name"]
        work_status = leetcode.info.check_work_status(
            user_id=user_id,
            required_questions=required_questions,
            optional_questions=optional_questions,
        )
        user_status[user_id] = {
            "display_name": display_name,
            "result": work_status,
        }

        if not work_status["complete"]:
            undo_users.append(
                {
                    "user_id": user_id,
                    "user": display_name,
                    "debit": work_status["debit"],
                }
            )
            if not replyable:
                update_user_debit(
                    user_id=user_data["user_id"], debit=work_status["debit"]
                )

    # Multi-threading
    for user_data in config.db.user.find():
        threads.append(threading.Thread(target=fetch_user_result, args=(user_data,)))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    if not replyable:
        # Update question history result
        question_data["history"][current_date]["result"] = user_status
        # Update check date
        question_data["latest"]["history"][check_date]["questions"][
            "check_date"
        ] = question_data["latest"]["history"][check_date]["questions"]["end_date"]
        config.db.questions.update_one({}, {"$set": question_data})
    return (user_status, undo_users)


def sort_complete_status(user_status: dict) -> List[Tuple[int, List[str]]]:
    """Sort Accepted data.

    Args:
        user_status (dict): Accepted data.

    Returns:
        List[Tuple[int, List[str]]]: sorted result
    """
    count_user_pairs = {}
    for user_id, user_data in user_status.items():
        new_ac_count = len(user_data["result"]["new_ac"])
        if new_ac_count in count_user_pairs:
            count_user_pairs[new_ac_count].append(user_data["display_name"])
        else:
            count_user_pairs[new_ac_count] = [user_data["display_name"]]
    sorted_status = sorted(count_user_pairs.items(), key=lambda x: -x[0])
    return sorted_status


def update_user_debit(user_id: str, debit: int) -> None:
    """更新使用者負債

    Args:
        user_id (str): 使用者 LINE ID
        debit (int): 負債金額
    """
    current_date = datetime.strftime(datetime.now(), "%Y/%m/%d")
    debit -= check_last_week(user_id=user_id, current_date=current_date)
    user_data = config.db.user.find_one({"user_id": user_id})
    user_data["debit"] -= debit
    config.db.user.update_one({"_id": user_data["_id"]}, {"$set": user_data})


def check_last_week(user_id: str, current_date: str) -> int:
    """檢查上週補全進度

    Args:
        user_id (str): 使用者 LINE ID

    Returns:
        int: 負債金額
    """
    debit = 0
    question_data = config.db.questions.find_one({})
    last_week = question_data["last_week"]
    if current_date == last_week:
        return debit
    last_week_required_questions = question_data["history"][last_week]["questions"][
        "required"
    ]
    last_week_optional_questions = question_data["history"][last_week]["questions"][
        "optional"
    ]

    user_data = question_data["history"][last_week]["result"][user_id]["result"]
    if user_data["debit"] > 0:
        work_status = leetcode.info.check_work_status(
            user_id=user_id,
            required_questions=last_week_required_questions,
            optinoal_questions=last_week_optional_questions,
            first_week=False,
        )
        debit = (user_data["debit"] - work_status["debit"]) / 2
        question_data["history"][last_week]["result"][user_id]["result"] = work_status
        config.db.questions.update_one({}, {"$set": question_data})
    return debit
