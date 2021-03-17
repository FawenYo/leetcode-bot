from typing import Dict, List

from pydantic import BaseModel


class GetLeetCodeStatus(BaseModel):
    user_id: str
    LEETCODE_SESSION: str
