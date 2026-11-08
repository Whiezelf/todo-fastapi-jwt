from sqlalchemy.orm import Session

from ..models import Todo
from ..schemas import TodoCreate, TodoUpdate
from .user import create_user, delete_user, get_user_by_email  # noqa: F401
from datetime import datetime, timezone


def get_todo(db: Session, todo_id: int, owner_id: int):
    return db.query(Todo).filter(Todo.id == todo_id, Todo.owner_id == owner_id).first()


def get_todos(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    return db.query(Todo).filter(Todo.owner_id == owner_id).order_by(Todo.id).offset(skip).limit(limit).all()


def create_todo(db: Session, todo: TodoCreate, owner_id: int):
    db_todo = Todo(title=todo.title, description=todo.description, owner_id=owner_id)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo


def update_todo(db: Session, todo_id: int, todo: TodoUpdate, owner_id: int):
    db_todo = get_todo(db, todo_id, owner_id)
    if db_todo is None:
        return None
    for key, value in todo.model_dump(exclude_none=True).items():
        setattr(db_todo, key, value)
    db.commit()
    db.refresh(db_todo)
    return db_todo


def delete_todo(db: Session, todo_id: int, owner_id: int):
    db_todo = get_todo(db, todo_id, owner_id)
    if db_todo is None:
        return False
    db.delete(db_todo)
    db.commit()
    return True


from ..models import PasswordResetToken
from ..security import generate_reset_token, hash_reset_token
from datetime import datetime, timezone


def create_reset_token(db: Session, user_id: int) -> str:
    raw_token, token_hash, expires_at = generate_reset_token()
    db.add(PasswordResetToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at))
    db.commit()
    return raw_token


def get_valid_reset_token(db: Session, raw_token: str):
    token_hash = hash_reset_token(raw_token)
    entry = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
    if entry is None or entry.used:
        return None

    expires_at = entry.expires_at
    if expires_at.tzinfo is None:  # SQLite non conserva il fuso orario: lo riattacchiamo
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        return None
    return entry


def mark_token_used(db: Session, entry: PasswordResetToken) -> None:
    entry.used = True
    db.commit()