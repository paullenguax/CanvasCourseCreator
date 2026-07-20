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
    source_id = input("Enter the SOURCE course ID (e.g. 35): ").strip()
    target_id = input("Enter the TARGET course ID (e.g. 38): ").strip()

    source_quizzes = get_quizzes(source_id)
    target_quizzes = get_quizzes(target_id)
    target_titles = {q["title"].strip() for q in target_quizzes}

    print(f"\nSource has {len(source_quizzes)} quizzes, target has {len(target_quizzes)} quizzes.\n")

    missing = [q for q in source_quizzes if q["title"].strip() not in target_titles]
    present = [q for q in source_quizzes if q["title"].strip() in target_titles]

    print(f"=== {len(missing)} quiz(zes) missing from target ===")
    for q in missing:
        print(f"\n- '{q['title']}' (id {q['id']}, quiz_type={q.get('quiz_type')})")
        print(f"    question_count={q.get('question_count')}")
        print(f"    has_access_code={bool(q.get('access_code'))}")
        print(f"    one_question_at_a_time={q.get('one_question_at_a_time')}")
        print(f"    quiz_extensions_url present={'quiz_extensions_url' in q}")

        questions = get_quiz_questions(source_id, q["id"])
        qtypes = sorted(set(qq.get("question_type") for qq in questions))
        uses_bank = any(qq.get("question_type") is None or "assessment_question_bank_id" in qq for qq in questions)
        print(f"    question_types_used={qtypes}")
        print(f"    quiz_group_id_present={any(qq.get('quiz_group_id') for qq in questions)}")

    print(f"\n=== {len(present)} quiz(zes) present in both (for comparison) ===")
    for q in present[:5]:
        print(f"- '{q['title']}' (id {q['id']}, quiz_type={q.get('quiz_type')})")

if __name__ == "__main__":
    main()
