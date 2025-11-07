from pydantic import BaseModel, ConfigDict


class MembroSimples(BaseModel):
    """Schema simplificado de membro para listar em quarto."""

    id: int
    fullname: str
    email: str
    model_config = ConfigDict(from_attributes=True)


class QuartoSchema(BaseModel):
    numero: int


class QuartoPublic(QuartoSchema):
    id: int
    membros: list[MembroSimples] = []
    model_config = ConfigDict(from_attributes=True)


class QuartoList(BaseModel):
    quartos: list[QuartoPublic]


class AdicionarMembroQuarto(BaseModel):
    membro_id: int
