from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

view = APIRouter()
templates = Jinja2Templates(directory="templates")

# Home Page
@view.get("/", response_class=JSONResponse)
async def index():
    message = {"stauts": "Success"}
    return JSONResponse(content=message)


# Login Page
@view.get("/login/leetcode", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", context={"request": request})
