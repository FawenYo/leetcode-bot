import copy
import sys
from typing import Dict, List

import requests

sys.path.append(".")
import config


def find_question(question_name: str) -> int:
    """Check if LeetCode question exist.

    Args:
        question_name (str): LeetCode question name.

    Returns:
        int: question id. -1 for not exist
    """
    response = requests.get("https://leetcode.com/api/problems/all/").json()
    for question in response["stat_status_pairs"]:
        question_title = question["stat"]["question__title"]
        if question_title == question_name:
            return question["stat"]["question_id"]
    return -1


def status_crawler(LEETCODE_SESSION: str, question_name: str) -> bool:
    """Check if question solved

    Args:
        LEETCODE_SESSION (str): User's LeetCode session.
        question_name (str): LeetCode question name.

    Returns:
        bool: Solved or not.
    """
    cookies = {"LEETCODE_SESSION": LEETCODE_SESSION}
    response = requests.get(
        "https://leetcode.com/api/problems/all/", cookies=cookies
    ).json()
    for question in response["stat_status_pairs"]:
        question_title = question["stat"]["question__title"]
        if question_title == question_name:
            if question["status"] == "ac":
                return True
    return False


def update_status(user_data):
    """Update user's LeetCode status"""
    LEETCODE_SESSION = user_data["account"]["LeetCode"]["LEETCODE_SESSION"]
    latest_status = current_leetcode_status(LEETCODE_SESSION=LEETCODE_SESSION)
    user_data["LeetCode"] = latest_status
    config.db.user.update_one({"_id": user_data["_id"]}, {"$set": user_data})


def find_question_status(LEETCODE_SESSION: str, questions: List[str]) -> List[str]:
    cookies = {"LEETCODE_SESSION": LEETCODE_SESSION}
    response = requests.get(
        "https://leetcode.com/api/problems/all/", cookies=cookies
    ).json()
    for question in response["stat_status_pairs"]:
        question_title = question["stat"]["question__title"]
        question_id = question["stat"]["question_id"]
        if f"{question_id}. {question_title}" in questions:
            question_index = questions.index(f"{question_id}. {question_title}")
            if question["status"] == "ac":
                questions[question_index] = f"{question_id}. {question_title} (已完成)"
            else:
                questions[question_index] = f"{question_id}. {question_title} (未完成)"
    return questions


def current_leetcode_status(LEETCODE_SESSION: str) -> Dict[str, bool]:
    """Fetch current LeetCode question status

    Args:
        LEETCODE_SESSION (str): User's LeetCode session.

    Returns:
        Dict[str, bool]: User's LeetCode question status.
    """
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


def check_work_status(
    user_id: str,
    required_questions: List[str],
    optional_questions: List[str],
    first_week=True,
) -> dict:
    """Check user's work status

    Args:
        user_id (str): User's LINE ID.
        required_questions (List[str]): Week required questions.
        optional_questions (List[str]): Week optional questions.
        first_week (bool, optional): If this is first week. Defaults to True.

    Returns:
        dict: User's work status
    """
    new_ac = []
    user_data = config.db.user.find_one({"user_id": user_id})
    old_status = user_data["LeetCode"]
    latest_status = current_leetcode_status(
        LEETCODE_SESSION=user_data["account"]["LeetCode"]["LEETCODE_SESSION"]
    )
    # shallow copy to prevent affect others
    copy_required = copy.copy(required_questions)
    for key, value in latest_status.items():
        if value == True:
            # 必選
            if key in copy_required:
                del copy_required[copy_required.index(key)]
                new_ac.append(key)
            # 選寫
            elif key in optional_questions:
                new_ac.append(key)
            # 其他題目
            else:
                try:
                    before_status = old_status[key]
                    if before_status ^ value:
                        new_ac.append(key)
                except KeyError:
                    pass
    if len(copy_required) == 0:
        return {
            "complete": True,
            "undo": copy_required,
            "new_ac": new_ac,
            "debit": 0,
        }
    else:
        if first_week:
            debit = 10 * len(copy_required)
        else:
            debit = 40 * len(copy_required)
        return {
            "complete": False,
            "undo": copy_required,
            "new_ac": new_ac,
            "debit": debit,
        }
