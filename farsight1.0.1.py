import sys
from pathlib import Path
from tkinter import Tk, Canvas, Entry, PhotoImage, Scrollbar, Frame
from cryptography.fernet import Fernet
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import requests
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
from functools import partial
import webbrowser
from PIL import Image, ImageTk
import io
from embedded_images import embedded_images_b64
from ranked_button_images import ranked_button_images
from main_menu_images_b64 import main_menu_images_b64
from rank_icons_b64 import rank_icons

# Paths and file definitions
OUTPUT_PATH = Path(__file__).parent
APP_FOLDER = os.path.join(os.path.expanduser("~"), "Documents", "FarSight")
KEY_FILE = os.path.join(APP_FOLDER, "secret.key")
DATA_FILE = os.path.join(APP_FOLDER, "accounts.json")
CONFIG_FILE = os.path.join(APP_FOLDER, "config.json")
RIOT_CERT_PATH = os.path.join(APP_FOLDER, "riotgames.pem")
PEM_URL = "https://static.developer.riotgames.com/docs/lol/riotgames.pem"
PEM_PATH = os.path.join(APP_FOLDER, "riotgames.pem")
lockfile_found = False
lockfile_path = None
league_client_status = 0
manage_overlay = None
manage_frame = None
main_menu_opened = False
canvas = None

BUTTON_START_X = 82
BUTTON_START_Y = 185
BUTTON_SPACING_X = 357  # Distance between buttons left to right
BUTTON_SPACING_Y = 120  # Distance between buttons top to bottom
MAX_BUTTONS = 12  # 3x3 layout
account_buttons = []  # List to store dynamically created account buttons
images = {}  # Dictionary to store preloaded images
popup_elements = []  # Initialize an empty list globally
image_references = []
main_menu_images = {}
champid = {}

def ensure_app_folder():
    # Ensures APP_FOLDER exists and downloads riotgames.pem if missing.
    try:
        if not os.path.exists(APP_FOLDER):
            os.makedirs(APP_FOLDER, exist_ok=True)
        download_riot_pem()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to create app folder: {e}")

def download_riot_pem():
    # Checks for the Riot Games PEM file and downloads if not present
    try:
        if os.path.exists(PEM_PATH):
            # Silently continue if the file already exists
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

# Initialize Tkinter Window
window = Tk()
window.title("FarSight")
window.geometry("1280x720")
window.configure(bg="#4F4F4F")

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

if hasattr(sys, '_MEIPASS'):
    icon_path = Path(sys._MEIPASS) / "farsight_trinket_icon.ico"
else:
    icon_path = Path(__file__).parent / "farsight_trinket_icon.ico"

# Set the icon only if the file exists to avoid runtime errors
if icon_path.exists():
    window.iconbitmap(icon_path)
else:
    print(f"Icon file not found: {icon_path}")

label = tk.Label(window, text="FarSight Icon Test Window")
label.pack(pady=50)

def get_image_from_b64(b64_str):
    return PhotoImage(data=b64_str)

def get_image_from_b64(b64_str):
    return PhotoImage(data=b64_str)


# Preload main menu images
main_menu_images = {}
for asset_name, b64_str in main_menu_images_b64.items():
    main_menu_images[asset_name] = get_image_from_b64(b64_str)

def preload_assets():
    global images
    images = {}
    for asset_name, b64_str in embedded_images_b64.items():
        images[asset_name] = get_image_from_b64(b64_str)
    for asset_name, b64_str in main_menu_images_b64.items():
        main_menu_images[asset_name] = get_image_from_b64(b64_str)

preload_assets()

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

def preload_assets():
    global images
    images = {}
    for asset_name, b64_str in embedded_images_b64.items():
        images[asset_name] = get_image_from_b64(b64_str)

preload_assets()

def hide_popup(canvas):
    global popup_elements
    for element in popup_elements:
        try:
            if isinstance(element, int):
                canvas.delete(element)
            else:
                element.destroy()
        except Exception:
            pass
    popup_elements = []

