from pathlib import Path
from tkinter import Tk, Canvas, Entry, PhotoImage
from cryptography.fernet import Fernet
import tkinter as tk
from tkinter import Menu
from tkinter import messagebox
import json
import os
import psutil
import subprocess
import pyautogui
import time
import requests
import base64
import pygetwindow as gw
import win32gui
import win32con
import pywinauto
import threading
import ssl
import certifi
import urllib3
import urllib.request

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path(r"D:\Coding Projects\build\assets\frame0")
APP_FOLDER = os.path.join(os.path.expanduser("~"), "Documents", "FarSight")
KEY_FILE = os.path.join(APP_FOLDER, "secret.key")
DATA_FILE = os.path.join(APP_FOLDER, "accounts.json")
CONFIG_FILE = os.path.join(APP_FOLDER, "config.json")
RIOT_CERT_PATH = os.path.join(APP_FOLDER, "riotgames.pem")
delete_buttons = []  # Store delete buttons separately to avoid missing references
PEM_URL = "https://static.developer.riotgames.com/docs/lol/riotgames.pem"
PEM_PATH = os.path.join(APP_FOLDER, "riotgames.pem")
lockfile_found = False

BUTTON_START_X = 82
BUTTON_START_Y = 185
BUTTON_SPACING_X = 357  # Distance between buttons left to right
BUTTON_SPACING_Y = 120  # Distance between buttons top to bottom
MAX_BUTTONS = 12  # 3x3 layout
account_buttons = []  # List to store dynamically created account buttons

def ensure_app_folder():
    """Ensures APP_FOLDER exists and downloads riotgames.pem if missing."""
    try:
        if not os.path.exists(APP_FOLDER):
            os.makedirs(APP_FOLDER, exist_ok=True)
            print(f"Created APP_FOLDER at {APP_FOLDER}")
        download_riot_pem()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to create app folder: {e}")

def download_riot_pem():
    """Downloads the Riot Games PEM file if it does not exist."""
    try:
        if os.path.exists(PEM_PATH):
            print("riotgames.pem already exists, skipping download.")
            messagebox.showinfo("Info", "riotgames.pem is already installed.")
            return
        
        print("Downloading riotgames.pem...")

        # Force the download using urllib.request
        with urllib.request.urlopen(PEM_URL) as response:
            data = response.read()
            with open(PEM_PATH, "wb") as pem_file:
                pem_file.write(data)
        
        print(f"Successfully downloaded riotgames.pem to {PEM_PATH}")
        messagebox.showinfo("Success", f"Successfully downloaded riotgames.pem to:\n{PEM_PATH}")

    except urllib.error.URLError as e:
        messagebox.showerror("Download Error", f"Failed to download riotgames.pem:\n{e.reason}")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")

def on_app_start():
    """Run this when the Tkinter app starts"""
    ensure_app_folder()  # Ensure folder and PEM file exist

def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)

# Initialize Tkinter Window
window = Tk()
window.geometry("1280x720")
window.configure(bg="#4F4F4F")

http = urllib3.PoolManager(
    cert_reqs="CERT_REQUIRED",
    ca_certs=RIOT_CERT_PATH  # Use Riot's self-signed certificate for SSL verification
)

def check_riot_client_path():
    """Ensures Riot Client path is set. If missing, display input overlay."""
    riot_client_path = load_riot_client_path()

    if not riot_client_path:  # ✅ If no path is found, show the overlay
        print("[INFO] No Riot Client path found. Displaying input overlay.")
        show_riot_path_overlay()  
 # ✅ Show the overlay if the path is missing

