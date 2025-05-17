import re
import json
import requests
from collections import defaultdict

LOCAL_FILE = "MissingSortedBySize.txt"
OUTPUT_JSON = "match_results.json"
MIN_MATCH_LENGTH = 5

def normalize(name):
    return re.sub(r'\W+', '', name.lower())

def load_hibp_breaches():
    try:
        response = requests.get(
            "https://haveibeenpwned.com/api/v3/breaches",
            headers={"User-Agent": "HIBP-Checker-Script"}
        )
        response.raise_for_status()
        return [b['Name'] for b in response.json()]
    except Exception:
        print("[WARN] Couldn't reach HIBP API. Falling back to local names.")
        return [
            "Nitro", "LastFM", "Shein", "Click", "Emuparadise", "Capital Economics", "Bookmate",
            "InterPals", "Duolingo", "RedMart", "HiAPK", "R2Games", "BinWeevils", "GGumim", "Audi",
            "Morele", "Nulled", "Legendas", "PetFlow", "JamesDelivery", "PaySystem", "ReverbNation",
            "CPRewritten", "GoGames"
        ]

def load_local_breaches(filepath):
    entries = []
    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            match = re.match(r"^\s*-\s([\d,]+)\s+(.+)$", line.strip())
            if match:
                size = int(match.group(1).replace(",", ""))
                raw_name = match.group(2).replace("_BF", "").replace(".7z", "")
                entries.append({
                    "raw_name": raw_name,
                    "normalized": normalize(raw_name),
                    "size": size
                })
    return entries

def find_matches(local_breaches, hibp_names):
    hibp_normalized = {normalize(name): name for name in hibp_names}
    hibp_keys = list(hibp_normalized.keys())
    results = []

    for entry in local_breaches:
        local_norm = entry["normalized"]
        matches = []

        for hibp_norm in hibp_keys:
            if len(local_norm) < MIN_MATCH_LENGTH and len(hibp_norm) < MIN_MATCH_LENGTH:
                continue
            if hibp_norm in local_norm or local_norm in hibp_norm:
                matches.append({
                    "hibp_name": hibp_normalized[hibp_norm],
                    "match_type": "contains" if hibp_norm in local_norm else "contained_in",
                    "match_length": len(hibp_norm)
                })

        matches_sorted = sorted(matches, key=lambda x: -x["match_length"])
        results.append({
            "local_name": entry["raw_name"],
            "normalized": local_norm,
            "size": entry["size"],
            "match_count": len(matches_sorted),
            "matches": matches_sorted
        })

    return results

if __name__ == "__main__":
    hibp_names = load_hibp_breaches()
    local_breaches = load_local_breaches(LOCAL_FILE)
    results = find_matches(local_breaches, hibp_names)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"[✔] JSON saved to: {OUTPUT_JSON}")
    print(f"[📊] Local entries: {len(local_breaches)}")
    print(f"[🔍] Matched: {sum(1 for r in results if r['match_count'] > 0)}")
    print(f"[❌] Unmatched: {sum(1 for r in results if r['match_count'] == 0)}")
