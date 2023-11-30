import os
from datetime import timedelta
from typing import List

from fastapi import APIRouter, HTTPException, Form
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette.status import HTTP_401_UNAUTHORIZED

from crud import user_crud
from crud.user_crud import get_current_user
from db import get_db
from models.usermodel import UserModel
from schemas.token_schemas import TokenSchema
from schemas.user_schemas import UserSchema, UserCreateSchema
from utils.security import authenticate_user, create_access_token

from dotenv import load_dotenv
load_dotenv()

ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')

user_router = APIRouter()


@user_router.get("", response_model=List[UserSchema], summary=" Get all users")
def users(db: Session = Depends(get_db)):
    """
    Returns a list of all users
    """
    users = user_crud.get_all_users(db)
    return list(users)


@user_router.get("/{email:str}", response_model=UserSchema, summary="Get user by email")
def get_user(email: str, db: Session = Depends(get_db)) -> UserSchema:
    """"
    Return a user by passing email as a URL parameter
    Returns a 404 if email does not exist in database
    """
    user = user_crud.get_user_by_email(db, email)
    if user:
        return user
    else:
        return {'message': 'user not found'}, 404


@user_router.post("", response_model=UserSchema, summary="Signup as a new user")
def sign_up(user_data: UserCreateSchema, db: Session = Depends(get_db)):
    """
    Create a new user with the following information:

    - **email**: each user must have a unique email
    - **first_name**: 
    - **last_name**: 
    - **password**: strong password
    
    """
    user = user_crud.get_user_by_email(db, user_data.email)
    if user:
        raise HTTPException(
            status_code=409,
            detail="email exist",
        )
    new_user = user_crud.add_user(db, user_data)
    return new_user


@user_router.post("/login", response_model=TokenSchema, summary="Login using email and password")
def login_for_access_token(
        db: Session = Depends(get_db),
        form_data: OAuth2PasswordRequestForm = Depends()
):
    
    """
    Login/Signin with the following information:

    - **email**: This is required
    - **password**: THis is required

    **NB** : username is treated as email
    """
    user_data = authenticate_user(db, form_data.username, form_data.password)
    if not user_data:
        raise HTTPException(
            HTTP_401_UNAUTHORIZED,
            detail="invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_expires_date = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={'sub': user_data.email},
        expires_delta=token_expires_date,
    )
    return {'access_token': access_token, 'token_type': 'bearer'}


@user_router.get("/me", response_model=UserSchema, summary="get the currently logged in user")
def get_current_user(user_data: UserModel = Depends(get_current_user)):
    """
    This endpoints exposes hthe currently authenticated user
    """

    return user_data