import sys
from pathlib import Path
from tkinter import Tk, Canvas, Entry, PhotoImage
from cryptography.fernet import Fernet
import tkinter as tk
from tkinter import messagebox
import json
import os
import psutil
import subprocess
import pyautogui
import time
import base64
import threading
import urllib3
import urllib.request

# Use the PyInstaller temporary folder if bundled, else use normal assets path
if getattr(sys, 'frozen', False):
    # PyInstaller sets `sys._MEIPASS` when bundled
    ASSETS_PATH = Path(sys._MEIPASS) / 'assets'
else:
    ASSETS_PATH = Path(__file__).parent / 'assets'

# Paths and file definitions
OUTPUT_PATH = Path(__file__).parent
APP_FOLDER = os.path.join(os.path.expanduser("~"), "Documents", "FarSight")
KEY_FILE = os.path.join(APP_FOLDER, "secret.key")
DATA_FILE = os.path.join(APP_FOLDER, "accounts.json")
CONFIG_FILE = os.path.join(APP_FOLDER, "config.json")
RIOT_CERT_PATH = os.path.join(APP_FOLDER, "riotgames.pem")
PEM_URL = "https://static.developer.riotgames.com/docs/lol/riotgames.pem"
PEM_PATH = os.path.join(APP_FOLDER, "riotgames.pem")

BUTTON_START_X = 82
BUTTON_START_Y = 185
BUTTON_SPACING_X = 357  # Distance between buttons left to right
BUTTON_SPACING_Y = 120  # Distance between buttons top to bottom
MAX_BUTTONS = 12  # 3x3 layout
account_buttons = []  # List to store dynamically created account buttons
images = {}  # Dictionary to store preloaded images

def ensure_app_folder():
    # Ensures APP_FOLDER exists and downloads riotgames.pem if missing.
    try:
        if not os.path.exists(APP_FOLDER):
            os.makedirs(APP_FOLDER, exist_ok=True)
        download_riot_pem()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to create app folder: {e}")

def download_riot_pem():
    # Downloads the Riot Games PEM file if it does not exist.
    try:
        if os.path.exists(PEM_PATH):
            messagebox.showinfo("Info", "riotgames.pem is already installed.")
            return
        with urllib.request.urlopen(PEM_URL) as response:
            data = response.read()
            with open(PEM_PATH, "wb") as pem_file:
                pem_file.write(data)
        messagebox.showinfo("Success", f"Successfully downloaded riotgames.pem to:\n{PEM_PATH}")
    except urllib.error.URLError as e:
        messagebox.showerror("Download Error", f"Failed to download riotgames.pem:\n{e.reason}")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")

def on_app_start():
    # Run this when the Tkinter app starts.
    ensure_app_folder()

def relative_to_assets(path: str) -> Path:
    # Update this function to use the new directory
    assets_dir = Path(r"C:\Users\elykr\Desktop\Coding Projects\build\assets\frame0")
    return assets_dir / Path(path)


# Initialize Tkinter Window
window = Tk()
window.geometry("1280x720")
window.configure(bg="#4F4F4F")

http = urllib3.PoolManager(
    cert_reqs="CERT_REQUIRED",
    ca_certs=RIOT_CERT_PATH
)

def load_riot_client_path():
    # Loads Riot Client path from config.json.
    if not os.path.exists(CONFIG_FILE):
        save_riot_client_path("")
        return None
    with open(CONFIG_FILE, "r") as file:
        try:
            data = json.load(file)
            return data.get("riot_client_path", None)
        except json.JSONDecodeError:
            return None

def save_riot_client_path(path):
    # Saves Riot Client path to config.json.
    if not path:
        return
    config_data = {"riot_client_path": path}
    with open(CONFIG_FILE, "w") as file:
        json.dump(config_data, file, indent=4)

def show_riot_path_overlay():
    # Displays an overlay for entering the Riot Client path.
    global riot_path_entry, riot_overlay
    riot_overlay = tk.Frame(window, bg="#000000", width=1280, height=720)
    riot_overlay.place(x=0, y=0)
    input_frame = tk.Frame(riot_overlay, bg="#2E2E2E", padx=20, pady=20)
    input_frame.place(relx=0.5, rely=0.5, anchor="center")
    label = tk.Label(input_frame, text="Enter Riot Client Path:", font=("Convergence Regular", 14), fg="white", bg="#2E2E2E")
    label.pack(pady=10)
    riot_path_entry = tk.Entry(input_frame, width=40, font=("Convergence Regular", 16))
    riot_path_entry.pack(pady=5)
    riot_path_entry.focus_set()
    save_button = tk.Button(input_frame, text="Save", command=save_riot_path_and_close)
    save_button.pack(pady=10)

