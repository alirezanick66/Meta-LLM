import uvicorn
from backend.app.core.config import settings

if __name__ == "__main__":
    print("🚀 Starting uvicorn server...")
    
    uvicorn.run(
        "backend.app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
    )