import requests

QUESTION_1: str = ""  # LeetCode 第一題
QUESTION_2: str = ""  # LeetCode 第二題
END_DATE: str = "2021/03/18"  # 截止日期
LAST_WEEK: str = "2021/03/17"  # 上次截止日期
TOKEN: str = ""


def set_new_question():
    data = {
        "questions": [QUESTION_1, QUESTION_2],
        "end_date": END_DATE,
        "last_week": LAST_WEEK,
        "token": TOKEN,
    }
    response = requests.post("http://leetcode-bot.ml/api/question/set", json=data).text
    print(response)


if __name__ == "__main__":
    set_new_question()
