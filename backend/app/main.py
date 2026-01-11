from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from app.routers import courses, chapters, users, chat

app = FastAPI(
    title="Micro-Learning App API",
    description="Backend for the AI-powered Micro-Learning platform",
    version="1.0.0"
)

app.include_router(courses.router)
app.include_router(chapters.router)
app.include_router(users.router)
app.include_router(chat.router)

# CORS Configuration
origins = [
    "http://localhost:3000",
    "http://localhost:5173", # Vite default
    "*" # For development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Micro-Learning API is running"}