def show_riot_path_overlay():
    """Displays an overlay in the main application window for entering the Riot Client path."""
    global riot_path_entry, riot_overlay

    riot_overlay = tk.Frame(window, bg="#000000", width=1280, height=720)  # ✅ Full-screen overlay
    riot_overlay.place(x=0, y=0)

    input_frame = tk.Frame(riot_overlay, bg="#2E2E2E", padx=20, pady=20)
    input_frame.place(relx=0.5, rely=0.5, anchor="center")  # ✅ Centered

    label = tk.Label(input_frame, text="Enter Riot Client Path:", font=("Convergence Regular", 14), fg="white", bg="#2E2E2E")
    label.pack(pady=10)

    riot_path_entry = tk.Entry(input_frame, width=40, font=("Convergence Regular", 16))
    riot_path_entry.pack(pady=5)
    riot_path_entry.focus_set()  # ✅ Auto-focus on input field

    save_button = tk.Button(input_frame, text="Save", command=lambda: save_riot_path_and_close())
    save_button.pack(pady=10)

    print("[INFO] Riot Client path overlay displayed.")

def save_riot_path_and_close():
    """Saves the Riot Client path and removes the overlay."""
    path = riot_path_entry.get()
    if not path.strip():
        print("[ERROR] No path entered. Please enter a valid path.")
        return  # ✅ Prevent closing without entering a valid path

    save_riot_client_path(path)  # ✅ Save the path
    riot_overlay.destroy()  # ✅ Remove the overlay after saving
    print("[INFO] Riot Client path saved and overlay removed.")

def save_riot_client_path(path):
    """Saves Riot Client path to config.json."""
    if not path:
        print("[ERROR] No path provided. Riot Client path not saved.")
        return

    config_data = {"riot_client_path": path}

    with open(CONFIG_FILE, "w") as file:
        json.dump(config_data, file, indent=4)

    print(f"[INFO] Riot Client path saved: {path}")

def load_riot_client_path():

    if not os.path.exists(CONFIG_FILE):
        print(f"[WARNING] No config.json found in {CONFIG_FILE}. Creating a new one.")
        save_riot_client_path("")  # ✅ Creates config.json but leaves it empty
        return None

    with open(CONFIG_FILE, "r") as file:
        try:
            data = json.load(file)
            return data.get("riot_client_path", None)  # ✅ Return path or None
        except json.JSONDecodeError:
            print("[ERROR] Failed to parse config.json")
            return None

import threading
import time

def find_lockfile(account_name):
    """Continuously searches for the League Client lockfile until it is found, then stops."""
    global lockfile_found

    print("[DEBUG] Lockfile monitoring started...")

    while True:  # ✅ Keep searching until lockfile is found
        for proc in psutil.process_iter(attrs=["pid", "name", "exe", "cwd"]):
            try:
                if "LeagueClient" in proc.info["name"]:
                    if proc.info["cwd"]:
                        lockfile_path = os.path.join(proc.info["cwd"], "lockfile")

                        if os.path.exists(lockfile_path):
                            print(f"[INFO] Lockfile detected at: {lockfile_path}")
                            lockfile_found = True  

                            # ✅ Start fetch_rank_info() with the correct `account_name`
                            threading.Thread(target=fetch_rank_info, args=(lockfile_path, account_name), daemon=True).start()

                            return  # ✅ Stop searching once the lockfile is found
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        time.sleep(1)  # ✅ Wait 1 second before checking again (prevents CPU overuse)


# Dictionary to store preloaded images
images = {}

def preload_assets():
    """Automatically loads all image assets into a dictionary."""
    global images
    images = {}

    # List of all image filenames (Make sure these match your actual file names)
    asset_files = [
        f"image_{i}.png" for i in range(1, 15)  # Adjust the range based on the number of images
    ]

    # Load each image dynamically
    for asset in asset_files:
        images[asset] = PhotoImage(file=relative_to_assets(asset))

# Call this function **once** at startup
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

canvas.place(x = 0, y = 0)

image_image_1 = PhotoImage( #top blue bar
    file=relative_to_assets("image_1.png"))
image_1 = canvas.create_image(0, -23, anchor="nw", image=image_image_1)

