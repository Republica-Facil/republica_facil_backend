from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from republica_facil.autenticacao import router as auth
from republica_facil.membros import router as membro
from republica_facil.quartos import router as quarto
from republica_facil.republicas import router as republica
from republica_facil.settings import Settings
from republica_facil.usuarios import router as user

app = FastAPI()

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        Settings().LOCALHOST_FRONTEND,
        Settings().LOCALHOST_FRONTEND_ADDRESS,
    ],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(republica.router)
app.include_router(membro.router)
app.include_router(quarto.router)
