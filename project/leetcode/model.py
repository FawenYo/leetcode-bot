from typing import List

from pydantic import BaseModel


class GetLeetCodeStatus(BaseModel):
    user_id: str
    LEETCODE_SESSION: str


class SetQuestion(BaseModel):
    questions: List[str]
    end_date: str
    last_week: str
    token: str
