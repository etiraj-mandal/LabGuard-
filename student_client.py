import psutil
import socket
import time
import requests
from datetime import datetime
import tkinter as tk
import threading
import pygetwindow as gw

# ===============================
# CONFIGURATION
# ===============================
SERVER_URL = "http://{server_ip}:8080/update" 
STATUS_URL = "http://{server_ip}:8080/get_status" # New endpoint for checking approval
PC_NAME = socket.gethostname()
ADMIN_PASSWORD = "lab123" 

BLOCKED_APPS = ["game.exe", "vlc.exe"]
BLOCKED_KEYWORDS = ["roblox", "crazygames", "facebook", "youtube", "insta"] 
CHECK_INTERVAL = 3 

# State Management
is_first_check = True
violation_counter = 0
is_locked = False

# ===============================
# APPROVAL CHECK LOGIC
# ===============================
def check_admin_permission():
    """Polls the server to see if the Admin has clicked 'APPROVE UNLOCK'."""
    try:
        response = requests.get(f"{STATUS_URL}/{PC_NAME}", timeout=2)
        if response.status_code == 200:
            status_data = response.json()
            # If is_violation is False, it means the Admin clicked Approve
            return not status_data.get("is_violation", True)
    except:
        pass
    return False

# ===============================
# ADMIN LOCK SCREEN UI
# ===============================
def show_lock_screen():
    global is_locked, violation_counter
    is_locked = True
    
    root = tk.Tk()
    root.title("SYSTEM LOCKED")
    root.attributes("-topmost", True)
    root.attributes("-fullscreen", True) 
    root.configure(bg="#450a0a")
    
    # Disable Alt+F4 or closing the window
    root.protocol("WM_DELETE_WINDOW", lambda: None)

    frame = tk.Frame(root, bg="#450a0a")
    frame.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(frame, text="🔒 SYSTEM LOCKED", fg="white", bg="#450a0a", 
             font=("Arial", 36, "bold")).pack(pady=20)
    
    status_label = tk.Label(frame, text="WAITING FOR ADMIN TO APPROVE UNLOCK...",
             fg="yellow", bg="#450a0a", font=("Arial", 14, "italic"))
    status_label.pack(pady=10)

    # Password entry starts DISABLED
    password_entry = tk.Entry(frame, show="*", font=("Arial", 20), justify='center', 
                              state="disabled", disabledbackground="#2a0505")
    password_entry.pack(pady=20)

    def check_for_approval():
        """Loop inside the UI to check if Admin clicked 'Approve'."""
        if is_locked:
            if check_admin_permission():
                password_entry.config(state="normal", disabledbackground="white")
                status_label.config(text="✅ ADMIN APPROVED: Enter Password to Unlock", fg="#4ade80")
                password_entry.focus_force()
            else:
                # Check again in 2 seconds
                root.after(2000, check_for_approval)

    def attempt_unlock(event=None):
        global is_locked, violation_counter
        if password_entry.get() == ADMIN_PASSWORD:
            is_locked = False
            violation_counter = 0 
            
            # Immediately notify server that the PC is now MONITORING (Clean)
            try:
                requests.post(SERVER_URL, json={
                    "pc_name": PC_NAME,
                    "cpu": psutil.cpu_percent(),
                    "ram": psutil.virtual_memory().percent,
                    "blocked_apps": [],
                    "status": "MONITORING",
                    "time": datetime.now().strftime("%H:%M:%S")
                }, timeout=2)
            except:
                pass

            root.destroy()
        else:
            status_label.config(text="❌ Incorrect Admin Password", fg="#f87171")
            password_entry.delete(0, tk.END)

    password_entry.bind('<Return>', attempt_unlock)
    
    # Start the approval background check
    root.after(2000, check_for_approval)
    root.mainloop()

# ===============================
# WARNING UI (FOR FIRST VIOLATION)
# ===============================
def show_warning(detail):
    def create_window():
        root = tk.Tk()
        root.attributes("-topmost", True)
        root.geometry("450x180+500+300")
        root.configure(bg="#b91c1c")
        root.overrideredirect(True) 
        
        tk.Label(root, text="⚠ WARNING", fg="yellow", bg="#b91c1c", 
                 font=("Arial", 16, "bold")).pack(pady=10)
        
        tk.Label(root, text=f"Violation: {detail}\nSecond violation will lock this PC.",
                 fg="white", bg="#b91c1c", font=("Arial", 11)).pack(expand=True)
        
        root.after(5000, root.destroy)
        root.mainloop()
        
    threading.Thread(target=create_window, daemon=True).start()

# ===============================
# DETECTION & ENFORCEMENT
# ===============================
def enforce_rules():
    global is_first_check, violation_counter, is_locked
    
    if is_locked:
        return ["SYSTEM_LOCKED"]

    violations = []

    # 1. Close Blocked Apps
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in BLOCKED_APPS:
                violations.append(f"App: {proc.info['name']}")
                proc.terminate()
        except: pass

    # 2. Close Blocked Websites
    try:
        all_windows = gw.getAllTitles()
        for title in all_windows:
            for keyword in BLOCKED_KEYWORDS:
                if keyword.lower() in title.lower():
                    violations.append(f"Site: {keyword}")
                    target_wins = gw.getWindowsWithTitle(title)
                    for win in target_wins:
                        win.close()
    except: pass

    # 3. Handle Logic
    if is_first_check:
        is_first_check = False
        return []
        
    if violations:
        violation_counter += 1
        if violation_counter >= 2:
            threading.Thread(target=show_lock_screen, daemon=True).start()
        else:
            show_warning(violations[0])
            
    return violations

# ===============================
# MAIN LOOP
# ===============================
print(f"--- LabGuard Ultra Shield Active on {PC_NAME} ---")

while True:
    found_violations = enforce_rules()
    
    data = {
        "pc_name": PC_NAME,
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "blocked_apps": found_violations,
        "status": "LOCKED" if is_locked else "MONITORING",
        "time": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    }

    try:
        requests.post(SERVER_URL, json=data, timeout=2)
    except:
        pass

    time.sleep(CHECK_INTERVAL)
