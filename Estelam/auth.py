import logging
import xml.etree.ElementTree as ET
from pydantic import BaseModel
from dbconnection import execute_query
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.security import OAuth2
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from typing import Dict, Optional
from jose import JWTError, jwt
import datetime as dt
from fastapi import Depends,Request,HTTPException,status
from ldap3 import Server, Connection, ALL, SUBTREE







logger = logging.getLogger("Authentication")
try:
    xmltree = ET.parse('./config.xml')
    xmlroot = xmltree.getroot()
    AD = xmlroot.find('AD').text
except:
    logger.error("Cannot read config file ")



class Settings:
    SECRET_KEY: str = xmlroot.find("secrete_key").text
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = (int(xmlroot.find("expire_minutes").text))  # in mins
    COOKIE_NAME = "access_token"

settings = Settings()



class User(BaseModel):
    id: int
    username: str
    password: str
    disabled: bool

def get_user(username: str) -> User:
    query = ("select * from users where username= ?")
    user = execute_query(query, "select",username)
    if user:
        return user
    return None



# --------------------------------------------------------------------------
# Authentication logic
# --------------------------------------------------------------------------
class OAuth2PasswordBearerWithCookie(OAuth2):
    """
    This class is taken directly from FastAPI:
    https://github.com/tiangolo/fastapi/blob/26f725d259c5dbe3654f221e608b14412c6b40da/fastapi/security/oauth2.py#L140-L171

    The only change made is that authentication is taken from a cookie
    instead of from the header!
    """

    def __init__(
            self,
            tokenUrl: str,
            scheme_name: Optional[str] = None,
            scopes: Optional[Dict[str, str]] = None,
            description: Optional[str] = None,
            auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(
            flows=flows,
            scheme_name=scheme_name,
            description=description,
            auto_error=auto_error,
        )

    async def __call__(self, request: Request) -> Optional[str]:
        # IMPORTANT: this is the line that differs from FastAPI. Here we use
        # `request.cookies.get(settings.COOKIE_NAME)` instead of
        # `request.headers.get("Authorization")`
        authorization: str = request.cookies.get(settings.COOKIE_NAME)
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return param


oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="token")


def create_access_token(data: Dict) -> str:
    to_encode = data.copy()
    expire = dt.datetime.utcnow() + dt.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def authenticate_user(username: str, plain_password: str) -> User:
    user = get_user(username)
    if AD =="0":
        if user.disabled:
            return False
        if plain_password != user[2]:
            return False
        return user


#-------------------------------------------------------------------------------------
#           Active Directory logic
    elif AD =="1":
        if user.disabled:
            return False
        else:
            server = Server('s002.site.pgsoc', get_info=ALL)

            # Define the username and password for binding to Active Directory
            activeUser = 'CN=حسین میرزائی زاده سرریگانی,OU=Users,OU=ICT Department,DC=Site,DC=PGSOC'
            activePass = ''

            # User to search for
            user_account_name = username  # Replace this with the account name you want to search for
            user_account_pass = plain_password
            # Bind to the Active Directory
            try:
                with Connection(server, user=activeUser, password=activePass, auto_bind=True) as conn:
                    if conn.bind():

                        # Define the search base and the filter to search for the user account
                        search_base = 'DC=site,DC=pgsoc'  # Define your search base
                        search_filter = f'(&(objectClass=user)(sAMAccountName={user_account_name}))'

                        # Perform the search
                        conn.search(search_base, search_filter, SUBTREE)

                        try:
                            with Connection(server, user=conn.entries[0].entry_dn, password=user_account_pass,
                                            auto_bind=True) as test:
                                if test.bind():
                                    return user

                        except:
                            return False

                    else:
                        return False
            except:
                return False





def decode_token(token: str) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials."
    )
    token = token.removeprefix("Bearer").strip()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("username")
        if username is None:
            raise credentials_exception
    except JWTError as e:
        print(e)
        raise credentials_exception

    user = get_user(username)
    return user


def get_current_user_from_token(token: str = Depends(oauth2_scheme)) -> User:

    user = decode_token(token)
    return user


def get_current_user_from_cookie(request: Request) -> User:

    token = request.cookies.get(settings.COOKIE_NAME)
    user = decode_token(token)
    return user
