from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from republica_facil.autenticacao import router as auth
from republica_facil.membros import router as membros
from republica_facil.republicas import router as republicas
from republica_facil.usuarios import router as user

app = FastAPI()

# Configuração de CORS para permitir frontend na porta 3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos HTTP
    allow_headers=["*"],  # Permite todos os headers
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(republicas.router)
app.include_router(membros.router)
