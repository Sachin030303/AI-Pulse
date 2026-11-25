"""Diagnose AI-Pulse login without displaying credentials or JWTs."""

from getpass import getpass
import httpx

print("\n=== AI-PULSE LOGIN DIAGNOSTIC ===")

email = input("Administrator email: ").strip()
password = getpass("Password (hidden): ")

servers = [
    ("FastAPI backend", "http://127.0.0.1:8000"),
    ("React Vite proxy", "http://127.0.0.1:5173"),
]

with httpx.Client(timeout=15, trust_env=False) as client:
    for label, origin in servers:
        print(f"\n--- {label} ---")

        try:
            login = client.post(
                origin + "/api/v1/auth/login",
                json={
                    "email": email,
                    "password": password,
                },
            )

            print("Login HTTP status:", login.status_code)

            if login.status_code != 200:
                if login.status_code == 401:
                    print("RESULT: Credentials rejected")
                elif login.status_code == 422:
                    print("RESULT: Login request validation failed")
                else:
                    print("RESULT: Login API returned an error")
                continue

            data = login.json()
            token = data.get("access_token")

            if not token:
                print("FAIL: Login response has no access token")
                continue

            print("PASS: Access token received (hidden)")

            profile = client.get(
                origin + "/api/v1/auth/me",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

            print("Session verification HTTP:", profile.status_code)

            if profile.status_code == 200:
                print("PASS: Login and session verification")
                print("Account role:", profile.json().get("role"))
            else:
                print("FAIL: Session verification")

        except (httpx.RequestError, ValueError) as error:
            print("FAIL:", type(error).__name__)

print("\nLOGIN DIAGNOSTIC COMPLETE")
