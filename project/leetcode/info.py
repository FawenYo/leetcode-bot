import requests
import sys

sys.path.append(".")
import config


async def status_crawler(LEETCODE_SESSION: str, question_name: str):
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


async def update_status(user_id: str, LEETCODE_SESSION: str):
    user_data = config.db.user.find({"user_id": user_id})
    latest_status = current_leetcode_status(LEETCODE_SESSION=LEETCODE_SESSION)
    user_data["LeetCode"] = latest_status
    config.db.user.update_one({"user_id": user_id}, {"$set": user_data})


def current_leetcode_status(LEETCODE_SESSION: str):
    cookies = {"LEETCODE_SESSION": LEETCODE_SESSION}
    response = requests.get(
        "https://leetcode.com/api/problems/all/", cookies=cookies
    ).json()
    user_stauts = {}
    for question in response["stat_status_pairs"]:
        solved = False
        question_title = question["stat"]["question__title"]
        if question["status"] == "ac":
            solved = True
        user_stauts[question_title] = solved
    return user_stauts


def check_user_progress(user_id: str):
    user_data = config.db.user.find({"user_id": user_id})
    old_status = user_data["LeetCode"]
    latest_status = current_leetcode_status(
        LEETCODE_SESSION=user_data["account"]["LeetCode"]["LEETCODE_SESSION"]
    )
    # TODO: Comparer two dict