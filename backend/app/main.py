import os
from dotenv import load_dotenv

from fastapi import FastAPI, File, HTTPException, UploadFile
from contextlib import asynccontextmanager

from app.database import SessionDep, create_db_and_tables
from app.models import GeneratedReport
from app.routes import router

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield
    
app = FastAPI(lifespan=lifespan)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)