from threading import current_thread

import requests

QUESTION_1 = ""  # LeetCode 第一題
QUESTION_2 = ""  # LeetCode 第二題
END_DATE = "2021/03/18"  # 截止日期
LAST_WEEK = "2021/03/17"  # 上次截止日期
TOKEN = ""


def set_new_question():
    data = {
        "questions": [QUESTION_1, QUESTION_2],
        "end_date": END_DATE,
        "last_week": LAST_WEEK,
        "token": TOKEN,
    }
    response = requests.post("https://leetcode-bot.ml/api/question/set", data=data)
    print(response)


if __name__ == "__main__":
    set_new_question()
