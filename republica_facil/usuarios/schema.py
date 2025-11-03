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
    republicas: str
    model_config = ConfigDict(from_attributes=True)


class UserList(BaseModel):
    users: list[UserPublic]
