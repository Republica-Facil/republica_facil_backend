from pydantic import BaseModel, ConfigDict


class RepublicaCreate(BaseModel):
    """Schema para criação de república."""

    nome: str
    cep: str
    rua: str
    numero: str
    complemento: str | None = None
    bairro: str
    cidade: str
    estado: str


class RepublicaPublic(RepublicaCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class RepublicaList(BaseModel):
    republicas: list[RepublicaPublic]
