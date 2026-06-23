import requests
import json
import os
import sys

# Add the project root to sys.path to import config
sys.path.append(os.getcwd())

try:
    from settings.config import Config
    config = Config['default']
    client_id = config.PAYPAL_CLIENT_ID
    client_secret = config.PAYPAL_CLIENT_SECRET
    mode = 'sandbox' # Force sandbox to test if credentials belong there
except Exception as e:
    print(f"Error importing config: {e}")
    sys.exit(1)

base_url = "https://api-m.paypal.com" if mode == 'live' else "https://api-m.sandbox.paypal.com"

print(f"--- PayPal Diagnostic Tool ---")
print(f"Mode: {mode}")
print(f"Base URL: {base_url}")
print(f"Client ID: {client_id[:10]}...")

def get_token():
    print("\n1. Requesting Access Token...")
    response = requests.post(
        f"{base_url}/v1/oauth2/token",
        auth=(client_id, client_secret),
        data={"grant_type": "client_credentials"}
    )
    if response.ok:
        print("Success: Token received.")
        return response.json()['access_token']
    else:
        print(f"Error: {response.text}")
        return None

def list_plans(token):
    print("\n2. Fetching Active Plans from PayPal...")
    response = requests.get(
        f"{base_url}/v1/billing/plans?page_size=20&status=ACTIVE",
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.ok:
        plans = response.json().get('plans', [])
        if not plans:
            print("No active plans found. Make sure you have ACTIVATE them in the dashboard.")
        else:
            print(f"Found {len(plans)} active plans:")
            for plan in plans:
                print(f" - {plan['name']} (ID: {plan['id']}) [Status: {plan['status']}]")
    else:
        print(f"Error fetching plans: {response.text}")

token = get_token()
if token:
    list_plans(token)