def show_popup(canvas):
    """Creates and displays the 'New Account' popup dynamically."""
    global popup_elements, images, account_name_entry, username_entry, password_entry
    popup_elements = []
    image_7 = canvas.create_image(0, 0, anchor="nw", image=images["image_7.png"])  # Opaque BG
    popup_elements.append(image_7)
    image_8 = canvas.create_image(439, 148, anchor="nw", image=images["image_8.png"])  # PopUp BG
    popup_elements.append(image_8)
    image_9 = canvas.create_image(490, 275, anchor="nw", image=images["image_9.png"])
    popup_elements.append(image_9)
    image_10 = canvas.create_image(459, 165, anchor="nw", image=images["image_10.png"])
    popup_elements.append(image_10)
    image_11 = canvas.create_image(490, 376, anchor="nw", image=images["image_11.png"])
    popup_elements.append(image_11)
    image_12 = canvas.create_image(490, 477, anchor="nw", image=images["image_12.png"])
    popup_elements.append(image_12)
    cancel_button = canvas.create_image(629, 547, anchor="nw", image=images["image_13.png"])
    popup_elements.append(cancel_button)
    save_button = canvas.create_image(490, 547, anchor="nw", image=images["image_14.png"])
    popup_elements.append(save_button)
    newaccount_text = canvas.create_text(482.0, 170.0, anchor="nw", text="New Account", fill="#FFFFFF", font=("Convergence Regular", 48 * -1))
    popup_elements.append(newaccount_text)
    accountname_text = canvas.create_text(514.0, 237.0, anchor="nw", text="Account Name", fill="#FFFFFF", font=("Convergence Regular", 32 * -1))
    popup_elements.append(accountname_text)
    un_text = canvas.create_text(549, 338, anchor="nw", text="Username", fill="#FFFFFF", font=("Convergence Regular", 32 * -1))
    popup_elements.append(un_text)
    pw_text = canvas.create_text(549, 439, anchor="nw", text="Password", fill="#FFFFFF", font=("Convergence Regular", 32 * -1))
    popup_elements.append(pw_text)
    save_text = canvas.create_text(520.0, 553.0, anchor="nw", text="Save", fill="#000000", font=("Convergence Regular", 32 * -1))
    popup_elements.append(save_text)
    cancel_text = canvas.create_text(643.0, 553.0, anchor="nw", text="Cancel", fill="#000000", font=("Convergence Regular", 32 * -1))
    popup_elements.append(cancel_text)
    account_name_entry = Entry(window, font=("Convergence Regular", 20))
    account_name_entry.place(x=514, y=281, width=223, height=38)
    popup_elements.append(account_name_entry)
    username_entry = Entry(window, font=("Convergence Regular", 20))
    username_entry.place(x=514, y=382, width=223, height=38)
    popup_elements.append(username_entry)
    password_entry = Entry(window, font=("Convergence Regular", 20))
    password_entry.place(x=514, y=483, width=223, height=38)
    popup_elements.append(password_entry)
    canvas.tag_bind(save_button, "<Button-1>", lambda event: save_account())
    canvas.tag_bind(save_text, "<Button-1>", lambda event: save_account())
    canvas.tag_bind(cancel_button, "<Button-1>", lambda event: hide_popup(canvas))
    canvas.tag_bind(cancel_text, "<Button-1>", lambda event: hide_popup(canvas))

def close_popup_and_refresh():
    hide_popup(canvas)
    refresh_account_buttons()

def show_message(popup_elements, color, text, delay=0,):
    if 'popup_elements' not in globals():
        popup_elements = []
    
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

    message_text = canvas.create_text(640, 620, text=text,fill=color, font=("Convergence Regular", 24 * -1))
    
    if delay > 0:
        window.after(delay, lambda: (canvas.delete(message_text), close_popup_and_refresh()))
    
    refresh_account_buttons(canvas)

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
    show_message("Account Saved!", "#00FF00", canvas)
    
    hide_popup(canvas)
    refresh_account_buttons(canvas)

def load_accounts():
    """Loads accounts from the JSON file."""
    try:
        with open(DATA_FILE, "r") as file:
            data = json.load(file)
            accounts = data.get("accounts", [])
            return accounts
    except Exception as e:
        return []

