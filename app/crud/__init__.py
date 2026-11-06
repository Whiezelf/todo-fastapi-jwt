from sqlalchemy.orm import Session

from ..models import Todo
from ..schemas import TodoCreate, TodoUpdate
from .user import create_user, get_user_by_email  # noqa: F401


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
