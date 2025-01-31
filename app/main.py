from fastapi import FastAPI
from app.routers import user_router
from app.routers import webhook, tools, google_callback


app = FastAPI(title="Luximus API", version="0.1.0")

app.include_router(webhook.router)
app.include_router(tools.router)
app.include_router(google_callback.router)

@app.get("/")
def read_root():
    return {"health": "ok"}