def monitor_league_client():
    global lockfile_path, lockfile_found, league_client_status
    while True:
        league_running = any("LeagueClient" in proc.name() for proc in psutil.process_iter())
        if league_running and league_client_status == 0:
            league_client_status = 1

        if not league_running and league_client_status == 1:
            if lockfile_path and os.path.exists(lockfile_path):
                try:
                    os.remove(lockfile_path)
                except Exception as e:
                    pass
            lockfile_found = False
            league_client_status = 0  # Reset tripwire
            start_lockfile_monitor()
        time.sleep(2)

def display_account_buttons():
    global account_buttons
    accounts = load_accounts()

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

    image_image_1 = images["image_1.png"]
    canvas.create_image(0, -23, anchor="nw", image=image_image_1)

    image_image_2 = images["image_2.png"]
    canvas.create_image(484, 27, anchor="nw", image=image_image_2)

    canvas.create_text(506.0, 15.0, anchor="nw", text="FarSight", fill="#FFFFFF",
                   font=("Convergence Regular", 64 * -1))
    image_image_5 = images["image_5.png"]
    add_account_button = canvas.create_image(934, 597, image=image_image_5, anchor="nw")
    add_account_text = canvas.create_text(965.0, 605.0, anchor="nw", text="Add Account", fill="#FFFFFF",
                   font=("Convergence Regular", 40 * -1))

# Correctly bind to the canvas image item
    canvas.tag_bind(add_account_button, "<Button-1>", lambda event: show_popup(canvas))
    canvas.tag_bind(add_account_text, "<Button-1>", lambda event: show_popup(canvas))
    if not isinstance(accounts, list):

        accounts = []
    
    # Clear existing buttons before adding new ones
    for button in account_buttons:
        canvas.delete(button)
    account_buttons.clear()
    image_references.clear()  # Clear image references to avoid memory bloat

    num_accounts = min(len(accounts), MAX_BUTTONS)
    row = 0
    col = 0

    for i in range(num_accounts):
        account = accounts[i]
        account_name = account.get("account_name", "Unknown")
        stored_rank = account.get("rank", "").strip()

        x_position = BUTTON_START_X + (col * BUTTON_SPACING_X) + 190
        y_position = BUTTON_START_Y + (row * BUTTON_SPACING_Y)

        rank_tier = stored_rank.split()[0].lower() if stored_rank else "unranked"
        image_key = f'button_{rank_tier}' if f'button_{rank_tier}' in ranked_button_images else 'button_unranked'

        try:
            # Load the image using the embedded base64 data and store the reference
            button_image = PhotoImage(data=ranked_button_images[image_key])
            image_references.append(button_image)  # Prevent garbage collection
        except Exception as e:
            continue

        # Determine text color based on rank (black for specific ranks, white for others)
        if rank_tier in ["unranked", "silver", "gold", "diamond", "challenger"]:
            text_color = "#000000"
        else:
            text_color = "#FFFFFF"

        # Create the button with the correct rank image
        button = canvas.create_image(x_position, y_position, image=button_image)

        button_text = canvas.create_text(x_position, y_position, text=account_name,
                                         fill=text_color, font=("Convergence Regular", 24 * -1))

        rank_text = canvas.create_text(x_position, y_position + 30, text=stored_rank or "Unranked",
                                       fill=text_color, font=("Convergence Regular", 20 * -1))

        account_buttons.extend([button, button_text, rank_text])

        canvas.tag_bind(button, "<Button-1>", lambda event, acc=account: launch_game(acc))
        canvas.tag_bind(button_text, "<Button-1>", lambda event, acc=account: launch_game(acc))

        col += 1
        if col >= 3:
            col = 0
            row += 1

    if accounts:
        create_manage_accounts_button(canvas)

def create_manage_accounts_button(canvas):
    # Creates the 'Manage Accounts' button using the same image as 'Add Account'.
    if "manage_accounts" not in images:
        images["manage_accounts"] = images["image_5.png"]
    manage_button = canvas.create_image(110, 597, anchor="nw", image=images["manage_accounts"])
    manage_text = canvas.create_text(125, 610, anchor="nw", text="Manage Accounts", fill="#FFFFFF",
                                     font=("Convergence Regular", 34 * -1))
    canvas.tag_bind(manage_button, "<Button-1>", lambda event: show_manage_accounts_overlay())
    canvas.tag_bind(manage_text, "<Button-1>", lambda event: show_manage_accounts_overlay())

