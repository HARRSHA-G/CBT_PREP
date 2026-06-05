import os
import sys
import threading
import time
import socket
import webview
import subprocess

# Setup persistent directory
HOME_DIR = os.path.expanduser("~")
DATA_DIR = os.path.join(HOME_DIR, ".cbt_engine_data")
os.makedirs(DATA_DIR, exist_ok=True)

# Export an environment variable so Django settings know where to put the DB
os.environ["CBT_DATA_DIR"] = DATA_DIR

# Find a free port
def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

# Set up paths
base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
os.chdir(base_dir)

# Start Django Server
port = get_free_port()
server_process = None

def start_server():
    global server_process
    
    # We must call manage.py migrate to ensure the DB exists in DATA_DIR
    subprocess.run([sys.executable, "manage.py", "migrate"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    server_process = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

# Give it time to bind
time.sleep(2)

# Create WebView Window
window = webview.create_window(
    'CBT Practice Engine',
    f'http://127.0.0.1:{port}',
    width=1280,
    height=800,
    min_size=(800, 600),
    background_color='#f8f9fa'
)

def on_closing():
    if server_process:
        server_process.terminate()
        server_process.wait()

window.events.closed += on_closing

if __name__ == '__main__':
    webview.start(gui='qt', debug=False)
