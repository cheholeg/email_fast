import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers import mail_routes, account_routes, service_routes, websocket_routes

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Замените на список разрешенных источников в продакшене
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(mail_routes.router)
app.include_router(account_routes.router)
app.include_router(service_routes.router)
app.include_router(websocket_routes.router)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