def show_manage_accounts_overlay():
    global manage_overlay, manage_frame  # Make both global to allow proper refreshing

    # Initialize if not already defined
    if manage_overlay is None:
        manage_overlay = tk.Frame(window, bg="#000000", width=window.winfo_width(), height=window.winfo_height())
        manage_overlay.place(x=0, y=0)
        
        manage_frame = tk.Frame(manage_overlay, bg="#2E2E2E", padx=20, pady=20)
        manage_frame.place(relx=0.5, rely=0.5, anchor="center")

    # Clear the manage frame before repopulating
    for widget in manage_frame.winfo_children():
        widget.destroy()

    title_label = tk.Label(manage_frame, text="Manage Accounts", font=("Convergence Regular", 16),
                           fg="white", bg="#2E2E2E")
    title_label.pack(pady=10)

    # Add a Close button to hide the overlay
    close_button = tk.Button(manage_frame, text="Close", font=("Convergence Regular", 12),
                             bg="#FF4C4C", fg="white", command=hide_manage_accounts_overlay)
    close_button.pack(pady=10)

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
                                      bg="#FF4C4C", fg="white", 
                                      command=lambda acc=account: delete_account(acc))
            delete_button.pack(side="right", padx=10)

def hide_manage_accounts_overlay():
    global manage_overlay, manage_frame
    if manage_overlay:
        manage_overlay.destroy()
        manage_overlay = None
        manage_frame = None
    refresh_account_buttons(canvas)

def delete_account(account):
    """Deletes the specified account from accounts.json and updates the UI."""
    accounts = load_accounts()
    updated_accounts = [acc for acc in accounts if acc.get("account_name") != account.get("account_name")]

    with open(DATA_FILE, "w") as file:
        json.dump({"accounts": updated_accounts}, file, indent=4)
    
    show_manage_accounts_overlay()

def start_lockfile_monitor(account):
    """Runs find_lockfile() only once and never restarts it."""
    global lockfile_found

    if not account:
        return

    if lockfile_found:
        return  # Prevents restarting

    thread = threading.Thread(target=find_lockfile, args=(account,), daemon=True)
    thread.start()

def launch_game(account):
    """Launches Riot Client and fetches rank after login."""
    riot_client_path = load_riot_client_path()
    
    username = decrypt_data(account.get("username", ""))
    password = decrypt_data(account.get("password", ""))

    accountname = account.get("account_name", "Unknown")

    if accountname == "Unknown":
        return

    subprocess.Popen([riot_client_path])
    time.sleep(5)  # Wait for Riot Client to load

    pyautogui.write(username)
    time.sleep(0.1)

    pyautogui.press("tab")
    time.sleep(0.1)

    pyautogui.write(password)
    time.sleep(0.1)

    pyautogui.press("enter")

    start_lockfile_monitor(account)

def find_lockfile(account):
    """Continuously searches for the League Client lockfile until it is found, then stops."""
    accountname = account.get("account_name", "Unknown")

    while True:  # Keep searching until lockfile is found
        for proc in psutil.process_iter(attrs=["pid", "name", "exe", "cwd"]):
            try:
                if "LeagueClient" in proc.info["name"]:
                    if proc.info["cwd"]:
                        lockfile_path = os.path.join(proc.info["cwd"], "lockfile")
                        if os.path.exists(lockfile_path):
                            lockfile_found = True  
                            threading.Thread(target=fetch_rank_info, args=(lockfile_path, account), daemon=True).start()
                            return  # Stop searching once the lockfile is found
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                continue

        time.sleep(1)

def parse_lockfile(lockfile_path):
    print('Parsing lockfile...')
    try:
        with open(lockfile_path, 'r') as lockfile:
            content = lockfile.read().strip().split(':')
            return {
                'port': content[2],
                'auth_token': content[3],
                'protocol': content[4]
            }
    except Exception as e:
        print(f'Error parsing lockfile: {e}')
        return None

def start_lockfile_monitor(account):
    """Runs find_lockfile() only once and never restarts it."""
    global lockfile_found

    if not account:
        return

    if lockfile_found:
        return  # Prevents restarting

    thread = threading.Thread(target=find_lockfile, args=(account,), daemon=True)
    thread.start()

