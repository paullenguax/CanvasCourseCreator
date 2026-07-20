
import requests
import time
import getpass

# === CONFIG ===
CANVAS_URL = "https://courses.lenguax.com"
ACCESS_TOKEN = getpass.getpass("🔑 Enter your Canvas API token (input hidden): ")

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

def get_quizzes(course_id):
    print(f"📥 Fetching quizzes from course {course_id}...")
    resp = requests.get(f"{CANVAS_URL}/api/v1/courses/{course_id}/quizzes?per_page=100", headers=headers)
    resp.raise_for_status()
    return resp.json()

def get_quiz_questions(course_id, quiz_id):
    print(f"🔍 Fetching questions for quiz {quiz_id}...")
    resp = requests.get(f"{CANVAS_URL}/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions?per_page=100", headers=headers)
    resp.raise_for_status()
    return resp.json()

def create_quiz(course_id, quiz_data):
    print(f"📝 Creating quiz: {quiz_data['title']}")
    payload = {
        "quiz": {
            "title": quiz_data["title"],
            "description": quiz_data.get("description", ""),
            "quiz_type": quiz_data["quiz_type"],
            "published": False,
            "shuffle_answers": quiz_data.get("shuffle_answers", True),
            "time_limit": quiz_data.get("time_limit", None),
            "hide_results": None,
            "show_correct_answers": True,
            "allowed_attempts": quiz_data.get("allowed_attempts", 1),
            "scoring_policy": quiz_data.get("scoring_policy", "keep_highest"),
        }
    }
    resp = requests.post(f"{CANVAS_URL}/api/v1/courses/{course_id}/quizzes", headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()

def create_question(course_id, quiz_id, question):
    print(f"🆕 Creating question: {question.get('question_name', 'Unnamed')}")

    qtype = question["question_type"]
    print(f"   📝 Question type: {qtype}")

    data = {
        "question": {
            "question_name": question.get("question_name", ""),
            "question_text": question.get("question_text", ""),
            "question_type": qtype,
            "points_possible": question.get("points_possible", 1),
        }
    }

    # Question-level feedback (shown for correct/incorrect/any answer) - verified to
    # persist correctly via the API, unlike per-answer comments below.
    for field in ("correct_comments", "incorrect_comments", "neutral_comments"):
        if question.get(field):
            data["question"][field] = question[field]

    if "answers" in question and question["answers"]:
        data["question"]["answers"] = []
        for answer in question["answers"]:
            answer_data = {
                "answer_text": answer.get("text", ""),
                "answer_weight": answer.get("weight", 0),
            }

            # NOTE: per-answer comments (answer_comments) do NOT persist via this API -
            # verified empirically (POST and PUT both return 200 but the comment never
            # shows up, even in the Canvas UI). This is a real Canvas platform
            # limitation, not a request-format issue, so we don't attempt it.

            # Matching question support with correct field names
            if qtype == "matching_question":
                if answer.get("left"):
                    answer_data["answer_match_left"] = answer["left"]
                if answer.get("right"):
                    answer_data["answer_match_right"] = answer["right"]

            data["question"]["answers"].append(answer_data)

        # Distractor pool for matching questions lives on the question, not per-answer
        if qtype == "matching_question" and question.get("matching_answer_incorrect_matches"):
            if data["question"]["answers"]:
                data["question"]["answers"][0]["matching_answer_incorrect_matches"] = question["matching_answer_incorrect_matches"]

    try:
        print(f"   🚀 Posting question to Canvas...")
        resp = requests.post(
            f"{CANVAS_URL}/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions",
            headers=headers,
            json=data
        )
        resp.raise_for_status()
        print(f"   ✅ Question created successfully!")
    except requests.exceptions.HTTPError as e:
        print(f"   ❌ Failed to create question: {e}")
        print(f"   Response: {e.response.text}")

def copy_all_quizzes():
    source_course_id = input("Enter the source (master) course ID: ").strip()
    target_course_id = input("Enter the target course ID: ").strip()

    quizzes = get_quizzes(source_course_id)
    print(f"🎯 Found {len(quizzes)} quizzes to copy.\n")

    for quiz in quizzes:
        print(f"🔄 Processing quiz: {quiz['title']}")
        new_quiz = create_quiz(target_course_id, quiz)
        original_questions = get_quiz_questions(source_course_id, quiz["id"])
        print(f"   📊 Found {len(original_questions)} questions to copy")

        for q in original_questions:
            create_question(target_course_id, new_quiz["id"], q)

        print(f"✅ Completed quiz: {quiz['title']}\n")
        time.sleep(1)

if __name__ == "__main__":
    copy_all_quizzes()
