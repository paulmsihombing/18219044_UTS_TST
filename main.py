# UTS II3160 Teknologi Sistem Terintegrasi
# Paul Marturia Sihombing - 18219044

import json

from os import write

from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Command : openssl rand -hex 32
SECRET_KEY = "25fb1e99e80a5fb93c53d8ee9c5892eedcd68ee9ade401789edc6a51c9ba293f"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

with open("menu.json", "r") as read_file:
    data = json.load(read_file)

# Title
TitleDescription = '''
FASTAPI Sederhana\n
Restoran Makanan\n
'''

# Header
HeaderDescription = '''
Nama    : Paul Marturia Sihombing\n
NIM     : 18219044\n
Prodi   : Sistem dan Teknologi Informasi\n
\n
Ujian Tengah Semester 2021/2022 - II3160 Teknologi Sistem Terintegrasi\n 
\n
'''

# Aplikasi FASTAPI
app = FastAPI(
    title=TitleDescription,
    description=HeaderDescription
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

# Data Pengguna, ASDF
db_users = {
    "asdf": {
        "username": "asdf",
        "full_name": "A. S. D. F. S.T., M.T",
        "email": "asdf@mahasiswa.com",
        "hashed_password": "$2b$12$naWFMV71ifNuPCNXUhknxuIEwKCPSZ7YfeG0ZelrQpfM9uZa6qLpe",
        "disabled": False,
    }
}

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
	username: str
	email: Optional[str] = None
	full_name: Optional[str] = None
	disabled: Optional[str] = None

class UserInDB(User):
    hashed_password: str

pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")

def verify_password(plain_password, hashed_password):
	return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
	pwd_context.hash(password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(user_db, username: str, password: str):
    user = get_user(user_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db_users, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user

# Token untuk keperluan Authentication

@app.post("/token", response_model=Token, tags=["Token"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(db_users, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=User, tags=["My Data"])
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# API Menu  

@app.get('/', tags=["Root"])
def root():
    return {'Menu':'Price'}

@app.get('/menu', tags=["Root"])   # Display All Item in Menu
async def display_all_menu(token: str = Depends(oauth2_scheme)):
    return data

@app.get('/menu/{item_id}', tags=["API Menu"])         # Display Spesific Menu with GET
async def read_menu(item_id: int, token: str = Depends(oauth2_scheme)):
    for menu_item in data['menu']:
        if menu_item['id'] == item_id:
            return menu_item
    raise HTTPException (
        status_code = 404, detail = f'Item not found'
    )

@app.put('/menu/{item_id},{name}', tags=["API Menu"])  # Update Menu with PUT
async def update_menu(item_id: int, name:str, token: str = Depends(oauth2_scheme)):
    for menu_item in data['menu']:
        if menu_item['id'] == item_id:
            menu_item['name'] = name
            read_file.close()
            with open("menu.json", "w") as write_file:
                json.dump(data, write_file, indent=4)
            write_file.close()
            return{"Your data has been updated! Please check in menu."}

    raise HTTPException (
        status_code = 404, detail = f'Error 404. Item not found'
    )

@app.delete('/menu/{item_id}', tags=["API Menu"])  # Delete Menu with DELETE
async def delete_menu(item_id: int, token: str = Depends(oauth2_scheme)):
    for menu_item in data['menu']:
        if menu_item['id'] == item_id:
            data['menu'].remove(menu_item)
            read_file.close()
            with open("menu.json", "w") as write_file:
                json.dump(data, write_file, indent=4)
            write_file.close()
            return{"Your data has been deleted! Please check in menu."}

    raise HTTPException (
        status_code = 404, detail = f'Error 404. Item not found'
    )

@app.post('/menu/{name}', tags=["API Menu"])   # Add Menu with POST    
async def add_menu(name:str, token: str = Depends(oauth2_scheme)):
    menu_id = 1
    if(len(data["menu"])>0):
        menu_id = data["menu"][len(data["menu"])-1]["id"]+1
    new_data_menu = {'id':menu_id, 'name':name}
    data['menu'].append(dict(new_data_menu))
    read_file.close()
    with open("menu.json", "w") as write_file:
        json.dump(data, write_file, indent = 4)
    write_file.close()
    return (new_data_menu)

    raise HTTPException (
        status_code = 500, detail = f'Error 500. Internal Server Error. Please check again!'
    )
