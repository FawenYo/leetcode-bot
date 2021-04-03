from typing import List

from pydantic import BaseModel


class GetLeetCodeStatus(BaseModel):
    user_id: str
    cstftoken: str
    LEETCODE_SESSION: str


class SetQuestion(BaseModel):
    required_questions: List[str]
    optional_questions: List[str]
    end_date: str
    last_week: str
    token: str