image_image_2 = PhotoImage( #blue title square
    file=relative_to_assets("image_2.png"))
image_2 = canvas.create_image(484, 27, anchor="nw", image=image_image_2)

image_image_2 = PhotoImage( #blue title square
    file=relative_to_assets("image_2.png"))
image_2 = canvas.create_image(484, 27, anchor="nw", image=image_image_2)

canvas.create_text(506.0,15.0,anchor="nw",text="FarSight",fill="#FFFFFF", #FarSight Label
font=("Convergence Regular", 64 * -1)
)

def hide_popup():
    global popup_elements

    for element in popup_elements:
        try:
            # If the element is a canvas item (text/image), delete it
            if isinstance(element, int):
                canvas.delete(element)
            # If the element is an Entry widget, destroy it
            else:
                element.destroy()
        except Exception as e:
            print(f"Error removing element: {e}")  # Debugging log

    popup_elements = []  # Clear the list to avoid issues with future popups



def show_popup():
    """Creates and displays the 'New Account' popup dynamically."""
    global popup_elements, images, account_name_entry, username_entry, password_entry
    popup_elements = [] 

    image_7 = canvas.create_image(0, 0, anchor = "nw", image=images["image_7.png"])  #Opaque BG
    popup_elements.append(image_7)

    image_8 = canvas.create_image(439, 148, anchor = "nw", image=images["image_8.png"])  #PopUp BG
    popup_elements.append(image_8)

    image_9 = canvas.create_image(490, 275, anchor = "nw", image=images["image_9.png"])  #
    popup_elements.append(image_9)

    image_10 = canvas.create_image(459, 165, anchor = "nw", image=images["image_10.png"])  #
    popup_elements.append(image_10)

    image_11 = canvas.create_image(490, 376, anchor = "nw", image=images["image_11.png"])  #
    popup_elements.append(image_11)

    image_12 = canvas.create_image(490, 477, anchor = "nw", image=images["image_12.png"])  #
    popup_elements.append(image_12)

    cancel_button=image_13 = canvas.create_image(629, 547, anchor = "nw", image=images["image_13.png"])  #
    popup_elements.append(cancel_button)

    save_button=image_14 = canvas.create_image(490, 547, anchor = "nw", image=images["image_14.png"])  
    popup_elements.append(save_button)

    newaccount_text=canvas.create_text(482.0,170.0,anchor="nw",text="New Account",fill="#FFFFFF",font=("Convergence Regular", 48 * -1))
    popup_elements.append(newaccount_text)
    accountname_text=canvas.create_text(514.0,237.0,anchor="nw",text="Account Name",fill="#FFFFFF",font=("Convergence Regular", 32 * -1))
    popup_elements.append(accountname_text)
    un_text=canvas.create_text(549,338,anchor="nw",text="Username",fill="#FFFFFF",font=("Convergence Regular", 32 * -1))
    popup_elements.append(un_text)
    pw_text=canvas.create_text(549,439,anchor="nw",text="Password",fill="#FFFFFF",font=("Convergence Regular", 32 * -1))
    popup_elements.append(pw_text)
    save_text=canvas.create_text(520.0,553.0,anchor="nw",text="Save",fill="#000000",font=("Convergence Regular", 32 * -1))
    popup_elements.append(save_text)
    cancel_text=canvas.create_text(643.0,553.0,anchor="nw",text="Cancel",fill="#000000",font=("Convergence Regular", 32 * -1))
    popup_elements.append(cancel_text)

    ##Account Info Entry

    account_name_entry = Entry(window, font=("Convergence Regular", 20))
    account_name_entry.place(x=514, y=281, width=223, height=38)
    popup_elements.append(account_name_entry)

    username_entry = Entry(window, font=("Convergence Regular", 20))
    username_entry.place(x=514, y=382, width=223, height=38)
    popup_elements.append(username_entry)

    password_entry = Entry(window, font=("Convergence Regular", 20))
    password_entry.place(x=514, y=483, width=223, height=38)
    popup_elements.append(password_entry)
    
    # Save Account Button
    canvas.tag_bind(save_button, "<Button-1>", lambda event: save_account())
    canvas.tag_bind(save_text, "<Button-1>", lambda event: save_account())

    #Cancel Add button
    canvas.tag_bind(cancel_button, "<Button-1>", lambda event: hide_popup())
    canvas.tag_bind(cancel_text, "<Button-1>", lambda event: hide_popup())