def save_riot_path_and_close():
    # Saves the Riot Client path and removes the overlay.
    path = riot_path_entry.get()
    if not path.strip():
        return
    save_riot_client_path(path)
    riot_overlay.destroy()

def check_riot_client_path():
    # Ensures Riot Client path is set; if missing, display input overlay.
    riot_client_path = load_riot_client_path()
    if not riot_client_path:
        show_riot_path_overlay()

def find_lockfile(account_name):
    # Continuously searches for the League Client lockfile until it is found.
    while True:
        for proc in psutil.process_iter(attrs=["pid", "name", "exe", "cwd"]):
            try:
                if "LeagueClient" in proc.info["name"]:
                    if proc.info["cwd"]:
                        lockfile_path = os.path.join(proc.info["cwd"], "lockfile")
                        if os.path.exists(lockfile_path):
                            threading.Thread(target=fetch_rank_info, args=(lockfile_path, account_name), daemon=True).start()
                            return
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        time.sleep(1)

def preload_assets():
    # Loads all image assets into a dictionary.
    global images
    images = {}
    asset_files = [f"image_{i}.png" for i in range(1, 15)]
    for asset in asset_files:
        images[asset] = PhotoImage(file=relative_to_assets(asset))

preload_assets()

# Create Canvas
canvas = Canvas(
    window,
    bg="#4F4F4F",
    height=720,
    width=1280,
    bd=0,
    highlightthickness=0,
    relief="ridge"
)
canvas.place(x=0, y=0)

# Top bar and title assets
image_image_1 = PhotoImage(file=relative_to_assets("image_1.png"))
canvas.create_image(0, -23, anchor="nw", image=image_image_1)

image_image_2 = PhotoImage(file=relative_to_assets("image_2.png"))
canvas.create_image(484, 27, anchor="nw", image=image_image_2)

canvas.create_text(506.0, 15.0, anchor="nw", text="FarSight", fill="#FFFFFF",
                   font=("Convergence Regular", 64 * -1))

def hide_popup():
    global popup_elements
    for element in popup_elements:
        try:
            if isinstance(element, int):
                canvas.delete(element)
            else:
                element.destroy()
        except Exception as e:
            pass
    popup_elements = []

def show_popup():
    # Creates and displays the 'New Account' popup.  Example for the rest
    global popup_elements, account_name_entry, username_entry, password_entry
    popup_elements = []
    image_7 = canvas.create_image(0, 0, anchor="nw", image=images["image_7.png"])
    popup_elements.append(image_7)
    image_8 = canvas.create_image(439, 148, anchor="nw", image=images["image_8.png"])
    popup_elements.append(image_8)
    # Add all other image assets similarly with relative pathing...

image_image_5 = PhotoImage(file=relative_to_assets("image_5.png"))
add_account_button = canvas.create_image(934, 597, image=image_image_5, anchor="nw")
canvas.create_text(965.0, 605.0, anchor="nw", text="Add Account", fill="#FFFFFF",
                   font=("Convergence Regular", 40 * -1))
canvas.tag_bind(image_image_5, "<Button-1>", lambda event: show_popup())
canvas.tag_bind(add_account_button, "<Button-1>", lambda event: show_popup())

def close_popup_and_refresh():
    hide_popup()
    refresh_account_buttons()

def show_message(text, color, delay=0):
    message_text = canvas.create_text(640, 620, text=text,
                                      fill=color, font=("Convergence Regular", 24 * -1))
    popup_elements.append(message_text)
    if delay > 0:
        window.after(delay, lambda: (canvas.delete(message_text), close_popup_and_refresh()))

def generate_key():
    # Generates an encryption key if it doesn't exist.
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)

def load_key():
    # Loads the encryption key from the file, generating it if missing.
    generate_key()
    with open(KEY_FILE, "rb") as key_file:
        return key_file.read()

def encrypt_data(data):
    cipher = Fernet(load_key())
    return cipher.encrypt(data.encode()).decode()

def decrypt_data(data):
    cipher = Fernet(load_key())
    return cipher.decrypt(data.encode()).decode()

