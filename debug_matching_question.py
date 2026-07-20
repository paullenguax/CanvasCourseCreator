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
    course_id = input("Enter the course ID to inspect (the SOURCE course with working matching questions): ").strip()

    quizzes = get_quizzes(course_id)
    for quiz in quizzes:
        questions = get_quiz_questions(course_id, quiz["id"])
        for q in questions:
            if q.get("question_type") == "matching_question":
                print(f"\n=== Found matching question in quiz '{quiz['title']}' ===")
                print(json.dumps(q, indent=2))
                return

    print("No matching_question found in this course.")

if __name__ == "__main__":
    main()
