from sqlalchemy.orm import Session

from ..models import User
from ..schemas import UserCreate
from ..security import get_password_hash


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email.lower()).first()


def create_user(db: Session, user: UserCreate):
    db_user = User(email=user.email.lower(), hashed_password=get_password_hash(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user: User):
    db.delete(user)  # il cascade elimina anche i suoi todo
    db.commit()