def save_account():
    # Encrypts and stores the account details securely.
    global account_name_entry, username_entry, password_entry
    account_name = account_name_entry.get().strip()
    username = username_entry.get().strip()
    password = password_entry.get().strip()
    missing_fields = []
    if not account_name:
        missing_fields.append("Account Name")
    if not username:
        missing_fields.append("Username")
    if not password:
        missing_fields.append("Password")
    if missing_fields:
        show_message(f"Missing: {', '.join(missing_fields)}", "#FF0000")
        return
    encrypted_username = encrypt_data(username)
    encrypted_password = encrypt_data(password)
    encrypted_data = {
        "account_name": account_name,
        "username": encrypted_username,
        "password": encrypted_password
    }
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            try:
                data = json.load(file)
                if isinstance(data, dict):
                    accounts = data.get("accounts", [])
                elif isinstance(data, list):
                    accounts = data
                else:
                    accounts = []
            except json.JSONDecodeError:
                accounts = []
    else:
        accounts = []
    if not isinstance(accounts, list):
        accounts = []
    accounts.append(encrypted_data)
    with open(DATA_FILE, "w") as file:
        json.dump({"accounts": accounts}, file, indent=4)
    show_message("Account Saved!", "#00FF00")
    refresh_account_buttons()
    hide_popup()

def load_accounts():
    # Loads accounts from accounts.json.
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as file:
        try:
            data = json.load(file)
            if isinstance(data, dict) and "accounts" in data:
                return data["accounts"]
            elif isinstance(data, list):
                return data
            else:
                return []
        except json.JSONDecodeError:
            return []

def display_account_buttons():
    # Creates buttons for saved accounts and displays their rank.
    global account_buttons
    accounts = load_accounts()
    if not isinstance(accounts, list):
        accounts = []
    if "button_bg" not in images:
        images["button_bg"] = PhotoImage(file=relative_to_assets("image_6.png"))
    num_accounts = min(len(accounts), MAX_BUTTONS)
    row = 0
    col = 0
    for i in range(num_accounts):
        try:
            account = accounts[i]
            account_name = account.get("account_name", "Unknown")
            stored_rank = account.get("rank", "")
            x_position = BUTTON_START_X + (col * BUTTON_SPACING_X) + 190
            y_position = BUTTON_START_Y + (row * BUTTON_SPACING_Y)
            button = canvas.create_image(x_position, y_position, image=images["button_bg"])
            button_text = canvas.create_text(x_position, y_position, text=account_name,
                                             fill="#FFFFFF", font=("Convergence Regular", 24 * -1))
            rank_text = canvas.create_text(x_position, y_position + 30, text=stored_rank,
                                           fill="#AAAAAA", font=("Convergence Regular", 20 * -1))
            account_buttons.extend([button, button_text, rank_text])
            canvas.tag_bind(button, "<Button-1>", lambda event, acc=account: launch_game(acc))
            canvas.tag_bind(button_text, "<Button-1>", lambda event, acc=account: launch_game(acc))
            col += 1
            if col == 3:
                col = 0
                row += 1
        except IndexError:
            break
    create_manage_accounts_button()

def create_manage_accounts_button():
    # Creates the 'Manage Accounts' button using the same image as 'Add Account'.
    if "manage_accounts" not in images:
        images["manage_accounts"] = PhotoImage(file=relative_to_assets("image_5.png"))
    manage_button = canvas.create_image(110, 597, anchor="nw", image=images["manage_accounts"])
    manage_text = canvas.create_text(125, 610, anchor="nw", text="Manage Accounts", fill="#FFFFFF",
                                     font=("Convergence Regular", 34 * -1))
    canvas.tag_bind(manage_button, "<Button-1>", lambda event: show_manage_accounts_overlay())
    canvas.tag_bind(manage_text, "<Button-1>", lambda event: show_manage_accounts_overlay())