def fetch_rank_info(lockfile_path, account):
    """Fetches Solo/Duo rank details with retry handling for HTTP 500 errors."""
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

        for attempt in range(5):
            response = http.request("GET", url, headers=headers)
            
            if response.status == 200:
                data = json.loads(response.data.decode("utf-8"))
                ranked_info = data.get("queues", [])

                for queue in ranked_info:
                    if queue["queueType"] == "RANKED_SOLO_5x5":
                        tier = queue.get("tier", "Unranked")
                        division = queue.get("division", "N/A")
                        league_points = queue.get("leaguePoints", 0)

                        rank_display = f"{tier} {division} - {league_points} LP"
                        update_account_rank(account['account_name'], rank_display)
                        return
                return
            
            elif response.status == 500:
                time.sleep(3)  # Wait before retrying
            
            else:
                return
        
        return None

    except Exception as e:
        return None

def update_account_rank(account_name, new_rank):
    """Updates the rank of the given account in accounts.json, adding the account if missing."""
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
        json.dump({"accounts": accounts}, file, indent=4)

    display_account_buttons()

def refresh_account_buttons(canvas):
    # Refreshes the account buttons after changes.
    account_buttons.clear()
    display_account_buttons()

def monitor_league_client():
    global lockfile_path, lockfile_found, league_client_status
    while True:
        league_running = any("LeagueClient" in proc.name() for proc in psutil.process_iter())
        if league_running and league_client_status == 0:
            league_client_status = 1

        if not league_running and league_client_status == 1:
            if lockfile_path and os.path.exists(lockfile_path):
                try:
                    os.remove(lockfile_path)
                except Exception as e:
                    pass
            lockfile_found = False
            league_client_status = 0  # Reset tripwire
            start_lockfile_monitor()
        time.sleep(2)

def fetch_latest_ddragon_version():
    version_url = "https://ddragon.leagueoflegends.com/api/versions.json"
    response = requests.get(version_url)
    if response.status_code == 200:
        versions = response.json()
        return versions[0]  # The latest version is the first in the list
    return "14.1.1"

def fetch_champion_icon(champion_name, version, size=(50, 50)):
    champion_name = champion_name.replace(" ", "")  # Ensure correct formatting
    icon_url = f"http://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{champion_name}.png"
    response = requests.get(icon_url)
    if response.status_code == 200:
        image_data = response.content
        image = Image.open(io.BytesIO(image_data))
        image = image.resize(size)  # Resize the image to fit inside the button
        return ImageTk.PhotoImage(image)
    return None

def load_icon_from_b64(b64_string, size=(100, 100)):
    """Convert a base64 string to a PhotoImage for Tkinter."""
    image_data = base64.b64decode(b64_string)
    image = Image.open(io.BytesIO(image_data))
    image = image.resize(size, Image.ANTIALIAS)
    return ImageTk.PhotoImage(image)

def display_profile_card(canvas, lockfile_path):
    global main_menu_images
    
    account_name = "Unknown Account"  # Default account name in case of an error
    
    try:
        with open(lockfile_path, 'r') as file:
            lockfile_data = file.read().strip().split(':')
            print(f"Lockfile Data: {lockfile_data}")  # Debug output
            
            if len(lockfile_data) < 5:
                print("Invalid lockfile format.")
                return
            
            port = lockfile_data[2]
            token = lockfile_data[3]
            url = f"https://127.0.0.1:{port}/lol-summoner/v1/current-summoner"
            headers = {
                "Authorization": f"Basic {base64.b64encode(f'riot:{token}'.encode()).decode()}"
            }
            
            print(f"Requesting account name from: {url}")  # Debug output
            response = requests.get(url, headers=headers, verify=False)
            print(f"Response Status Code: {response.status_code}")  # Debug output
            
            if response.status_code == 200:
                data = response.json()
                account_name = data.get('gameName', 'Unknown Account')
                print(f"Fetched Account Name: {account_name}")  # Debug output
            else:
                print(f"Failed to fetch account name: {response.status_code}")
    
    except Exception as e:
        print(f"Error reading lockfile: {e}")
    
    # Display the profile card image
    image_image_8 = main_menu_images['Image8.png']
    canvas.image = image_image_8  # Prevent garbage collection
    canvas.create_image(41, 100, anchor='nw', image=image_image_8)

    # Render the dynamic account name on the profile card
    canvas.create_text(
        62, 111, anchor='nw', 
        text=account_name, 
        fill="#FFFFFF", 
        font=("Convergence Regular", 38, "bold")
    )

    image_image_8_8 = main_menu_images['Image8-8.png']
    canvas.image = image_image_8_8
    canvas.create_image(41, 229, anchor = 'nw', image=image_image_8_8)
    
