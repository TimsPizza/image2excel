from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
import uvicorn

from app.core.config import ENV_CONFIG
from app.routes import auth_router, files_router, tasks_router
from starlette.middleware.cors import CORSMiddleware

# Set the SCRIPT_ROOT_DIR property of ENV_CONFIG to the directory of the main.py file
ENV_CONFIG.SCRIPT_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("startup")
    try:
        yield
    except Exception as e:
        print(f"error: {e}")
    finally:
        print("shutdown")


app = FastAPI(lifespan=lifespan)

app.include_router(files_router) 
app.include_router(auth_router)
app.include_router(tasks_router)
if ENV_CONFIG.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ENV_CONFIG.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host=ENV_CONFIG.BACKEND_HOST, port=ENV_CONFIG.BACKEND_PORT, reload=True)
    

