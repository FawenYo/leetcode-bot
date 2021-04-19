import copy
import sys
from typing import Dict, List, Tuple

import requests

sys.path.append(".")
import config


def login(LEETCODE_SESSION: str = "", csrftoken: str = "", homepage: bool = False) -> Tuple[bool, dict]:
    """Fetch user's LeetCode data

    Args:
        LEETCODE_SESSION (str, optional): LEETCODE_SESSION. Defaults to "".
        csrftoken (str, optional): csrftoken. Defaults to "".

    Returns:
        Tuple[bool, dict]: [description]
    """
    if homepage:
        url = "https://leetcode.com/"
    else:
        url = "https://leetcode.com/api/problems/all/"
    cookies = {"LEETCODE_SESSION": LEETCODE_SESSION, "csrftoken": csrftoken}
    response = requests.get(url=url, cookies=cookies)
    csrftoken = response.cookies.get_dict()["csrftoken"]
    is_login = not not response.json()["user_name"]
    return is_login, response.json(), csrftoken


def find_question(question_name: str) -> Tuple[int, str]:
    """Check if LeetCode question exist.

    Args:
        question_name (str): LeetCode question name.

    Returns:
        Tuple: (question id, question_url)
    """
    is_login, response, csrftoken = login()

    for question in response["stat_status_pairs"]:
        question_title = question["stat"]["question__title"]
        if question_title == question_name:
            return (
                question["stat"]["question_id"],
                question["stat"]["question__title_slug"],
            )
    return (-1, "Null")


def update_leetcode_status(user_data):
    """Update user's LeetCode status"""
    LEETCODE_SESSION = user_data["account"]["LeetCode"]["LEETCODE_SESSION"]
    csrftoken = user_data["account"]["LeetCode"]["csrftoken"]
    latest_status = current_leetcode_status(
        LEETCODE_SESSION=LEETCODE_SESSION, csrftoken=csrftoken
    )
    user_data["LeetCode"] = latest_status
    config.db.user.update_one({"_id": user_data["_id"]}, {"$set": user_data})


def find_question_status(
    LEETCODE_SESSION: str, csrftoken: str, questions: List[str]
) -> List[str]:
    is_login, response, csrftoken = login(LEETCODE_SESSION=LEETCODE_SESSION, csrftoken=csrftoken)
    if not is_login:
        return []
    for question in response["stat_status_pairs"]:
        question_title = question["stat"]["question__title"]
        question__title_slug = question["stat"]["question__title_slug"]
        question_id = question["stat"]["question_id"]
        if f"{question_id}. {question_title}__||__{question__title_slug}" in questions:
            question_index = questions.index(
                f"{question_id}. {question_title}__||__{question__title_slug}"
            )

            # Complete status text
            complete_text = "(未完成)"
            if question["status"] == "ac":
                complete_text = "(已完成)"

            # Use __||__ to split question's info and url
            questions[
                question_index
            ] = f"{question_id}. {question_title} {complete_text}__||__{question__title_slug}"
    return questions


def current_leetcode_status(LEETCODE_SESSION: str, csrftoken: str) -> Dict[str, bool]:
    """Fetch current LeetCode question status

    Args:
        LEETCODE_SESSION (str): User's LeetCode session.
        csrftoken (str): User's LeetCode csrf_token.

    Returns:
        Dict[str, bool]: User's LeetCode question status.
    """
    leetcode_status = {}

    is_login, response, csrftoken = login(LEETCODE_SESSION=LEETCODE_SESSION, csrftoken=csrftoken)

    # LeetCode user name
    leetcode_status["user_name"] = response["user_name"]

    for question in response["stat_status_pairs"]:
        solved = False
        question_title = question["stat"]["question__title"]
        question__title_slug = question["stat"]["question__title_slug"]
        question_id = question["stat"]["question_id"]
        if question["status"] == "ac":
            solved = True
        # Use __||__ to split question's info and url
        leetcode_status[
            f"{question_id}. {question_title}__||__{question__title_slug}"
        ] = solved
    return leetcode_status


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
        LEETCODE_SESSION=user_data["account"]["LeetCode"]["LEETCODE_SESSION"],
        csrftoken=user_data["account"]["LeetCode"]["csrftoken"],
    )
    user_name = latest_status["user_name"]
    # shallow copy to prevent affect others
    copy_required = copy.copy(required_questions)
    for key, value in latest_status.items():
        if value == True:
            # Required questions
            if key in copy_required:
                del copy_required[copy_required.index(key)]
                new_ac.append(key)
            # Optional questions
            elif key in optional_questions:
                new_ac.append(key)
            # Other questions
            else:
                try:
                    before_status = old_status[key]
                    if before_status ^ value:
                        new_ac.append(key)
                except KeyError:
                    pass
    # Complete all required questions
    if len(copy_required) == 0:
        return {
            "user_name": user_name,
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
            "user_name": user_name,
            "undo": copy_required,
            "new_ac": new_ac,
            "debit": debit,
        }
