import uvicorn
import webbrowser
import threading
import time

def open_browser():
    # Wait a moment for the server to start before opening the browser
    time.sleep(1.5)
    webbrowser.open("http://localhost:8000/")

if __name__ == "__main__":
    print("Starting server and launching browser...")
    # Start the browser in a separate thread so it doesn't block the server startup
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run the uvicorn server
    uvicorn.run("app.main:app", host="localhost", port=8000, reload=True)
