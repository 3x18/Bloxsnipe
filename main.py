import requests
import time
import threading
import os
import json
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console, Group
from rich.live import Live
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.panel import Panel

# --- CONFIGURATION ---
CONFIG_FILE = "config.json"
THREADS = 50
COOLDOWN_THRESHOLD = 15  # Pause if 15 errors occur rapidly
COOLDOWN_TIME = 30       # Seconds to stay on cooldown
# ---------------------

console = Console()

class Stats:
    def __init__(self, total=0):
        self.total = total
        self.checked = 0
        self.valid = 0
        self.taken = 0
        self.censored = 0
        self.errors = 0
        self.consecutive_errors = 0
        self.current_user = "Waiting..."
        self.start_time = time.time()
        self.on_cooldown = False
        self.cooldown_remaining = 0
        self.failed_usernames = []
        self.lock = threading.Lock()

    def reset(self, total):
        self.total = total
        self.checked = 0
        self.valid = 0
        self.taken = 0
        self.censored = 0
        self.errors = 0
        self.consecutive_errors = 0
        self.failed_usernames = []
        self.start_time = time.time()
        self.on_cooldown = False

    @property
    def speed(self):
        elapsed = time.time() - self.start_time
        return self.checked / elapsed if elapsed > 0 else 0

stats = None
WEBHOOK_URL = ""

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_config(webhook):
    with open(CONFIG_FILE, "w") as f: json.dump({"webhook": webhook}, f)

def generate_pattern_user(mode):
    chars = string.ascii_lowercase + string.digits
    vowels = "aeiou"
    consonants = "".join(c for c in string.ascii_lowercase if c not in vowels)
    
    if mode == "1": return "".join(random.choices(chars, k=3))
    elif mode == "2": return "".join(random.choices(chars, k=4))
    elif mode == "3": return random.choice(consonants) + random.choice(vowels) + random.choice(consonants) + random.choice(vowels)
    return "".join(random.choices(chars, k=5))

def send_webhook(username):
    if not WEBHOOK_URL: return
    payload = {
        "username": "Bloxsnipe",
        "avatar_url": "https://www.roblox.com/headshot-thumbnail/image?userId=1&width=420&height=420&format=png",
        "embeds": [{
            "title": "🎯 Username Available!",
            "description": f"A new username has been successfully sniped.",
            "color": 5763719,
            "fields": [
                {"name": "👤 Username", "value": f"**`{username}`**", "inline": True},
                {"name": "✨ Status", "value": "✅ **Valid**", "inline": True},
                {"name": "🔗 Profile Link", "value": f"[Click to view](https://www.roblox.com/users/profile?username={username})", "inline": False},
                {"name": "🌐 Info", "value": "Discord: **fear.sh**", "inline": False}
            ],
            "footer": {"text": "Bloxsnipe | Made by fear.sh"},
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }]
    }
    try: requests.post(WEBHOOK_URL, json=payload, timeout=5)
    except: pass

def check_username(username):
    global stats
    base_url = f"https://auth.roblox.com/v1/usernames/validate?Username={username}&Birthday=2000-01-01"
    cors_url = f"https://corsproxy.io/?{base_url}"
    
    with stats.lock:
        stats.current_user = username

    response_data = None
    
    if stats.on_cooldown:
        try:
            resp = requests.get(cors_url, timeout=7)
            if resp.status_code == 200:
                response_data = resp.json()
        except: pass
    else:
        try:
            resp = requests.get(base_url, timeout=5)
            if resp.status_code == 200:
                response_data = resp.json()
            elif resp.status_code == 429:
                response_data = "RATE"
        except:
            try:
                resp = requests.get(cors_url, timeout=5)
                if resp.status_code == 200:
                    response_data = resp.json()
            except: pass

    with stats.lock:
        if response_data == "RATE":
            stats.checked += 1
            stats.errors += 1
            stats.consecutive_errors += 1
            stats.failed_usernames.append(username)
            if stats.consecutive_errors >= COOLDOWN_THRESHOLD:
                stats.on_cooldown = True
                stats.cooldown_remaining = COOLDOWN_TIME
        elif isinstance(response_data, dict) and "code" in response_data:
            stats.checked += 1
            stats.consecutive_errors = 0
            code = response_data.get("code")
            if code == 0:
                stats.valid += 1
                with open("valid.txt", "a") as f: f.write(f"{username}\n")
                send_webhook(username)
            elif code == 1: stats.taken += 1
            elif code == 2: stats.censored += 1
            else: 
                stats.errors += 1
                stats.failed_usernames.append(username)
        else:
            stats.checked += 1
            stats.errors += 1
            stats.consecutive_errors += 1
            stats.failed_usernames.append(username)
            if stats.consecutive_errors >= COOLDOWN_THRESHOLD and not stats.on_cooldown:
                stats.on_cooldown = True
                stats.cooldown_remaining = COOLDOWN_TIME

def cooldown_timer_thread():
    global stats
    while True:
        if stats and stats.on_cooldown:
            while stats.cooldown_remaining > 0:
                time.sleep(1)
                with stats.lock:
                    stats.cooldown_remaining -= 1
            with stats.lock:
                stats.on_cooldown = False
                stats.consecutive_errors = 0
        time.sleep(1)