image_image_5 = PhotoImage(file=relative_to_assets("image_5.png")) #Add Account Button
image_5 = canvas.create_image(934,597,image=image_image_5,anchor="nw")

add_account_text=canvas.create_text(965.0,605.0,anchor="nw",text="Add Account",fill="#FFFFFF", #Add Account Text
    font=("Convergence Regular", 40 * -1)
)

def close_popup_and_refresh():
    """Closes the popup and refreshes account buttons after success message disappears."""
    hide_popup()  # Close popup
    refresh_account_buttons()  # Refresh account buttons

def show_message(text, color, delay=0):
    """Displays a temporary success or error message, with an optional delay before UI actions."""
    message_text = canvas.create_text(640, 620, text=text,
                                      fill=color, font=("Convergence Regular", 24 * -1))
    popup_elements.append(message_text)  # Store message so it can be removed later

    if delay > 0:
        # After delay, delete message and refresh UI
        window.after(delay, lambda: (canvas.delete(message_text), close_popup_and_refresh()))

##Account Security

def generate_key():
    """Generates an encryption key if it doesn't exist."""
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
        print("Encryption key generated successfully!")
    else:
        print("Encryption key already exists.")

# Load the encryption key
def load_key():
    """Loads the encryption key from the file, generating it if missing."""
    generate_key()  # Ensure the key file exists
    with open(KEY_FILE, "rb") as key_file:
        return key_file.read()

# Encrypt data
def encrypt_data(data):
    cipher = Fernet(load_key())
    return cipher.encrypt(data.encode()).decode()

# Decrypt data
def decrypt_data(data):
    cipher = Fernet(load_key())
    return cipher.decrypt(data.encode()).decode()

# Save account details securely
def save_account():
    """Encrypt and store the account details securely in a specific folder, ensuring correct JSON format."""
    global account_name_entry, username_entry, password_entry

    account_name = account_name_entry.get().strip()
    username = username_entry.get().strip()
    password = password_entry.get().strip()

    # Validate input fields
    missing_fields = []
    if not account_name:
        missing_fields.append("Account Name")
    if not username:
        missing_fields.append("Username")
    if not password:
        missing_fields.append("Password")

    if missing_fields:
        error_message = f"Missing: {', '.join(missing_fields)}"
        show_message(error_message, "#FF0000")  # Show error in red
        return

    encrypted_username = encrypt_data(username)
    encrypted_password = encrypt_data(password)

    if encrypted_username is None or encrypted_password is None:
        print("[ERROR] Encryption failed. Account not saved.")
        return

    encrypted_data = {
        "account_name": account_name,
        "username": encrypted_username,
        "password": encrypted_password
    }

    # Load existing data or create new
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            try:
                data = json.load(file)
                if isinstance(data, dict):  # If JSON is a dictionary, extract the account list
                    accounts = data.get("accounts", [])
                elif isinstance(data, list):  # If JSON is already a list, use it
                    accounts = data
                else:
                    print("[ERROR] Invalid JSON format. Resetting accounts.")
                    accounts = []
            except json.JSONDecodeError:
                print("[ERROR] Failed to parse accounts.json. Resetting accounts.")
                accounts = []
    else:
        accounts = []

    # Ensure `accounts` is a list before appending
    if not isinstance(accounts, list):
        accounts = []

    # Append the new account
    accounts.append(encrypted_data)

    # Save back to the file in the correct format
    with open(DATA_FILE, "w") as file:
        json.dump({"accounts": accounts}, file, indent=4)

    print(f"[INFO] Account '{account_name}' saved successfully.")

    # Show success message
    show_message("Account Saved!", "#00FF00")

    # Refresh UI to show new account
    refresh_account_buttons()

    # Hide the popup after refresh
    hide_popup()

