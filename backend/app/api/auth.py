"""认证相关 API：注册、登录、改密"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.auth import RegisterRequest, LoginRequest, ChangePasswordRequest, TokenResponse, UserResponse
from app.services import user_service

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    user = user_service.create_user(db, req.username, req.password, req.email)
    return user.to_dict()


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户登录，返回 JWT token"""
    return user_service.authenticate_user(db, req.username, req.password)


@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改密码（需要旧密码验证）"""
    user_service.change_user_password(db, current_user, req.old_password, req.new_password)
    return {"message": "密码修改成功"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    """获取当前登录用户信息"""
    return current_user.to_dict()
