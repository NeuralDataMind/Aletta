from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core import security
from app.models import project as models
from app import schemas

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=schemas.UserResponse)
def register(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    # Check if user already exists
    db_user = db.query(models.User).filter(
        (models.User.username == user_in.username) |
        (models.User.email == user_in.email)
    ).first()

    if db_user:
        raise HTTPException(
            status_code = 400,
            detail="Username or email already registered"
        )
    
    hashed_pwd = security.get_password_hash(user_in.password)
    new_user = models.User(
        username = user_in.username,
        email = user_in.email,
        hashed_password = hashed_pwd
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.post("/token", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Find User by Username
    user = db.query(models.User).filter(models.User.username == form_data.username).first()

    # Verify password math
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WW-Authenticate": "Bearer"},
        )
    
    # Generate the JWT VIP Pass
    access_token = security.create_access_token(data={"sub": user.username})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }