from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class Member(BaseModel):
    fullname: str
    email: EmailStr
    telephone: str
    quarto_id: Optional[int] = None

    # todo member: Member, deve possuir esses atributos


class MemberPublic(Member):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ListMember(BaseModel):
    members: list[MemberPublic]


# ConfigDict é uma função/fábrica que cria um dicionário de configurações para
# um modelo Pydantic.
