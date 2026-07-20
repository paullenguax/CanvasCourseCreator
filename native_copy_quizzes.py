import requests
import getpass
import time

CANVAS_URL = "https://courses.lenguax.com"
ACCESS_TOKEN = getpass.getpass("🔑 Enter your Canvas API token (input hidden): ")

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

def get_quizzes(course_id):
    resp = requests.get(f"{CANVAS_URL}/api/v1/courses/{course_id}/quizzes?per_page=100", headers=headers)
    resp.raise_for_status()
    return resp.json()

def main():
    source_id = input("Enter the SOURCE course ID: ").strip()
    target_id = input("Enter the TARGET course ID (this is a real native Canvas course copy - it will actually create content): ").strip()

    quizzes = get_quizzes(source_id)
    quiz_ids = [q["id"] for q in quizzes]
    print(f"\nFound {len(quiz_ids)} quizzes in source course {source_id}: {quiz_ids}")

    confirm = input(f"\nTrigger a native Canvas content migration copying these {len(quiz_ids)} quizzes into course {target_id}? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Aborted.")
        return

    resp = requests.post(
        f"{CANVAS_URL}/api/v1/courses/{target_id}/content_migrations",
        headers=headers,
        data={
            "migration_type": "course_copy_importer",
            "settings[source_course_id]": source_id,
            "select[quizzes]": quiz_ids,
        }
    )
    resp.raise_for_status()
    migration = resp.json()
    migration_id = migration["id"]
    print(f"\n📦 Migration {migration_id} created, state={migration.get('workflow_state')}")

    print("⏳ Polling for completion...")
    for _ in range(30):
        time.sleep(2)
        check = requests.get(
            f"{CANVAS_URL}/api/v1/courses/{target_id}/content_migrations/{migration_id}",
            headers=headers
        )
        check.raise_for_status()
        state = check.json().get("workflow_state")
        print(f"   state={state}")
        if state in ("completed", "failed", "failed_with_messages"):
            break

    issues_resp = requests.get(
        f"{CANVAS_URL}/api/v1/courses/{target_id}/content_migrations/{migration_id}/migration_issues",
        headers=headers
    )
    issues = issues_resp.json()
    print(f"\n{len(issues)} migration issue(s) logged.")
    for issue in issues:
        print(f"  - {issue.get('description')}: {issue.get('error_message')}")

    result_quizzes = get_quizzes(target_id)
    print(f"\n✅ Target course {target_id} now has {len(result_quizzes)} quizzes:")
    for q in result_quizzes:
        print(f"   - {q['title']} (id {q['id']})")

if __name__ == "__main__":
    main()
