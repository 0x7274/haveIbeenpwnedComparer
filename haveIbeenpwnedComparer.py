import requests
import re

# ANSI color codes
GREEN = '\033[92m'
DARK_GREEN = '\033[32m'
RED = '\033[91m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

HIBP_API_URL = "https://haveibeenpwned.com/api/v3/breaches"
HEADERS = {
    "User-Agent": "HIBP-Checker-Script"
}

def get_all_breaches():
    response = requests.get(HIBP_API_URL, headers=HEADERS)
    response.raise_for_status()
    breaches = response.json()
    return {breach['Name'] for breach in breaches}

def normalize(name):
    return re.sub(r'(_[A-Za-z0-9]+)?(\.zip|\.7z|\.tar\.gz)?$', '', name)

def load_local_breaches(filepath):
    normalized = {}
    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:
                size_str, raw_name = parts
                try:
                    size = int(size_str)
                except ValueError:
                    size = 0
                name = normalize(raw_name)
                normalized[name] = {'original': raw_name, 'size': size}
    return normalized

def main():
    hibp_breaches = get_all_breaches()
    local_breaches = load_local_breaches("output.txt")
    local_normalized = set(local_breaches.keys())

    in_both = hibp_breaches & local_normalized
    only_in_hibp = hibp_breaches - local_normalized
    only_local = local_normalized - hibp_breaches

    # Sort entries by file size descending
    in_both_sorted = sorted(in_both, key=lambda x: local_breaches[x]['size'], reverse=True)
    only_local_sorted = sorted(only_local, key=lambda x: local_breaches[x]['size'], reverse=True)

    print(f"\n✅ {GREEN}Breaches present in both HIBP and local (sorted by size):{RESET}")
    for name in in_both_sorted:
        entry = local_breaches[name]
        print(f"{GREEN}  ✓ {entry['size']:,} {entry['original']}{RESET}")

    print(f"\n➕ {DARK_GREEN}Breaches in HIBP but missing locally:{RESET}")
    for name in sorted(only_in_hibp):
        print(f"{DARK_GREEN}  + {name}{RESET}")

    print(f"\n❌ {RED}Breaches in local file but not found on HIBP (sorted by size):{RESET}")
    for name in only_local_sorted:
        entry = local_breaches[name]
        print(f"{RED}  - {entry['size']:,} {entry['original']}{RESET}")

    print(f"\n{BOLD}{CYAN}📊 Summary:{RESET}")
    print(f"  {GREEN}✔ In both         : {len(in_both)}{RESET}")
    print(f"  {DARK_GREEN}➕ HIBP only      : {len(only_in_hibp)}{RESET}")
    print(f"  {RED}❌ Local only     : {len(only_local)}{RESET}")
    print(f"  {CYAN}📈 Total HIBP     : {len(hibp_breaches)}")
    print(f"  📄 Total Local    : {len(local_normalized)}{RESET}")

if __name__ == "__main__":
    main()
