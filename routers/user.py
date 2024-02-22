from typing import Annotated
from fastapi import APIRouter, Depends, Request, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from models.user import User, UserForm
from services.auth import authorization

router = APIRouter()

@router.post('/token')
async def login(
  request: Request,
  user_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
  try:
    user: User = request.app.services.users.get_by_username(user_data.username)
  except IndexError:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail=f'Username with email: ${user_data.username} does not exist'
    )
  hashed_password = authorization.hash_password(user_data.password)
  if not hashed_password == user.password:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail='Incorrect password'
    )
  return {
    'access_token': user.id,
    'token_type': 'bearer'
  }


@router.get('/me')
async def get_user(user = Depends(authorization.get_user)):
  return user


@router.get('')
async def get_users(
  request: Request
):
  return request.app.services.users.get_all()


def user_data(
  user_data: UserForm = Body(...)
):
  return user_data

@router.post('')
async def create_user(
  request: Request,
  user_data: Annotated[UserForm, user_data],
):
  return request.app.services.users.create(user_data)


@router.get('/{id}')
async def get_user(
  request: Request,
  id: str
):
  return request.app.services.users.get_one(id)


@router.patch('/{id}')
async def update_user(
  request: Request,
  id: str,
  user: UserForm
):
  return request.app.services.users.update(id, user)