def load_accounts():
    """Loads accounts from accounts.json."""
    if not os.path.exists(DATA_FILE):
        print("[WARNING] No accounts.json found. Returning empty list.")
        return []

    with open(DATA_FILE, "r") as file:
        try:
            data = json.load(file)
            if isinstance(data, dict) and "accounts" in data:
                return data["accounts"]  # ✅ Now correctly accessing the account list
            elif isinstance(data, list):
                return data  # ✅ Handle old JSON format with just a list
            else:
                print("[ERROR] Invalid accounts.json format. Resetting.")
                return []
        except json.JSONDecodeError:
            print("[ERROR] Failed to parse accounts.json")
            return []

def display_account_buttons():
    """Creates buttons for saved accounts and displays their rank."""
    global images, account_buttons
    accounts = load_accounts()

    if not isinstance(accounts, list):
        print("[ERROR] Accounts data is not a list. Resetting to empty.")
        accounts = []

    print(f"[DEBUG] Loading {len(accounts)} accounts.")

    if "button_bg" not in images:
        images["button_bg"] = PhotoImage(file=relative_to_assets("image_6.png"))

    num_accounts = min(len(accounts), MAX_BUTTONS)
    row = 0
    col = 0

    for i in range(num_accounts):
        try:
            account = accounts[i]
            account_name = account.get("account_name", "Unknown")
            
            # ✅ Load stored rank information from accounts.json
            stored_rank = account.get("rank", "Fetching...")  

            # ✅ Calculate X and Y based on grid position
            x_position = BUTTON_START_X + (col * BUTTON_SPACING_X) + 190
            y_position = BUTTON_START_Y + (row * BUTTON_SPACING_Y)

            # ✅ Create button with image background
            button = canvas.create_image(x_position, y_position, image=images["button_bg"])
            button_text = canvas.create_text(x_position, y_position, text=account_name,
                                             fill="#FFFFFF", font=("Convergence Regular", 24 * -1))

            # ✅ Add rank below the account name
            rank_text = canvas.create_text(x_position, y_position + 30, text=stored_rank,
                                           fill="#AAAAAA", font=("Convergence Regular", 20 * -1))

            # ✅ Store button references correctly
            account_buttons.append(button)
            account_buttons.append(button_text)  # Account name
            account_buttons.append(rank_text)  # Account rank

            # ✅ Bind button click to launching Riot Client
            canvas.tag_bind(button, "<Button-1>", lambda event, acc=account: launch_game(acc))
            canvas.tag_bind(button_text, "<Button-1>", lambda event, acc=account: launch_game(acc))

            # ✅ Move to next column, reset row if needed
            col += 1
            if col == 3:
                col = 0
                row += 1

        except IndexError:
            print(f"[ERROR] Account index {i} is out of range.")
            break


    manage_button = canvas.create_image(82,597, anchor = "nw", image=images["image_5.png"])
    manage_text = canvas.create_text(110, 605, anchor="nw", text="Management", fill="#FFFFFF", font=("Convergence Regular", 40 * -1))
    canvas.tag_bind(manage_button, "<Button-1>", lambda event: open_manage_accounts_window())
    canvas.tag_bind(manage_text, "<Button-1>", lambda event: open_manage_accounts_window())

    print("[INFO] Manage Accounts button created using `image_5` and positioned opposite Add Account button.")


