import requests
import time
from datetime import datetime

# ============================================================
# COLLECTIVE MVP — Transaction Detector
# ============================================================

TINK_CLIENT_ID = "4108870e1072447c9c36947735908f4c"
TINK_CLIENT_SECRET = "2862178434bb405e97bf87e51a941a62"

# Add your friend's shop name here (we'll update tomorrow)
CASHBACK_RULES = {
    "BELLA COFFEE": 0.30,
    "TOTALENERGIES": 0.20,
    "CARREFOUR": 0.50,
}

TINK_BASE = "https://api.tink.com"

def now():
    return datetime.now().strftime("%H:%M:%S")

def get_access_token():
    url = f"{TINK_BASE}/api/v1/oauth/token"
    payload = {
        "client_id": TINK_CLIENT_ID,
        "client_secret": TINK_CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "transactions:read accounts:read"
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print(f"[{now()}] ✅ Connected to Tink")
        return response.json().get("access_token")
    else:
        print(f"[{now()}] ❌ Token error: {response.text}")
        return None

def get_transactions(token):
    url = f"{TINK_BASE}/data/v2/transactions"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, params={"pageSize": 20})
    if response.status_code == 200:
        return response.json().get("transactions", [])
    else:
        print(f"[{now()}] ❌ Transaction error: {response.text}")
        return []

seen_ids = set()

def check_transactions(transactions):
    for txn in transactions:
        txn_id = txn.get("id")
        if txn_id in seen_ids:
            continue
        seen_ids.add(txn_id)

        merchant = (
            txn.get("merchant", {}).get("name", "") or
            txn.get("descriptions", {}).get("display", "") or ""
        ).upper()

        raw = txn.get("amount", {}).get("value", {}).get("unscaledValue", 0)
        if raw > 0:
            continue  # skip incoming money

        amount = abs(raw) / 100
        currency = txn.get("amount", {}).get("currencyCode", "EUR")
        print(f"[{now()}] 🔍 {merchant} — {amount} {currency}")

        for shop, cashback in CASHBACK_RULES.items():
            if shop in merchant:
                print("")
                print("=" * 50)
                print("🎉 CASHBACK TRIGGERED!")
                print("=" * 50)
                print(f"🏪 Shop:     {merchant}")
                print(f"💳 Paid:     {amount} {currency}")
                print(f"💰 Cashback: €{cashback}")
                print(f"⏰ Time:     {now()}")
                print("=" * 50)
                print(f"👉 Open Revolut → send €{cashback} to yourself")
                print(f"   Label: 'Cashback — {merchant}'")
                print("=" * 50)
                print("")
                break

def run():
    print("\n" + "=" * 50)
    print("  COLLECTIVE MVP — Live")
    print(f"  Watching: {', '.join(CASHBACK_RULES.keys())}")
    print("=" * 50 + "\n")

    token = get_access_token()
    if not token:
        return

    print(f"[{now()}] Loading existing transactions...")
    for txn in get_transactions(token):
        seen_ids.add(txn.get("id"))
    print(f"[{now()}] ✅ Ready. Watching for new transactions...\n")

    while True:
        try:
            check_transactions(get_transactions(token))
        except Exception as e:
            print(f"[{now()}] ⚠️ Error: {e}")
            token = get_access_token()
        time.sleep(60)

if __name__ == "__main__":
    run()