import sys
from typing import List

import requests

sys.path.append(".")
import config


def status_crawler(LEETCODE_SESSION: str, question_name: str):
    solved = False
    cookies = {"LEETCODE_SESSION": LEETCODE_SESSION}
    response = requests.get(
        "https://leetcode.com/api/problems/all/", cookies=cookies
    ).json()
    for question in response["stat_status_pairs"]:
        question_title = question["stat"]["question__title"]
        if question_title == question_name:
            if question["status"] == "ac":
                solved = True
    return solved


def update_status(user_id: str, LEETCODE_SESSION: str):
    user_data = config.db.user.find_one({"user_id": user_id})
    latest_status = current_leetcode_status(LEETCODE_SESSION=LEETCODE_SESSION)
    user_data["LeetCode"] = latest_status
    config.db.user.update_one({"user_id": user_id}, {"$set": user_data})


def current_leetcode_status(LEETCODE_SESSION: str) -> dict:
    user_stauts = {}

    cookies = {"LEETCODE_SESSION": LEETCODE_SESSION}
    response = requests.get(
        "https://leetcode.com/api/problems/all/", cookies=cookies
    ).json()

    for question in response["stat_status_pairs"]:
        solved = False
        question_title = question["stat"]["question__title"]
        if question["status"] == "ac":
            solved = True
        user_stauts[question_title] = solved
    return user_stauts


def check_work_status(user_id: str, required_question: List[str]) -> dict:
    new_ac = []
    user_data = config.db.user.find_one({"user_id": user_id})
    old_status = user_data["LeetCode"]
    latest_status = current_leetcode_status(
        LEETCODE_SESSION=user_data["account"]["LeetCode"]["LEETCODE_SESSION"]
    )
    for key, value in latest_status.items():
        # 必選
        if key in required_question and value == True:
            del required_question[required_question.index(key)]
        else:
            # 新作答題目
            try:
                before_status = old_status[key]
                if before_status ^ value:
                    new_ac.append(key)
            except KeyError:
                pass

    if len(required_question) == 0:
        return {
            "complete": True,
            "undo": required_question,
            "new_ac": new_ac,
            "debit": 0,
        }
    else:
        debit = 50 * len(required_question)
        return {
            "complete": False,
            "undo": required_question,
            "new_ac": new_ac,
            "debit": debit,
        }
