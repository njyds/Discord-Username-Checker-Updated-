# Discord Username Checker - Faster Version (Threaded) 2026
# Original: suenerve | Updated by Grok

import random
import string
import requests
import os
import time
import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, init
from configparser import ConfigParser
from queue import Queue

init(autoreset=True)

__version__ = "DSV 2.1 Fast (Threaded - June 2026)"

dir_path = os.path.dirname(os.path.realpath(__file__))
configur = ConfigParser()
config_file = os.path.join(dir_path, "config.ini")
configur.read(config_file)

tokens_path = os.path.join(dir_path, "tokens.txt")
proxies_path = os.path.join(dir_path, "proxies.txt")
av_list = os.path.join(dir_path, "available_usernames.txt")
username_list = os.path.join(dir_path, "usernames.txt")

# Global locks
print_lock = threading.Lock()
file_lock = threading.Lock()

URL = "https://discord.com/api/v9/users/@me/pomelo-attempt"

def load_tokens():
    if os.path.exists(tokens_path):
        with open(tokens_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

def load_proxies():
    if os.path.exists(proxies_path):
        with open(proxies_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

tokens = load_tokens()
proxies = load_proxies()
token_idx = 0
proxy_idx = 0

def get_headers(token=None):
    token = token or configur.get("sys", "TOKEN", fallback="")
    return {
        "Content-Type": "application/json",
        "Authorization": token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    }

def get_next_proxy():
    global proxy_idx
    if not proxies:
        return None
    proxy = proxies[proxy_idx % len(proxies)]
    proxy_idx += 1
    return {"http": proxy, "https": proxy}

def get_next_token():
    global token_idx
    if not tokens:
        return None
    token = tokens[token_idx % len(tokens)]
    token_idx += 1
    return token

def check_username(username, token=None):
    username = username.lower().strip()
    if not username or len(username) < 2 or len(username) > 32:
        return None
    
    body = {"username": username}
    use_token = token or get_next_token() or configur.get("sys", "TOKEN", fallback="")
    headers = get_headers(use_token)
    proxy = get_next_proxy()
    
    try:
        resp = requests.post(URL, headers=headers, json=body, proxies=proxy, timeout=12)
        
        if resp.status_code == 429:
            retry_after = resp.json().get("retry_after", 3)
            with print_lock:
                print(f"{Fore.LIGHTBLACK_EX}[!]{Fore.YELLOW} Rate limit → waiting {retry_after}s")
            time.sleep(retry_after)
            return check_username(username, use_token)  # retry
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("taken") is False:
                with print_lock:
                    print(f"{Fore.LIGHTBLACK_EX}[+]{Fore.LIGHTGREEN_EX} AVAILABLE → {username}")
                save_hit(username)
                send_webhook(username)
                return True
            else:
                with print_lock:
                    print(f"{Fore.LIGHTBLACK_EX}[-]{Fore.RED} Taken → {username}")
                return False
        else:
            with print_lock:
                print(f"{Fore.LIGHTBLACK_EX}[?]{Fore.RED} Error {resp.status_code} for {username}")
            return None
            
    except Exception as e:
        with print_lock:
            print(f"{Fore.LIGHTBLACK_EX}[?]{Fore.RED} Request failed for {username}: {e}")
        return None

def save_hit(username):
    with file_lock:
        with open(av_list, "a", encoding="utf-8") as f:
            f.write(f"{username}\n")

def send_webhook(username):
    webhook_url = configur.get("sys", "WEBHOOK_URL", fallback="")
    if not webhook_url or not webhook_url.startswith("https"):
        return
    try:
        embed = {
            "title": "✅ Username Available!",
            "description": f"`{username}`",
            "color": 0x00ff00,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }
        requests.post(webhook_url, json={"embeds": [embed]}, timeout=8)
    except:
        pass

def generate_username(length=8):
    chars = string.ascii_lowercase + string.digits + "._"
    return ''.join(random.choice(chars) for _ in range(length))

def main():
    print(f"{Fore.LIGHTYELLOW_EX}=== {__version__} ==={Fore.RESET}")
    print(f"{Fore.LIGHTCYAN_EX}Multi-threaded Discord Username Checker\n")
    
    token = configur.get("sys", "TOKEN", fallback="")
    if token:
        try:
            me = requests.get("https://discord.com/api/v9/users/@me", headers=get_headers(token), timeout=10).json()
            print(f"{Fore.LIGHTGREEN_EX}Logged in as: {me.get('username', 'Unknown')}")
        except:
            print(f"{Fore.YELLOW}Warning: Could not verify token.")
    
    num_threads = int(configur.get("config", "threads", fallback="8"))
    delay = float(configur.get("config", "default_delay", fallback="0.8"))
    
    print(f"{Fore.LIGHTCYAN_EX}Loaded: {len(tokens)} tokens | {len(proxies)} proxies | Threads: {num_threads} | Base delay: {delay}s\n")
    
    while True:
        print(f"{Fore.LIGHTBLACK_EX}[1] Generate & Check (Fast)")
        print(f"{Fore.LIGHTBLACK_EX}[2] Check from usernames.txt")
        print(f"{Fore.LIGHTBLACK_EX}[3] Exit")
        choice = input(f"\nChoice:> ").strip()
        
        if choice == "1":
            try:
                length = int(input("Username length (2-32): "))
                count = int(input("How many to generate: "))
                if not 2 <= length <= 32:
                    print(f"{Fore.RED}Invalid length!")
                    continue
                
                print(f"{Fore.CYAN}Starting {count} checks with {num_threads} threads...")
                with ThreadPoolExecutor(max_workers=num_threads) as executor:
                    futures = []
                    for _ in range(count):
                        name = generate_username(length)
                        futures.append(executor.submit(check_username, name))
                        time.sleep(delay)  # slight stagger to avoid instant burst
                    
                    for future in as_completed(futures):
                        future.result()  # wait for completion
                
            except Exception as e:
                print(f"{Fore.RED}Error: {e}")
                
        elif choice == "2":
            if not os.path.exists(username_list):
                print(f"{Fore.RED}usernames.txt not found!")
                continue
            with open(username_list, "r", encoding="utf-8") as f:
                usernames = [line.strip() for line in f if line.strip()]
            
            print(f"{Fore.CYAN}Checking {len(usernames)} usernames with {num_threads} threads...")
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(check_username, u) for u in usernames]
                for future in as_completed(futures):
                    future.result()
        
        elif choice == "3":
            print(f"{Fore.LIGHTYELLOW_EX}Goodbye!")
            break
        else:
            print(f"{Fore.RED}Invalid option.")

if __name__ == "__main__":
    main()