def generate_stats_table():
    table = Table(show_header=False, box=None)
    table.add_column("Label", style="bold white")
    table.add_column("Value")
    
    if stats.on_cooldown:
        status = f"[bold red]COOLDOWN ({stats.cooldown_remaining}s)[/bold red] [dim](Proxy Only)[/dim]"
    else:
        status = "[bold green]ACTIVE[/bold green] [dim](Direct + Proxy)[/dim]"

    table.add_row("Status:", status)
    table.add_row("Checking:", f"[bold yellow]{stats.current_user}[/bold yellow]")
    table.add_row("Checked:", f"[bold blue]{stats.checked}[/bold blue]" + (f"/[blue]{stats.total}[/blue]" if stats.total > 0 else ""))
    table.add_row("Valid:", f"[bold green]{stats.valid}[/bold green]")
    table.add_row("Taken:", f"[bold red]{stats.taken}[/bold red]")
    table.add_row("Censored:", f"[bold magenta]{stats.censored}[/bold magenta]")
    table.add_row("Errors:", f"[bold red]{stats.errors}[/bold red]" if stats.errors > 0 else "0")
    table.add_row("Speed:", f"[bold cyan]{stats.speed:.2f} u/s[/bold cyan]")
    
    return Panel(
        table, 
        title="[bold white]Bloxsnipe Stats[/bold white]", 
        subtitle="[bold cyan]Discord: fear.sh[/bold cyan]",
        border_style="red" if stats.on_cooldown else "bright_blue", 
        expand=False
    )

def run_sniper_loop(usernames, infinite, choice):
    progress = Progress(
        TextColumn("[bold white]{task.description}"),
        BarColumn(bar_width=None, complete_style="green"),
        "[progress.percentage]{task.percentage:>3.0f}%" if not infinite else "",
        TimeRemainingColumn() if not infinite else "",
    )
    task_id = progress.add_task("Sniping...", total=len(usernames) if not infinite else None)

    with Live(Group(generate_stats_table(), progress), refresh_per_second=10) as live:
        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            if infinite:
                while True:
                    sleep_time = 0.1 if stats.on_cooldown else 0.02
                    executor.submit(check_username, generate_pattern_user(choice))
                    progress.update(task_id, advance=0.1) 
                    live.update(Group(generate_stats_table(), progress))
                    time.sleep(sleep_time)
            else:
                futures = [executor.submit(check_username, u) for u in usernames]
                for _ in as_completed(futures):
                    progress.update(task_id, advance=1)
                    live.update(Group(generate_stats_table(), progress))

def main():
    global stats, WEBHOOK_URL
    os.system('clear')
    console.print("[bold green]Starting Bloxsnipe...[/bold green]")
    
    config = load_config()
    saved_webhook = config.get("webhook", "")
    
    if saved_webhook:
        use_saved = console.input(f"\n[bold cyan]Found saved webhook ({saved_webhook[:20]}...). Use it? (y/n/enter=y): [/bold cyan]").lower()
        if use_saved == 'n':
            WEBHOOK_URL = console.input("[bold cyan]Enter new Discord Webhook (Optional, Enter to skip): [/bold cyan]").strip()
            save_config(WEBHOOK_URL)
        else: WEBHOOK_URL = saved_webhook
    else:
        WEBHOOK_URL = console.input("\n[bold cyan]Enter Discord Webhook (Optional, Enter to skip): [/bold cyan]").strip()
        if WEBHOOK_URL: save_config(WEBHOOK_URL)

    console.print("\n[bold white]Pattern Sniper & Mode Options:[/bold white]")
    console.print("[1] 3-Letter Names")
    console.print("[2] 4-Letter Names")
    console.print("[3] CVCV (e.g. pogo)")
    console.print("[4] Infinite Random")
    console.print("[5] Use usernames.txt")
    
    choice = console.input("\n[bold cyan]Select Option (Enter to ignore/default): [/bold cyan]").strip()
    
    usernames = []
    infinite = False
    
    if choice == "5":
        try:
            with open("usernames.txt", "r") as file: usernames = file.read().splitlines()
        except FileNotFoundError:
            console.print("[red]usernames.txt not found![/red]")
            return
    elif choice in ["1", "2", "3", "4"]:
        infinite = True
    else:
        try:
            with open("usernames.txt", "r") as file: usernames = file.read().splitlines()
        except FileNotFoundError:
            infinite = True
            choice = "4"

    stats = Stats(len(usernames) if not infinite else 0)
    threading.Thread(target=cooldown_timer_thread, daemon=True).start()

    os.system('clear')
    console.print("[bold green]Starting Bloxsnipe...[/bold green]\n")

    while True:
        run_sniper_loop(usernames, infinite, choice)

        console.print("\n[bold green]Execution Complete.[/bold green]")
        total_time = time.time() - stats.start_time
        minutes, seconds = divmod(int(total_time), 60)
        hours, minutes = divmod(minutes, 60)
        time_str = f"{seconds}s"
        if minutes > 0: time_str = f"{minutes}m {time_str}"
        if hours > 0: time_str = f"{hours}h {time_str}"
        console.print(f"[bold white]Time Taken:[/bold white] [bold cyan]{time_str}[/bold cyan]")
        console.print(f"[bold white]Total Checked:[/bold white] [bold blue]{stats.checked}[/bold blue]")
        console.print(f"[bold white]Valid Found:[/bold white] [bold green]{stats.valid}[/bold green]\n")

        if not infinite and stats.failed_usernames:
            recheck = console.input(f"[bold yellow]Found {len(stats.failed_usernames)} errors. Re-check them? (y/n): [/bold yellow]").lower()
            if recheck == 'y':
                usernames = stats.failed_usernames[:]
                stats.reset(len(usernames))
                os.system('clear')
                console.print("[bold green]Re-checking Error Names...[/bold green]\n")
                continue
        break

if __name__ == "__main__":
    main()