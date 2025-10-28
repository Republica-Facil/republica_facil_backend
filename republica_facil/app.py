from fastapi import FastAPI

from republica_facil.user.controller import router

app = FastAPI()
app.include_router(router)
