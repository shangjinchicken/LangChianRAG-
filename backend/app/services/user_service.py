"""用户服务：注册、登录、改密"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token


def create_user(db: Session, username: str, password: str, email: str | None = None) -> User:
    """注册新用户"""
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")

    user = User(
        username=username,
        password_hash=hash_password(password),
        email=email,
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> dict:
    """用户登录，验证凭据后返回 JWT token"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    token = create_access_token(user.id, user.username, user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user.to_dict(),
    }


def change_user_password(db: Session, user: User, old_password: str, new_password: str) -> None:
    """修改密码"""
    if not verify_password(old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="旧密码不正确")
    user.password_hash = hash_password(new_password)
    db.commit()


def init_admin(db: Session) -> None:
    """初始化管理员账户 admin/123456（仅当不存在时创建）"""
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            password_hash=hash_password("123456"),
            email="admin@example.com",
            role="admin",
        )
        db.add(admin)
        db.commit()
