from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.routers import user_router
from app.routers import webhook, tools, google_callback, short_links


app = FastAPI(title="Luximus API", version="0.1.0")

app.include_router(webhook.router)
app.include_router(tools.router)
app.include_router(google_callback.router)
app.include_router(short_links.router)

@app.get("/")
def read_root():
    return {"health": "ok"}

@app.get("/integration-success")
def integration_success():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Integration Success</title>
        <style>
            body {
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                font-family: Arial, sans-serif;
                background-color: #f0f0f0;
            }
            .container {
                text-align: center;
            }
            .icon {
                font-size: 50px;
                color: green;
            }
            .message {
                font-size: 24px;
                margin-top: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">✔️</div>
            <div class="message">Integração realizada com sucesso!</div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)