def open_manage_accounts_window():
    """Opens a popup window listing all saved accounts with delete buttons."""
    global account_buttons

    manage_window = tk.Toplevel(window)
    manage_window.title("Manage Accounts")
    manage_window.geometry("400x400")  # Adjust size as needed
    manage_window.configure(bg="#2E2E2E")  # Dark theme (optional)

    label = tk.Label(manage_window, text="Saved Accounts", font=("Convergence Regular", 16), fg="white", bg="#2E2E2E")
    label.pack(pady=10)

    accounts = load_accounts()

    if not accounts:
        tk.Label(manage_window, text="No accounts saved.", font=("Convergence Regular", 12), fg="white", bg="#2E2E2E").pack()
        return

    for account in accounts:
        frame = tk.Frame(manage_window, bg="#3E3E3E")
        frame.pack(fill="x", pady=5, padx=10)

        acc_label = tk.Label(frame, text=account["account_name"], font=("Convergence Regular", 14), fg="white", bg="#3E3E3E")
        acc_label.pack(side="left", padx=10, pady=5)

        del_button = tk.Button(frame, text="Delete", fg="red", bg="#5E5E5E",
                               command=lambda acc=account["account_name"]: delete_account(acc, manage_window))
        del_button.pack(side="right", padx=10)

    print("[INFO] Manage Accounts window opened.")

def delete_account(account_name):
    """Deletes an account and refreshes the Manage Accounts overlay."""
    if not os.path.exists(DATA_FILE):
        print("[ERROR] No accounts.json found.")
        return

    with open(DATA_FILE, "r") as file:
        try:
            data = json.load(file)
            # Expecting data to be a dict with an "accounts" key
            accounts = data.get("accounts", [])
        except json.JSONDecodeError:
            print("[ERROR] Failed to read accounts.json")
            return

    updated_accounts = [acc for acc in accounts if acc.get("account_name") != account_name]

    if len(updated_accounts) == len(accounts):
        print(f"[WARNING] Account '{account_name}' not found.")
        return

    # Save updated accounts back to accounts.json, preserving the structure
    new_data = {"accounts": updated_accounts}
    with open(DATA_FILE, "w") as file:
        json.dump(new_data, file, indent=4)

    print(f"[INFO] Deleted account: {account_name}")

    # Refresh the Manage Accounts overlay:
    refresh_account_buttons()
    hide_manage_accounts_overlay()
    show_manage_accounts_overlay()


def refresh_account_buttons():
    global account_buttons
    # Loop through each entry in account_buttons
    for btn_set in account_buttons:
        # If btn_set is iterable (e.g. a tuple or list), delete each item
        if isinstance(btn_set, (list, tuple)):
            for item in btn_set:
                canvas.delete(item)
        else:
            # Otherwise, delete the item directly (assuming it's a single canvas item ID)
            canvas.delete(btn_set)
    account_buttons.clear()
    display_account_buttons()



# ✅ Define `launch_game()` first
def launch_game(account):
    """Launches Riot Client and fetches rank after login."""
    riot_client_path = load_riot_client_path()
    
    username = decrypt_data(account["username"])
    password = decrypt_data(account["password"])

    print(f"[INFO] Launching Riot Client for: {account['account_name']}")

    # ✅ Start Riot Client
    subprocess.Popen([riot_client_path])
    time.sleep(5)  # Wait for Riot Client to load

    # ✅ Type username
    pyautogui.write(username)
    time.sleep(0.1)

    # ✅ Tab to password field
    pyautogui.press("tab")
    time.sleep(0.1)

    # ✅ Type password
    pyautogui.write(password)
    time.sleep(0.1)

    # ✅ Press Enter to log in
    pyautogui.press("enter")

    print("[INFO] Login process completed.")

    # ✅ Start lockfile monitoring in a separate thread
    threading.Thread(target=find_lockfile, args=(account["account_name"],), daemon=True).start()

