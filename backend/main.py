import uvicorn
import os

if __name__ == "__main__":
    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", 8000))
    # Run the app
    reload = os.getenv("ENV", "").lower() == "dev"
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=reload)
