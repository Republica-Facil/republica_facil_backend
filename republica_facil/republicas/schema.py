from pydantic import BaseModel, ConfigDict


class RepublicaCreate(BaseModel):
    """Schema para criação de república."""

    name: str
    address: str


class RepublicaPublic(BaseModel):
    id: int | None = None
    name: str
    address: str
    model_config = ConfigDict(from_attributes=True)


class RepublicaList(BaseModel):
    republicas: list[RepublicaPublic]
