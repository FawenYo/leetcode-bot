import sys
import threading

import requests
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from linebot.api import LineBotApi

from . import info
from .model import *

sys.path.append(".")
import config
from line import flex_template

leetcode = APIRouter()
line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)


@leetcode.post("/api/leetcode/login", response_class=JSONResponse)
async def get_leetcode_status(param: GetLeetCodeStatus) -> JSONResponse:
    """LeetCode Login API

    Args:
        param (GetLeetCodeStatus): Post data.

    Returns:
        JSONResponse: LeetCode login result.
    """
    cookies = {"LEETCODE_SESSION": param.LEETCODE_SESSION}
    response = requests.get(
        "https://leetcode.com/api/problems/all/", cookies=cookies
    ).json()
    if response["user_name"] != "":
        user_data = config.db.user.find_one({"user_id": param.user_id})
        if user_data:
            user_data["account"]["LeetCode"][
                "LEETCODE_SESSION"
            ] = param.LEETCODE_SESSION
            config.db.user.update_one({"_id": user_data["_id"]}, {"$set": user_data})
            message = {"status": "success", "message": "已成功登入帳號！"}

            # 更新 LeetCode 狀況
            thread = threading.Thread(target=info.update_status, args=(param.user_id,))
            thread.start()
        else:
            message = {"status": "failed", "message": "請先加入 LINE Bot 好友！"}
    else:
        message = {"status": "failed", "message": "查無 LeetCode 帳號！"}

    return JSONResponse(content=message)


@leetcode.get("/api/leetcode/getdata", response_class=JSONResponse)
async def get_leetcode_status(user_id: str) -> JSONResponse:
    """Check if user already login to LeetCode.

    Args:
        user_id (str): User's LINE ID.

    Returns:
        JSONResponse: Login history data.
    """
    user_data = config.db.user.find_one({"user_id": user_id})
    if user_data:
        if user_data["account"]["LeetCode"]["LEETCODE_SESSION"] == "":
            message = {"status": "success", "message": "尚未紀錄 LeetCode 帳號"}
        else:
            message = {"status": "failed", "message": "已經登入過 LeetCode 帳號！"}
    else:
        message = {"status": "failed", "message": "請先加入 LINE Bot 好友！"}

    return JSONResponse(content=message)


@leetcode.post("/api/question/set", response_class=JSONResponse)
async def set_week_question(param: SetQuestion) -> JSONResponse:
    """Week set new question

    Args:
        param (SetQuestion): Post data.

    Returns:
        JSONResponse: Set question result.
    """
    try:
        if param.token == config.TOKEN:
            no_questions = []
            question_exist = True
            required_questions = param.required_questions
            optional_questions = param.optional_questions

            for each in required_questions:
                if not info.find_question(question_name=each):
                    question_exist = False
                    no_questions.append(each)

            for each in optional_questions:
                if not info.find_question(question_name=each):
                    question_exist = False
                    no_questions.append(each)

            if question_exist:
                question_data = config.db.questions.find_one({})

                question_data["latest"] = {
                    "required": required_questions,
                    "optional": optional_questions,
                }
                question_data["history"][param.end_date] = {
                    "questions": {
                        "required": required_questions,
                        "optional": optional_questions,
                    },
                    "result": {},
                }
                question_data["last_week"] = param.last_week
                message = flex_template.set_question(
                    required_questions=required_questions,
                    optional_questions=optional_questions,
                )
                line_bot_api.push_message(
                    to="C39d4dd7d542f3ce98cc69402a3dda664", messages=message
                )
                config.db.questions.update_one({}, {"$set": question_data})
                message = {"status": "success", "message": "已成功設置！"}
            else:
                message = {
                    "status": "failed",
                    "message": f"查無題目：{','.join(no_questions)}",
                }
        else:
            message = {"status": "failed", "message": "Token錯誤！"}
    except:
        config.console.print_exception()
        message = {"status": "failed", "message": "發生未知錯誤！"}
    return JSONResponse(content=message)
