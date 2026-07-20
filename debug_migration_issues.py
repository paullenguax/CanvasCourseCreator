import requests
import getpass
import json

CANVAS_URL = "https://courses.lenguax.com"
ACCESS_TOKEN = getpass.getpass("🔑 Enter your Canvas API token (input hidden): ")

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

def get_content_migrations(course_id):
    resp = requests.get(f"{CANVAS_URL}/api/v1/courses/{course_id}/content_migrations?per_page=100", headers=headers)
    resp.raise_for_status()
    return resp.json()

def get_migration_issues(course_id, migration_id):
    resp = requests.get(
        f"{CANVAS_URL}/api/v1/courses/{course_id}/content_migrations/{migration_id}/migration_issues?per_page=100",
        headers=headers
    )
    resp.raise_for_status()
    return resp.json()

def main():
    course_id = input("Enter the TARGET course ID (the one that was copied INTO, missing quizzes): ").strip()

    migrations = get_content_migrations(course_id)
    if not migrations:
        print("No content migrations found for this course - it may not have been created via a course copy/import.")
        return

    print(f"\nFound {len(migrations)} content migration(s) for course {course_id}:\n")
    for m in migrations:
        print(f"  id={m['id']}  type={m.get('migration_type')}  state={m.get('workflow_state')}  started_at={m.get('started_at')}")

    for m in migrations:
        migration_id = m["id"]
        issues = get_migration_issues(course_id, migration_id)
        print(f"\n=== Migration {migration_id} ({m.get('migration_type')}, {m.get('workflow_state')}) - {len(issues)} issue(s) ===")
        if not issues:
            print("  (no issues logged)")
        for issue in issues:
            print(json.dumps({
                "issue_type": issue.get("issue_type"),
                "description": issue.get("description"),
                "workflow_state": issue.get("workflow_state"),
                "error_message": issue.get("error_message"),
            }, indent=2))

if __name__ == "__main__":
    main()