def show_manage_accounts_overlay():
    # Displays an overlay listing all saved accounts with a delete button for each.
    global manage_overlay
    manage_overlay = tk.Frame(window, bg="#000000", width=window.winfo_width(), height=window.winfo_height())
    manage_overlay.place(x=0, y=0)
    manage_frame = tk.Frame(manage_overlay, bg="#2E2E2E", padx=20, pady=20)
    manage_frame.place(relx=0.5, rely=0.5, anchor="center")
    title_label = tk.Label(manage_frame, text="Manage Accounts", font=("Convergence Regular", 16),
                            fg="white", bg="#2E2E2E")
    title_label.pack(pady=10)
    accounts = load_accounts()
    if not accounts:
        tk.Label(manage_frame, text="No accounts saved.", font=("Convergence Regular", 12),
                 fg="white", bg="#2E2E2E").pack(pady=5)
    else:
        for account in accounts:
            account_name = account.get("account_name", "Unknown")
            row_frame = tk.Frame(manage_frame, bg="#3E3E3E")
            row_frame.pack(fill="x", pady=5, padx=10)
            name_label = tk.Label(row_frame, text=account_name, font=("Convergence Regular", 14),
                                  fg="white", bg="#3E3E3E")
            name_label.pack(side="left", padx=10)
            delete_button = tk.Button(row_frame, text="Delete", font=("Convergence Regular", 12),
                                      bg="#FF4C4C", fg="white", command=lambda acc=account: delete_account(acc))
            delete_button.pack(side="right", padx=10)

def delete_account(account):
    # Deletes the selected account.
    accounts = load_accounts()
    accounts = [acc for acc in accounts if acc["account_name"] != account["account_name"]]
    with open(DATA_FILE, "w") as file:
        json.dump({"accounts": accounts}, file, indent=4)
    show_message("Account Deleted!", "#FF0000")
    refresh_account_buttons()
    hide_manage_accounts_overlay()

def hide_manage_accounts_overlay():
    global manage_overlay
    manage_overlay.destroy()

def refresh_account_buttons():
    # Refreshes the account buttons after changes.
    for button in account_buttons:
        canvas.delete(button)
    account_buttons.clear()
    display_account_buttons()

def launch_game(account):
    # Launches the game with the selected account.
    riot_client_path = load_riot_client_path()
    account_name = account.get("account_name", "Unknown")
    username = decrypt_data(account["username"])
    password = decrypt_data(account["password"])
    # Implement the logic to launch the game with the account credentials
    print(f"Launching game for {account_name}...")
    # pyautogui or subprocess code for logging in would go here
    subprocess.Popen([riot_client_path])
    time.sleep(5)
    pyautogui.write(username)
    time.sleep(0.1)
    pyautogui.press("tab")
    time.sleep(0.1)
    pyautogui.write(password)
    time.sleep(0.1)
    pyautogui.press("enter")
    threading.Thread(target=find_lockfile, args=(account["account_name"],), daemon=True).start()

def fetch_rank_info(lockfile_path, account_name):
    """Fetches Solo/Duo rank details with retry handling."""
    try:
        if not lockfile_path or not os.path.exists(lockfile_path):
            return
        with open(lockfile_path, "r") as lockfile:
            content = lockfile.read().strip().split(":")
            port, auth_token, protocol = content[2], content[3], content[4]
        headers = {
            "Authorization": f"Basic {base64.b64encode(f'riot:{auth_token}'.encode()).decode()}",
            "Accept": "application/json"
        }
        url = f"{protocol}://127.0.0.1:{port}/lol-ranked/v1/current-ranked-stats"
        for _ in range(5):
            response = http.request("GET", url, headers=headers)
            if response.status == 200:
                data = json.loads(response.data.decode("utf-8"))
                ranked_info = data.get("queues", [])
                for queue in ranked_info:
                    if queue["queueType"] == "RANKED_SOLO_5x5":
                        tier = queue.get("tier", "Unranked")
                        division = queue.get("division", "N/A")
                        leaguePoints = queue.get("leaguePoints", 0)
                        new_rank = f"{tier} {division} - {leaguePoints} LP"
                        update_account_rank(account_name, new_rank)
                        return new_rank
            elif response.status == 500:
                time.sleep(3)
            else:
                return None
        return None
    except Exception as e:
        return None

def update_account_rank(account_name, new_rank):
    """Updates the rank of the given account in accounts.json."""
    accounts = load_accounts()
    updated = False
    for account in accounts:
        if account["account_name"] == account_name:
            account["rank"] = new_rank
            updated = True
            break
    if not updated:
        accounts.append({"account_name": account_name, "rank": new_rank})
    with open(DATA_FILE, "w") as file:
        json.dump(accounts, file, indent=4)
    display_account_buttons()

on_app_start()
check_riot_client_path()
display_account_buttons()

window.resizable(False, False)
window.mainloop()
