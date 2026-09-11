"""压测数据准备脚本 —— 预置 N 个测试用户

运行（必须在 backend 目录下，或脚本会自动切到 backend）：
    venv\\Scripts\\python stress/seed.py --users 120

说明：
  - 所有测试用户共用一个密码哈希（同一盐），仅为压测准备提速；
    生产环境严禁复用盐。登录时 bcrypt 校验仍逐个执行，不影响认证压测真实性。
  - 管理员账户 admin/123456 由 init_admin 保证存在。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)  # 让 .env 按 cwd 正确加载

from app.core.database import SessionLocal, Base, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.user_service import init_admin  # noqa: E402

SEED_PASSWORD = "LoadTest123!"   # 与 locustfile.py 保持一致
USER_PREFIX = "load_user_"


def main(users: int) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        init_admin(db)
        shared_hash = hash_password(SEED_PASSWORD)  # 只算一次 bcrypt
        created = 0
        existing = 0
        for i in range(1, users + 1):
            name = f"{USER_PREFIX}{i:04d}"
            if db.query(User).filter(User.username == name).first():
                existing += 1
                continue
            db.add(User(username=name, password_hash=shared_hash, role="user"))
            created += 1
        db.commit()
        print(f"[seed] 目标 {users} 个用户 | 新建 {created} | 已存在 {existing}")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="预置压测用户")
    p.add_argument("--users", type=int, default=120,
                   help="预置用户数（默认 120，覆盖 100 并发 + 余量）")
    args = p.parse_args()
    main(args.users)
