import threading
from datetime import datetime
from typing import List, Tuple

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from linebot import LineBotApi

import config
import leetcode.info
from line import actions, flex_template

cron = APIRouter()
line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)


@cron.get("/update", response_class=JSONResponse)
async def cron_update(token: str) -> JSONResponse:
    """Start cron jobs - update

    Args:
        token (str): API token

    Returns:
        JSONResponse: Job status
    """
    # Check API token
    if token == config.TOKEN:
        daily_update()
        message = {"stauts": "success", "message": "已完成任務！"}
    else:
        message = {"status": "error", "message": "Token錯誤！"}
    return JSONResponse(content=message)


@cron.get("/check", response_class=JSONResponse)
async def cron_check(token: str) -> JSONResponse:
    """Start cron jobs - check

    Args:
        token (str): API token

    Returns:
        JSONResponse: Job status
    """
    # Check API token
    if token == config.TOKEN:
        week_check()
        message = {"stauts": "success", "message": "已完成任務！"}
    else:
        message = {"status": "error", "message": "Token錯誤！"}
    return JSONResponse(content=message)


def daily_update() -> None:
    """Update user's LEETCODE_SESSION"""
    threads = []

    def update_leetcode_session(user_data: dict):
        LEETCODE_SESSION = user_data["account"]["LeetCode"]["LEETCODE_SESSION"]
        is_login, response, new_leetcode_session = leetcode.info.login(
            LEETCODE_SESSION=LEETCODE_SESSION
        )
        if is_login:
            if new_leetcode_session:
                user_data["account"]["LeetCode"][
                    "LEETCODE_SESSION"
                ] = new_leetcode_session
                config.db.user.update_one(
                    {"_id": user_data["_id"]}, {"$set": user_data}
                )

    # Using multi-threading for better response time
    for user_data in config.db.user.find():
        threads.append(
            threading.Thread(target=update_leetcode_session, args=(user_data,))
        )
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


def week_check(
    replyable: bool = False,
) -> None:
    """Week check LeetCode status

    Args:
        replyable (bool, optional): If the message can use reply. Defaults to False.
    """
    user_status, undo_users, unbound_users = fetch_all_leetcode(replyable=replyable)
    sorted_status = sort_complete_status(user_status=user_status)

    message = [
        flex_template.complete_result(data=sorted_status),
        flex_template.undo_result(data=undo_users),
        flex_template.unbound_users(data=unbound_users),
    ]
    if replyable:
        return message
    else:
        # Push week result to LINE group
        line_bot_api.push_message(
            to="C39d4dd7d542f3ce98cc69402a3dda664", messages=message
        )
        # Update user's LINE display_name
        actions.update_user_profile()
        # Update user's LeetCode status
        for user_data in config.db.user.find({}):
            leetcode.info.update_leetcode_status(user_data=user_data)


def fetch_all_leetcode(
    replyable: bool = False,
) -> Tuple[dict, list]:
    """Fetch All Users' LeetCode status

    Args:
        replyable (bool, optional): If the message can use reply. Defaults to False.

    Returns:
        Tuple[dict, list]: (user_status, undo_users)
    """

    current_date: str = datetime.strftime(datetime.now(), "%Y/%m/%d")
    user_status = {}
    undo_users = []
    unbound_users = []
    threads: List[threading.Thread] = []

    question_data = config.db.questions.find_one({})
    check_date = question_data["latest"]["check_date"]
    required_questions = question_data["history"][check_date]["questions"]["required"]
    optional_questions = question_data["history"][check_date]["questions"]["optional"]

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

        # Unbound LeetCode account
        if not work_status["user_name"]:
            unbound_users.append(
                {
                    "user_id": user_id,
                    "user": display_name,
                }
            )

        # Undo users
        if work_status["undo"]:
            undo_users.append(
                {
                    "user_id": user_id,
                    "user": display_name,
                    "debit": work_status["debit"],
                }
            )
        if not replyable:
            update_user_debit(user_id=user_id, debit=work_status["debit"])

    # Using multi-threading for better response time
    for user_data in config.db.user.find({"check": True}):
        threads.append(threading.Thread(target=fetch_user_result, args=(user_data,)))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    if not replyable:
        # Update question history result
        question_data["history"][current_date]["result"] = user_status
        # Update check date
        question_data["latest"]["check_date"] = question_data["latest"]["end_date"]
        config.db.questions.update_one({}, {"$set": question_data})
    return (user_status, undo_users, unbound_users)


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
    """Update user's debit

    Args:
        user_id (str): User's LINE ID
        debit (int): Debit amount
    """
    debit += check_last_week(user_id=user_id)
    user_data = config.db.user.find_one({"user_id": user_id})
    user_data["debit"] -= debit
    config.db.user.update_one({"_id": user_data["_id"]}, {"$set": user_data})


def check_last_week(user_id: str) -> int:
    """Check last week's status

    Args:
        user_id (str): User's LINE ID

    Returns:
        int: Debit amount
    """
    debit = 0
    question_data = config.db.questions.find_one({})
    last_week = question_data["latest"]["last_week"]

    user_data = question_data["history"][last_week]["result"][user_id]["result"]
    # He/She has not complete last week's work
    if user_data["debit"] > 0:
        # Last week's questions
        last_week_required_questions = question_data["history"][last_week]["questions"][
            "required"
        ]
        last_week_optional_questions = question_data["history"][last_week]["questions"][
            "optional"
        ]
        work_status = leetcode.info.check_work_status(
            user_id=user_id,
            required_questions=last_week_required_questions,
            optional_questions=last_week_optional_questions,
            first_week=False,
        )
        debit = work_status["debit"]
        question_data["history"][last_week]["result"][user_id]["result"] = work_status
        config.db.questions.update_one({}, {"$set": question_data})
    return debit
