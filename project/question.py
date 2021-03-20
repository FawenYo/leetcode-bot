import requests

REQUIRED_QUESTION_1: str = ""  # LeetCode 必寫題 - 第一題
REQUIRED_QUESTION_2: str = ""  # LeetCode 必寫題 - 第二題
OPTIONAL_QUESTION_3: str = ""  # LeetCode 選寫題 - 第三題
OPTIONAL_QUESTION_4: str = ""  # LeetCode 選寫題 - 第四題
OPTIONAL_QUESTION_5: str = ""  # LeetCode 選寫題 - 第五題
END_DATE: str = "2021/03/18"  # 截止日期
LAST_WEEK: str = "2021/03/17"  # 上次截止日期
TOKEN: str = ""


def set_new_question():
    data = {
        "required_questions": [REQUIRED_QUESTION_1, REQUIRED_QUESTION_2],
        "optional_questions": [
            OPTIONAL_QUESTION_3,
            OPTIONAL_QUESTION_4,
            OPTIONAL_QUESTION_5,
        ],
        "end_date": END_DATE,
        "last_week": LAST_WEEK,
        "token": TOKEN,
    }
    response = requests.post("https://leetcode-bot.ml/api/question/set", json=data).text
    print(response)


if __name__ == "__main__":
    set_new_question()