# ✅ Now call `display_account_buttons()`
def display_account_buttons():
    """Creates buttons for saved accounts and displays their rank."""
    global images, account_buttons
    accounts = load_accounts()

    if not isinstance(accounts, list):
        print("[ERROR] Accounts data is not a list. Resetting to empty.")
        accounts = []

    print(f"[DEBUG] Loading {len(accounts)} accounts.")

    if "button_bg" not in images:
        images["button_bg"] = PhotoImage(file=relative_to_assets("image_6.png"))

    num_accounts = min(len(accounts), MAX_BUTTONS)
    row = 0
    col = 0

    for i in range(num_accounts):
        try:
            account = accounts[i]
            account_name = account.get("account_name", "Unknown")

            # ✅ Set blank rank instead of "Fetching..."
            stored_rank = account.get("rank", "")

            x_position = BUTTON_START_X + (col * BUTTON_SPACING_X) + 190
            y_position = BUTTON_START_Y + (row * BUTTON_SPACING_Y)

            button = canvas.create_image(x_position, y_position, image=images["button_bg"])
            button_text = canvas.create_text(x_position, y_position, text=account_name,
                                             fill="#FFFFFF", font=("Convergence Regular", 24 * -1))

            rank_text = canvas.create_text(x_position, y_position + 30, text=stored_rank,
                                           fill="#AAAAAA", font=("Convergence Regular", 20 * -1))

            account_buttons.append(button)
            account_buttons.append(button_text)  
            account_buttons.append(rank_text)  

            # ✅ Bind button click to launching Riot Client
            canvas.tag_bind(button, "<Button-1>", lambda event, acc=account: launch_game(acc))
            canvas.tag_bind(button_text, "<Button-1>", lambda event, acc=account: launch_game(acc))

            col += 1
            if col == 3:
                col = 0
                row += 1

        except IndexError:
            print(f"[ERROR] Account index {i} is out of range.")
            break

def create_manage_accounts_button():
    """Creates the 'Manage Accounts' button using the same image as 'Add Account'."""
    global images

    if "manage_accounts" not in images:
        images["manage_accounts"] = PhotoImage(file=relative_to_assets("image_5.png"))  # ✅ Uses same image

    # ✅ Position: Opposite the 'Add Account' button
    manage_button = canvas.create_image(110, 597, anchor = "nw", image=images["manage_accounts"])  # Adjust X,Y as needed
    manage_text = canvas.create_text(125, 610, anchor = "nw", text="Manage Accounts", fill="#FFFFFF", font=("Convergence Regular", 34 * -1))

    # ✅ Bind click event to open manage accounts overlay
    canvas.tag_bind(manage_button, "<Button-1>", lambda event: show_manage_accounts_overlay())
    canvas.tag_bind(manage_text, "<Button-1>", lambda event: show_manage_accounts_overlay())

    return manage_button, manage_text

# ✅ Call this function inside your UI setup to display the button
create_manage_accounts_button()

def show_manage_accounts_overlay():
    """Displays an overlay in the main window listing all saved accounts with a delete button for each."""
    global manage_overlay

    # Create an overlay frame covering the entire main window.
    manage_overlay = tk.Frame(window, bg="#000000", width=window.winfo_width(), height=window.winfo_height())
    manage_overlay.place(x=0, y=0)

    # Create a centered frame for the management UI.
    manage_frame = tk.Frame(manage_overlay, bg="#2E2E2E", padx=20, pady=20)
    manage_frame.place(relx=0.5, rely=0.5, anchor="center")

    title_label = tk.Label(manage_frame, text="Manage Accounts", font=("Convergence Regular", 16),
                            fg="white", bg="#2E2E2E")
    title_label.pack(pady=10)

    # Load accounts from accounts.json
    accounts = load_accounts()

    if not accounts:
        tk.Label(manage_frame, text="No accounts saved.", font=("Convergence Regular", 12),
                 fg="white", bg="#2E2E2E").pack(pady=5)
    else:
        # For each account, create a row with the account name and a delete button.
        for account in accounts:
            account_name = account.get("account_name", "Unknown")
            row_frame = tk.Frame(manage_frame, bg="#3E3E3E")
            row_frame.pack(fill="x", pady=5, padx=10)

            name_label = tk.Label(row_frame, text=account_name, font=("Convergence Regular", 14),
                                  fg="white", bg="#3E3E3E")
            name_label.pack(side="left", padx=10)

            delete_button = tk.Button(row_frame, text="Delete", fg="red", bg="#5E5E5E",
                                      command=lambda name=account_name: delete_account(name))
            delete_button.pack(side="right", padx=10)

    # Add a Close button to dismiss the overlay.
    close_button = tk.Button(manage_frame, text="Close", command=hide_manage_accounts_overlay)
    close_button.pack(pady=10)

    print("[INFO] Manage Accounts overlay displayed.")

