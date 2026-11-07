from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ---------- Utenti ----------
class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def password_rules(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La password deve essere di almeno 8 caratteri")
        if len(v.encode("utf-8")) > 72:  # limite di bcrypt: 72 BYTE, non caratteri
            raise ValueError("La password non può superare i 72 byte")
        return v


class UserInDB(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool


class AccountDelete(BaseModel):
    password: str


# ---------- Token ----------
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# ---------- Todo ----------
class TodoBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)


class TodoCreate(TodoBase):
    pass


class TodoUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    completed: Optional[bool] = None


class TodoInDB(TodoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    completed: bool
