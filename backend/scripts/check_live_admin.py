"""Verify live administrator JWT authorization without database writes."""

from getpass import getpass

import httpx


BASE_URL = "http://127.0.0.1:8000"
ADMIN_EMAIL = "sunnykhubchandani030303@gmail.com"


def main():
    password = getpass("Administrator password: ")

    with httpx.Client(base_url=BASE_URL, timeout=30) as client:

        health = client.get("/health")
        assert health.status_code == 200, (
            f"Health check returned {health.status_code}"
        )
        print("PASS: FastAPI server running")

        anonymous = client.get("/api/v1/projects/")
        assert anonymous.status_code == 401, (
            f"Expected HTTP 401, got {anonymous.status_code}. "
            "Restart Uvicorn to load the authorization patch."
        )
        print("PASS: Anonymous project access blocked")

        login = client.post(
            "/api/v1/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": password,
            },
        )

        assert login.status_code == 200, (
            f"Administrator login returned HTTP {login.status_code}"
        )
        print("PASS: Administrator login")

        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        profile = client.get(
            "/api/v1/auth/me",
            headers=headers,
        )

        assert profile.status_code == 200, (
            f"Profile request returned HTTP {profile.status_code}"
        )

        user = profile.json()

        assert user["email"] == ADMIN_EMAIL
        assert user["role"] == "admin"
        assert user["is_active"] is True
        print("PASS: Administrator identity verified")

        projects = client.get(
            "/api/v1/projects/",
            headers=headers,
        )

        assert projects.status_code == 200, (
            f"Admin project access returned HTTP {projects.status_code}"
        )
        print("PASS: Administrator project access granted")

    print("\nLIVE ADMINISTRATOR AUTHORIZATION VERIFIED")


if __name__ == "__main__":
    main()
