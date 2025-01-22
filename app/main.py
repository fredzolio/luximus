from fastapi import FastAPI
from app.routers import user_router
from app.services import webhook

app = FastAPI(title="Luximus API", version="0.1.0")

app.include_router(user_router.router)
app.include_router(webhook.router)

@app.get("/")
def read_root():
    return {"health": "ok"}
