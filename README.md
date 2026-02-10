# 🎯 Bloxsnipe

A high-performance Roblox username sniper with pattern support, real-time statistics, and Discord webhook integration.

**Developed by:** [fear.sh](https://fear.subeditor.works/)  and terror._1.

**Discord:** `fear.sh`
**Discord:** `terror._1.`
---

## 🚀 Features

- **Multi-Mode Sniping:** Choose from 3-letter, 4-letter, CVCV patterns, or infinite random generation.
- **Custom Lists:** Load your own target list from `usernames.txt`.
- **Intelligent Rate Limiting:** Automatically switches to proxy checking when rate-limited to maintain speed.
- **Live Dashboard:** Real-time console UI with check speed, valid count, and status tracking.
- **Discord Integration:** Get instant notifications when a valid username is found.

## 🛠️ Installation

1. **Clone the repository** (or download the ZIP).
2. **Install requirements:**
   ```sh
   pip install requests rich
   ```

## 📖 How to Use

### 1. Configure the Sniper
Run the main script:
```sh
python main.py
```
On the first run, it will ask for your **Discord Webhook URL** (optional) and save it to `config.json`.

### 2. Choose a Sniping Mode
Select one of the built-in patterns:
- `[1]` 3-Letter Names
- `[2]` 4-Letter Names
- `[3]` CVCV (e.g., pogo)
- `[4]` Infinite Random
- `[5]` Use `usernames.txt`

### 3. Generating Custom Lists (Optional)
If you want to generate a custom list of random usernames to `usernames.txt`, use the generator:
```sh
python UG.py
```

## 📂 File Structure

- `main.py`: The core sniper engine and UI.
- `UG.py`: Utility script to generate custom username lists.
- `usernames.txt`: Input file for custom username targets.
- `valid.txt`: Output file where found usernames are saved.
- `config.json`: Stores your webhook configuration. (Auto generated)

---
*Disclaimer: This tool is for educational purposes only. Use responsibly.*
