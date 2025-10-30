from pydantic import BaseModel


class TokenJWT(BaseModel):
    access_token: str
    token_type: str