def hide_manage_accounts_overlay():
    """Closes the Manage Accounts overlay."""
    global manage_overlay
    if manage_overlay:
        manage_overlay.destroy()
        manage_overlay = None
        print("[INFO] Manage Accounts overlay closed.")

def fetch_rank_info(lockfile_path, account_name):
    """Fetches Solo/Duo rank details with retry handling for HTTP 500 errors."""
    try:
        if not lockfile_path or not os.path.exists(lockfile_path):
            print("[ERROR] Lockfile not found. Cannot fetch rank.")
            return

        # ✅ Read lockfile
        with open(lockfile_path, "r") as lockfile:
            content = lockfile.read().strip().split(":")
            port, auth_token, protocol = content[2], content[3], content[4]

        headers = {
            "Authorization": f"Basic {base64.b64encode(f'riot:{auth_token}'.encode()).decode()}",
            "Accept": "application/json"
        }

        url = f"{protocol}://127.0.0.1:{port}/lol-ranked/v1/current-ranked-stats"

        # ✅ Retry loop (max 5 attempts)
        for attempt in range(5):
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
                        print(f"[INFO] Rank Info for {account_name}: {new_rank}")

                        # ✅ Update accounts.json
                        update_account_rank(account_name, new_rank)

                        return new_rank
            
            elif response.status == 500:
                print(f"[WARNING] HTTP 500 error (attempt {attempt+1}/5). Retrying in 3 seconds...")
                time.sleep(3)  # Wait before retrying
            
            else:
                print(f"[ERROR] Failed to fetch rank data. HTTP {response.status}")
                return None
        
        print("[ERROR] Maximum retries reached. Could not fetch rank.")
        return None

    except Exception as e:
        print(f"[ERROR] Exception while fetching rank: {e}")
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
        print(f"[INFO] Adding new account entry: {account_name}")
        accounts.append({"account_name": account_name, "rank": new_rank})

    with open(DATA_FILE, "w") as file:
        json.dump(accounts, file, indent=4)

    print(f"[INFO] Updated rank for {account_name} in accounts.json.")

    # ✅ Refresh UI
    display_account_buttons()


def start_lockfile_monitor():
    """Runs find_lockfile() only once and never restarts it."""
    global lockfile_found

    if lockfile_found:
        print("[INFO] Lockfile already found, stopping monitor.")
        return  # ✅ Prevents restarting

    thread = threading.Thread(target=find_lockfile, daemon=True)
    thread.start()
    print("[DEBUG] Lockfile monitor started once.")

on_app_start()

check_riot_client_path()
display_account_buttons()

# ✅ Start lockfile monitor AFTER UI loads
start_lockfile_monitor()

print("[DEBUG] Main application started successfully.")  # ✅ Confirm program starts


# Add Account PopUp Button
canvas.tag_bind(image_5, "<Button-1>", lambda event: show_popup())
canvas.tag_bind(add_account_text, "<Button-1>", lambda event: show_popup())

window.resizable(False, False)
window.mainloop()
