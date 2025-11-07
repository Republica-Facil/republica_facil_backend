from pydantic import BaseModel, ConfigDict


class QuartoSchema(BaseModel):
    numero: int


class QuartoPublic(QuartoSchema):
    id: int
    model_config = ConfigDict(from_attributes=True)


class QuartoList(BaseModel):
    quartos: list[QuartoPublic]


class AdicionarMembroQuarto(BaseModel):
    membro_id: int