def fetch_champion_data():
    """
    Fetch champion data from Riot's Data Dragon API and build a mapping of champion ID to champion name.

    Returns:
        dict: Mapping of champion ID to champion name.
    """
    version_url = "https://ddragon.leagueoflegends.com/api/versions.json"
    response = requests.get(version_url)

    if response.status_code == 200:
        latest_version = response.json()[0]
        champion_data_url = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/champion.json"
        response = requests.get(champion_data_url)

        if response.status_code == 200:
            data = response.json()["data"]
            id_to_name = {
                details["key"]: details["id"] for details in data.values()
            }
            return id_to_name
        else:
            raise Exception(f"Error fetching champion data: {response.status_code}")
    else:
        raise Exception(f"Error fetching version data: {response.status_code}")
    
def launch_client_menu(account_name, lockfile_path):
    champid = fetch_champion_data()
    ddragon_version = fetch_latest_ddragon_version()

    print('Launching client menu...')  # Debug print
    for widget in window.winfo_children():
        widget.destroy()
    window.configure(bg='#4F4F4F')
    window.update()  # Force update

    canvas = tk.Canvas(window, bg='#4F4F4F', height=720, width=1280, bd=0, highlightthickness=0, relief='ridge')
    canvas.place(x=0, y=0)

    image_image_1 = main_menu_images['Image1.png']
    canvas.create_image(0, 0, anchor='nw', image=image_image_1)

    image_image_2 = main_menu_images['Image2.png']
    canvas.create_image(484, 27, anchor='nw', image=image_image_2)

    canvas.create_text(506.0, 15.0, anchor="nw", text="FarSight", fill="#FFFFFF", font=("Convergence Regular", 64 * -1))

    match_frame = tk.Frame(window, bg='#4F4F4F')
    match_frame.place(x=437, y=229, anchor='nw')

    scrollable_canvas = tk.Canvas(match_frame, bg='#4F4F4F', height=408, width=387, highlightthickness=0)
    
    scrollable_frame = tk.Frame(scrollable_canvas, bg='#4F4F4F')
    scrollable_canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')

    scrollable_frame.bind(
        '<Configure>',
        lambda e: scrollable_canvas.configure(
            scrollregion=scrollable_canvas.bbox('all')
        )
    )

    scrollable_canvas.bind_all('<MouseWheel>', lambda e: scrollable_canvas.yview_scroll(int(-1 * (e.delta / 120)), 'units'))

    match_data = fetch_match_data(lockfile_path)
    print(f"Fetched {len(match_data)} matches from the lockfile.")

    image_height = 102
    total_height = len(match_data) * image_height

    image_refs = []  # To hold image references
    
    recent_matches = match_data[:20]
    win_count = sum(1 for match in recent_matches if match.get('win', False))
    total_matches = len(recent_matches)
    winrate = (win_count / total_matches) * 100 if total_matches > 0 else 0

    win_rate_color = "#00FF00" if winrate >= 50 else "#FF0000"

    canvas.create_text(450, 160, anchor="nw", text=f"Last 20 |", fill="#FFFFFF", font=("Convergence Regular", 52 * -1))
    canvas.create_text(660, 160, anchor="nw", text=f"{winrate}%", fill=win_rate_color, font=("Convergence Regular", 52 * -1))

    for index, match in enumerate(match_data[:20]):
        win = match.get('win', False)
        champion = champid.get(match['champion'], "Unknown Champion")
        scoreline = match.get('scoreline', "0/0/0")

        match_image_path = main_menu_images['Image8-9.png'] if win else main_menu_images['Image8-10.png']
        match_image = match_image_path

        match_image_id = scrollable_canvas.create_image(
            0, index * image_height, anchor='nw', image=match_image, tags=f"match_button_{index}"
        )

        # Fetch and display the champion icon within the button
        icon = fetch_champion_icon(champion, ddragon_version, size=(50, 50))
        if icon:
            # Position the icon inside the button, aligned to the left
            scrollable_canvas.create_image(
                40, index * image_height + 42, anchor='center', image=icon
            )
            image_refs.append(icon)  # Keep reference to avoid garbage collection

        text_y_position = index * image_height + image_height // 2
        
        # Champion name positioned to the right of the icon
        scrollable_canvas.create_text(225, text_y_position - 10,  # Adjusted x position for icon
            text=f"{champion} | {scoreline}",
            fill="#FFFFFF",
            font=("Convergence Regular", 28, "bold"))
        
        # Scoreline positioned below the champion name

        scrollable_canvas.tag_bind(match_image_id, "<Button-1>", lambda event, url=match['stat_url']: webbrowser.open(url))

        image_refs.append(match_image)  # Store reference

    scrollable_canvas.image_refs = image_refs
    scrollable_frame.config(height=total_height)

    scrollable_canvas.pack(side='left', fill='both', expand=True)
    display_profile_card(canvas, lockfile_path)

