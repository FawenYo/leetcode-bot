import sys
import asyncio

import requests
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from .model import *
from . import info

sys.path.append(".")
import config

leetcode = APIRouter()


@leetcode.post("/api/leetcode/login", response_class=JSONResponse)
async def get_leetcode_status(param: GetLeetCodeStatus) -> JSONResponse:
    message = {"status": "failed"}

    cookies = {"LEETCODE_SESSION": param.LEETCODE_SESSION}
    response = requests.get(
        "https://leetcode.com/api/problems/all/", cookies=cookies
    ).json()
    if response["user_name"] != "":
        user_data = config.db.user.find({"user_id": param.user_id})
        if user_data:
            user_data["account"]["LeetCode"][
                "LEETCODE_SESSION"
            ] = param.LEETCODE_SESSION

            asyncio.run(
                info.update_status(
                    user_id=param.user_id, LEETCODE_SESSION=param.LEETCODE_SESSION
                )
            )

            config.db.user.update_one({"user_id": param.user_id}, {"$set": user_data})
            message = {"status": "success"}

    return JSONResponse(content=message)
