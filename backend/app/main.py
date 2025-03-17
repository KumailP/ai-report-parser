from dotenv import load_dotenv

from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.database import create_db_and_tables
from app.routes import router

# Load environment variables from .env file
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database and tables when app starts
    create_db_and_tables()
    yield
    
app = FastAPI(lifespan=lifespan)

# Include API routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    # Run the FastAPI application
    uvicorn.run(app, host="127.0.0.1", port=8000)