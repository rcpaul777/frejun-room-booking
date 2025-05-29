from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import crud, models, schemas, security
from deps import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

@router.post("/register", response_model=schemas.UserResponse)
def register(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user.
    """
    # Check if user already exists
    user = crud.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists."
        )
    
    # Create new user
    user = crud.create_user(db, user=user_in)
    # Ensure gender is a string for Pydantic
    user_dict = user.__dict__.copy()
    if hasattr(user, 'gender') and hasattr(user.gender, 'value'):
        user_dict['gender'] = user.gender.value
    return schemas.UserResponse(**user_dict)

@router.post("/token", response_model=schemas.Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = crud.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(
    current_user: models.User = Depends(security.get_current_user),
) -> Any:
    """
    Get current user information.
    """
    user_dict = current_user.__dict__.copy()
    if hasattr(current_user, 'gender') and hasattr(current_user.gender, 'value'):
        user_dict['gender'] = current_user.gender.value
    return schemas.UserResponse(**user_dict)
