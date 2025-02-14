from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

from app.core.config import ENV_CONFIG
from app.routes import auth_router, files_router
from starlette.middleware.cors import CORSMiddleware

@asynccontextmanager
def lifespan():
    print("startup")
    try:
        yield
    finally:
        print("shutdown")

app = FastAPI(lifespan=lifespan)
app.include_router(files_router)
app.include_router(auth_router)
if ENV_CONFIG.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ENV_CONFIG.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )



if __name__ == "__main__":
    uvicorn.run(app, host=ENV_CONFIG.BACKEND_HOST, port=ENV_CONFIG.BACKEND_PORT)

