import requests
import getpass
import json

CANVAS_URL = "https://courses.lenguax.com"
ACCESS_TOKEN = getpass.getpass("🔑 Enter your Canvas API token (input hidden): ")

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

def get_quizzes(course_id):
    resp = requests.get(f"{CANVAS_URL}/api/v1/courses/{course_id}/quizzes?per_page=100", headers=headers)
    resp.raise_for_status()
    return resp.json()

def get_quiz_questions(course_id, quiz_id):
    resp = requests.get(f"{CANVAS_URL}/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions?per_page=100", headers=headers)
    resp.raise_for_status()
    return resp.json()

def main():
    course_id = input("Enter the SOURCE course ID to scan: ").strip()

    quizzes = get_quizzes(course_id)
    found_any = False
    for quiz in quizzes:
        questions = get_quiz_questions(course_id, quiz["id"])
        for q in questions:
            for answer in q.get("answers", []):
                comments = answer.get("comments") or ""
                comments_html = answer.get("comments_html") or ""
                if comments.strip() or comments_html.strip():
                    found_any = True
                    print(f"\n=== Quiz '{quiz['title']}' - question id {q['id']} ({q.get('question_type')}) - answer id {answer.get('id')} ===")
                    print(json.dumps({"comments": comments, "comments_html": comments_html}, indent=2))

    if not found_any:
        print("\nNo per-answer comments found on any answer in this course - the field is empty in the source too.")

if __name__ == "__main__":
    main()
