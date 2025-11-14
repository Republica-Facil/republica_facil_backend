from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Message(BaseModel):
    message: str


class UserSchema(BaseModel):
    fullname: str
    email: EmailStr
    password: str = Field(min_length=8)
    telephone: str


class UserPublic(BaseModel):
    id: int
    fullname: str
    email: EmailStr
    telephone: str
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    fullname: str
    email: str
    telephone: str


class UserUpdatePassword(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str


class UserList(BaseModel):
    users: list[UserPublic]
