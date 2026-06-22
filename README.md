# Discord Username Checker (Updated 2026)

Modernized version of the popular Discord username sniping tool.

## Features
- Multi-token support with rotation
- Proxy support
- Webhook notifications
- Username generation + list checking
- Better rate-limit handling

## Setup

1. `pip install -r requirements.txt`
2. Edit `config.ini` with your token and webhook
3. (Optional) Add tokens to `tokens.txt` (one per line)
4. (Optional) Add proxies to `proxies.txt`
5. Run `python dsv.py`

## Files
- `dsv.py` - Main script
- `config.ini` - Configuration
- `tokens.txt` - Multiple tokens (optional)
- `proxies.txt` - Proxies (optional)
- `usernames.txt` - List of usernames to check
- `available_usernames.txt` - Hits are saved here

**Warning**: Using this tool may violate Discord ToS. Use responsibly on alt accounts.

Original by suenerve • Updated June 2026
