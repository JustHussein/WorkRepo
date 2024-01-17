import logging
import datetime
from typing import Dict, List, Optional
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status,Form
from fastapi.responses import HTMLResponse, RedirectResponse,FileResponse
from fastapi.security import  OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from rich.console import Console
from estelam import getestelam
import xml.etree.ElementTree as ET
import re
from auth import authenticate_user,create_access_token,get_current_user_from_token,User,get_current_user_from_cookie


current_date = datetime.date.today().strftime("%Y%m%d")
log_filename = f".\\Logging\\Log_{current_date}.log"
logging.basicConfig(filename=log_filename,
                    encoding='utf-8',
                    level=logging.DEBUG,
                    format='%(levelname)s:%(asctime)s:%(message)s')

logger = logging.getLogger("main")

console = Console()
try:
    xmltree = ET.parse('./config.xml')
    xmlroot = xmltree.getroot()

except:
    logger.error("Cannot read config file ")

# --------------------------------------------------------------------------
# Models and Data
# --------------------------------------------------------------------------

favicon_path = 'statics/images/favicon.ico'
# Create a "database" to hold your data. This is just for example purposes. In
# a real world scenario you would likely connect to a SQL or NoSQL database.




# --------------------------------------------------------------------------
# Setup FastAPI
# --------------------------------------------------------------------------
class Settings:
    SECRET_KEY: str = xmlroot.find("secrete_key").text
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = (int(xmlroot.find("expire_minutes").text))  # in mins
    COOKIE_NAME = "access_token"


app = FastAPI(docs_url=None, redoc_url=None)
templates = Jinja2Templates(directory="templates")
app.mount("/statics", StaticFiles(directory="statics"), name="statics")

settings = Settings()


def is_valid_iran_code(input: str) -> bool:
    if not re.search(r'^\d{10}$', input): return False
    check = int(input[9])
    s = sum(int(input[x]) * (10 - x) for x in range(9)) % 11
    return check == s if s < 2 else check + s == 11

@app.post("token")
def login_for_access_token(
        response: Response,
        form_data: OAuth2PasswordRequestForm = Depends()
) -> Dict[str, str]:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    access_token = create_access_token(data={"username": user.username})
    # Set an HttpOnly cookie in the response. `httponly=True` prevents
    # JavaScript from reading the cookie.
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=f"Bearer {access_token}",
        httponly=True
    )
    logger.info(f"login successfully: {user.username}")
    return {settings.COOKIE_NAME: access_token, "token_type": "bearer"}


# --------------------------------------------------------------------------
# Home Page
# --------------------------------------------------------------------------
"""@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    try:
        user = get_current_user_from_cookie(request)
    except:
        user = None
    context = {
        "user": user,
        "request": request,
    }
    return templates.TemplateResponse("index.html", context)

"""

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)
# --------------------------------------------------------------------------
# Private Page
# --------------------------------------------------------------------------
# A private page that only logged in users can access.
@app.get("/private", response_class=HTMLResponse)
def private(request: Request, user: User = Depends(get_current_user_from_token)):
    context = {
        "user": user,
        "request": request,
        "request":request
    }
    return templates.TemplateResponse("private.html", {"user": user,"request": request,"request": request})


# --------------------------------------------------------------------------
# Login - GET
# --------------------------------------------------------------------------
@app.get("/", response_class=(HTMLResponse,RedirectResponse))
def login_get(request: Request ):
    try:
        user = get_current_user_from_cookie(request)
        context = {
            "user": user,
            "request": request
        }
        return RedirectResponse("private",status_code=status.HTTP_303_SEE_OTHER)
    except:
        context = {
            "request": request,
        }
        return templates.TemplateResponse("login.html", context)

@app.post("/estelam")
async def estelam(request: Request,nationalID: str=Form(...) ,user: User = Depends(get_current_user_from_token)):
    if is_valid_iran_code(nationalID):
        try:
            result = getestelam(nationalID)
            if result[0] == 200:
                result1= result[1]
                result2= zip(result[2],result[3])
                return templates.TemplateResponse("private.html",{"request":request,"result":result,"result2":result2})
            else:
                return templates.TemplateResponse("private.html",{"request":request,"detail_error":result[1]})
        except:
            return templates.TemplateResponse("private.html",
                                              {"request": request, "detail_error": "خطا در ارتباط با مرکز"})

    else:
        return templates.TemplateResponse("private.html", {"request": request, "detail_error": "کد ملی صحیح نمیباشد."})


# --------------------------------------------------------------------------
# Login - POST
# --------------------------------------------------------------------------
class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.errors: List = []
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def load_data(self):
        form = await self.request.form()
        self.username = form.get("username")
        self.password = form.get("password")

    async def is_valid(self):
        if not self.username:
            self.errors.append("نام کاربری یا کلمه عبور اشتباه است.")
        if not self.password or not len(self.password) >= 4:
            self.errors.append("نام کاربری یا کلمه عبور اشتباه است.")
        if not self.errors:
            return True
        return False


@app.post("/", response_class=HTMLResponse)
async def login_post(request: Request):
    form = LoginForm(request)
    await form.load_data()
    if await form.is_valid():
        try:
            response = RedirectResponse("/", status.HTTP_302_FOUND)
            login_for_access_token(response=response, form_data=form)
            form.__dict__.update(msg=f"Login Successful! {request.client}")
            console.log(f"[green]Login Successful! {request.client}")
            logger.info(request.client)
            return response
        except HTTPException:
            form.__dict__.update(msg="")
            form.__dict__.get("errors").append("نام کاربری یا کلمه عبور اشتباه است.")
            return templates.TemplateResponse("login.html", form.__dict__)
    return templates.TemplateResponse("login.html", form.__dict__)


# --------------------------------------------------------------------------
# Logout
# --------------------------------------------------------------------------
@app.get("/auth/logout", response_class=HTMLResponse)
def login_get():
    response = RedirectResponse(url="/")
    response.delete_cookie(settings.COOKIE_NAME)
    return response