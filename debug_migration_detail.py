import requests
import getpass
import json

CANVAS_URL = "https://courses.lenguax.com"
ACCESS_TOKEN = getpass.getpass("🔑 Enter your Canvas API token (input hidden): ")

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

def main():
    course_id = input("Enter the TARGET course ID: ").strip()
    migration_id = input("Enter the migration ID to inspect (from the previous script): ").strip()

    resp = requests.get(
        f"{CANVAS_URL}/api/v1/courses/{course_id}/content_migrations/{migration_id}",
        headers=headers
    )
    resp.raise_for_status()
    print("\n=== Full migration object ===")
    print(json.dumps(resp.json(), indent=2))

if __name__ == "__main__":
    main()
