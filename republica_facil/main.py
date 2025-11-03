from fastapi import FastAPI

from republica_facil.autenticacao import router as auth
from republica_facil.republicas import router as republicas
from republica_facil.usuarios import router as user

app = FastAPI()
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(republicas.router)
