from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

view = APIRouter()
templates = Jinja2Templates(directory="templates")


@view.get("/", response_class=JSONResponse)
async def index() -> JSONResponse:
    """Home Page

    Returns:
        JSONResponse: System status
    """
    message = {"stauts": "success", "message": "System working"}
    return JSONResponse(content=message)


@view.get("/login/leetcode", response_class=HTMLResponse)
async def login(request: Request) -> HTMLResponse:
    """LeetCode Login Page

    Args:
        request (Request): Request Object.

    Returns:
        HTMLResponse: LeetCode Login Page
    """
    return templates.TemplateResponse("login.html", context={"request": request})
