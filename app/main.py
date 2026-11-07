import logging
import os
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from . import crud, schemas
from .models import Base, SessionLocal, User, engine
from .security import ALGORITHM, SECRET_KEY, create_access_token, verify_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Todo API", description="API per gestire todo con autenticazione JWT", version="1.1.0")

# Rate limiting (disattivabile nei test con RATE_LIMIT_ENABLED=false)
limiter = Limiter(
    key_func=get_remote_address,
    enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: origini consentite da variabile d'ambiente (separate da virgola)
allowed_origins = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,  # il token viaggia nell'header Authorization, non in cookie
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Credenziali non valide",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise credentials_exception
    email = payload.get("sub")
    if not email:
        raise credentials_exception
    user = crud.get_user_by_email(db, email=email)
    if user is None or not user.is_active:
        raise credentials_exception
    return user


@app.get("/")
def read_root():
    return {"message": "Todo API", "docs": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.delete("/me", status_code=204)
@limiter.limit("3/minute")
def delete_account(
    request: Request,
    payload: schemas.AccountDelete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Password errata")
    crud.delete_user(db, current_user)


@app.post("/register", response_model=schemas.UserInDB, status_code=201)
@limiter.limit("3/minute")
def register(request: Request, user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email già registrata")
    logger.info("Nuovo utente registrato")
    return crud.create_user(db=db, user=user)


@app.post("/login", response_model=schemas.Token)
@limiter.limit("5/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not user.is_active or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Email o password errati",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": create_access_token(data={"sub": user.email}), "token_type": "bearer"}


@app.post("/todos/", response_model=schemas.TodoInDB, status_code=201)
def create_todo(todo: schemas.TodoCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.create_todo(db=db, todo=todo, owner_id=current_user.id)


@app.get("/todos/", response_model=list[schemas.TodoInDB])
def read_todos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.get_todos(db, skip=skip, limit=limit, owner_id=current_user.id)


@app.get("/todos/{todo_id}", response_model=schemas.TodoInDB)
def read_todo(todo_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_todo = crud.get_todo(db, todo_id=todo_id, owner_id=current_user.id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo non trovato")
    return db_todo


@app.put("/todos/{todo_id}", response_model=schemas.TodoInDB)
def update_todo(
    todo_id: int,
    todo: schemas.TodoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_todo = crud.update_todo(db, todo_id=todo_id, todo=todo, owner_id=current_user.id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo non trovato")
    return db_todo


@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not crud.delete_todo(db, todo_id=todo_id, owner_id=current_user.id):
        raise HTTPException(status_code=404, detail="Todo non trovato")
    return {"message": f"Todo {todo_id} eliminato"}
