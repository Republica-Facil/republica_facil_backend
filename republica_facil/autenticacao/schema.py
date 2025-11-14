from pydantic import BaseModel, EmailStr, Field


class TokenJWT(BaseModel):
    access_token: str
    token_type: str


# fluxo esqueci minha senha
class ForgotPasswordSchema(BaseModel):
    email: EmailStr


class VerifyCodeSchema(BaseModel):
    email: EmailStr
    code: str = Field(
        min_length=6, max_length=6, description='code of 6 digits'
    )


class ResetTokenSchema(BaseModel):
    reset_token: str
    token_type: str = 'Bearer'


class ResetPasswordSchema(BaseModel):
    new_password: str = Field(
        min_length=8, description='new password with at least 8 characters'
    )