def fetch_match_data(lockfile_path):
    print('Fetching match data from lockfile...')
    try:
        with open(lockfile_path, 'r') as lockfile:
            content = lockfile.read().strip().split(':')
            port, auth_token, protocol = content[2], content[3], content[4]

        headers = {
            'Authorization': f'Basic {base64.b64encode(f"riot:{auth_token}".encode()).decode()}',
            'Accept': 'application/json'
        }

        url = f'{protocol}://127.0.0.1:{port}/lol-match-history/v1/products/lol/current-summoner/matches'
        print(f'Requesting match history from: {url}')

        http = urllib3.PoolManager(cert_reqs='CERT_NONE')
        response = http.request('GET', url, headers=headers)

        if response.status == 200:
            data = json.loads(response.data.decode('utf-8'))
            matches = data.get('games', {}).get('games', [])
            
            # Debug: Print the number of matches retrieved
            print(f'Fetched {len(matches)} matches from the API.')

            # Parse match details including scoreline and champion ID
            match_data = []
            for match in matches:
                participant = match.get('participants', [{}])[0]
                win = participant.get('stats', {}).get('win', False)
                kills = participant.get('stats', {}).get('kills', 0)
                deaths = participant.get('stats', {}).get('deaths', 0)
                assists = participant.get('stats', {}).get('assists', 0)
                champion_id = participant.get('championId', 'Unknown')
                scoreline = f'{kills}/{deaths}/{assists}'
                match_data.append({
                    'scoreline': scoreline,
                    'champion': str(champion_id),
                    'win': win,
                    'stat_url': f'https://www.leagueofgraphs.com/match/na/{match.get("gameId")}'
                })
            
            
            return match_data[:20]  # Limit to the most recent 20 matches

        else:
            print(f'HTTP Error: {response.status}')
    except Exception as e:
        print(f'Error fetching match data: {e}')
    
    return []

def initialize_app(accounts):
    print('Initializing application...')  # Debug print
    
    global canvas, main_menu_opened
    
    # Clear all existing window elements
    for widget in window.winfo_children():
        widget.destroy()

    # Check for an active lockfile and open the client menu if found
    for account in accounts:
        account_name = account.get('account_name', 'Unknown')
        for proc in psutil.process_iter(attrs=['pid', 'name', 'exe', 'cwd']):
            try:
                if 'LeagueClient' in proc.info['name'] and proc.info['cwd']:
                    lockfile_path = os.path.join(proc.info['cwd'], 'lockfile')
                    if os.path.exists(lockfile_path):
                        print('Lockfile found on startup!')
                        
                        # Clear all widgets and launch the main menu
                        for widget in window.winfo_children():
                            widget.destroy()
                        
                        launch_client_menu(account_name, lockfile_path)
                        main_menu_opened = True
                        return  # Stop execution to avoid loading the account window
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                print(f'Error accessing process: {e}')
                continue

    # Display the account window if no lockfile is found
    print('No lockfile found, displaying account window.')
    display_account_buttons()

# Start the application
accounts = [{'account_name': 'TestAccount'}]  # Replace with actual account loading logic
initialize_app(accounts)

on_app_start()
check_riot_client_path()

window.resizable(False, False)
window.mainloop()

