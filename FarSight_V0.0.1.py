import random
import requests
import base64
import os
import urllib3
import psutil
import time
import tkinter as tk
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

RIOT_API_KEY = "" 
region = "na1"

# Lockfile functions
def find_lockfile():
    for proc in psutil.process_iter(attrs=["pid", "name", "exe", "cwd"]):
        try:
            if "LeagueClient" in proc.info["name"]:
                lockfile_path = os.path.join(proc.info["cwd"], "lockfile")
                if os.path.exists(lockfile_path):
                    return lockfile_path
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return None

def get_lockfile_info():
    lockfile_path = find_lockfile()
    if lockfile_path is None:
        raise FileNotFoundError("Lockfile not found. Ensure the League Client is running.")
    with open(lockfile_path, "r") as lockfile:
        content = lockfile.read().strip().split(":")
        return {
            "port": content[2],
            "auth_token": content[3],
            "protocol": content[4],
        }

# API functions
def get_summoner_info():
    lockfile = get_lockfile_info()
    url = f"https://127.0.0.1:{lockfile['port']}/lol-summoner/v1/current-summoner"
    auth_token = base64.b64encode(f"riot:{lockfile['auth_token']}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_token}",
        "Accept": "application/json",
    }
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error {response.status_code}: {response.text}")

def check_queue_status():
    lockfile = get_lockfile_info()
    auth_token = base64.b64encode(f"riot:{lockfile['auth_token']}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_token}",
        "Accept": "application/json",
    }

    ready_check_url = f"https://127.0.0.1:{lockfile['port']}/lol-matchmaking/v1/ready-check"
    response = requests.get(ready_check_url, headers=headers, verify=False)
    if response.status_code == 200:
        return "In Queue"

    matchmaking_url = f"https://127.0.0.1:{lockfile['port']}/lol-matchmaking/v1/search"
    response = requests.get(matchmaking_url, headers=headers, verify=False)
    if response.status_code == 200:
        return "In Queue"

    lobby_url = f"https://127.0.0.1:{lockfile['port']}/lol-lobby/v2/lobby"
    response = requests.get(lobby_url, headers=headers, verify=False)
    if response.status_code == 200:
        return "In Lobby"

    if response.status_code == 404:
        return "In Menu"

    raise Exception(f"Error {response.status_code}: {response.text}")

# GUI function
def create_window():
    def update_status():
        try:
            status = check_queue_status()
            status_label.config(text=f"{status}")
            root.after(2000, update_status)
        except Exception as e:
            status_label.config(text=f"Error: {e}")

    summoner_info = get_summoner_info()
    game_name = summoner_info.get("gameName", "Unknown")
    summoner_level = summoner_info.get("summonerLevel", "Unknown")

    root = tk.Tk()
    root.title(f"FarSight")
    root.geometry("400x200")

    tk.Label(root, text=f"Summoner: {game_name}", font=("Arial", 14)).pack(pady=10)
    tk.Label(root, text=f"Level: {summoner_level}", font=("Arial", 12)).pack(pady=5)

    status_label = tk.Label(root, text="Status: Checking...", font=("Arial", 12))
    status_label.pack(pady=10)

    update_status()

    root.mainloop()

if __name__ == "__main__":
    create_window()
