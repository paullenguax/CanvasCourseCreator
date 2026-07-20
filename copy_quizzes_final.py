
import requests
import time
import getpass
import re
import html as html_module

# === CONFIG ===
CANVAS_URL = "https://courses.lenguax.com"
ACCESS_TOKEN = getpass.getpass("🔑 Enter your Canvas API token (input hidden): ")

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

def html_to_plain_text(value):
    # Question feedback fields display whatever string is written to them
    # verbatim - Canvas does not render markup in them - so raw HTML (as stored
    # in the *_html variants) shows up as literal tag soup. Strip it to plain text.
    if not value:
        return value
    text = re.sub(r'(?i)<br\s*/?>', '\n', value)
    text = re.sub(r'(?i)</p\s*>', '\n\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = html_module.unescape(text)
    text = text.replace('\xa0', ' ')
    text = re.sub(r' +', ' ', text)
    return text.strip()

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

    # Per-answer comments ("if student chooses this answer" feedback) cannot be
    # written via this API - verified empirically, see README. Collect any found
    # in the source so they can be reported for manual re-entry instead of
    # silently vanishing.
    skipped_comments = set()
    for answer in question.get("answers", []):
        comment_text = answer.get("comments_html") or answer.get("comments")
        if comment_text:
            skipped_comments.add(html_to_plain_text(comment_text))

    data = {
        "question": {
            "question_name": question.get("question_name", ""),
            "question_text": question.get("question_text", ""),
            "question_type": qtype,
            "points_possible": question.get("points_possible", 1),
        }
    }

    # Question-level feedback (shown for correct/incorrect/any answer) - verified to
    # persist correctly via the API, unlike per-answer comments below. Rich-text
    # feedback is stored in the _html variant with the plain field left blank, but
    # Canvas displays whatever we write here as literal text (no markup rendering),
    # so convert HTML down to plain text rather than copying tags verbatim.
    for field in ("correct_comments", "incorrect_comments", "neutral_comments"):
        html_value = question.get(f"{field}_html")
        plain_value = question.get(field)
        if html_value:
            data["question"][field] = html_to_plain_text(html_value)
        elif plain_value:
            data["question"][field] = plain_value

    if "answers" in question and question["answers"]:
        data["question"]["answers"] = []
        for answer in question["answers"]:
            answer_data = {
                "answer_text": answer.get("text", ""),
                "answer_weight": answer.get("weight", 0),
            }

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

    return skipped_comments

def copy_all_quizzes():
    source_course_id = input("Enter the source (master) course ID: ").strip()
    target_course_id = input("Enter the target course ID: ").strip()

    quizzes = get_quizzes(source_course_id)
    print(f"🎯 Found {len(quizzes)} quizzes to copy.\n")

    manual_followup = []

    for quiz in quizzes:
        print(f"🔄 Processing quiz: {quiz['title']}")
        new_quiz = create_quiz(target_course_id, quiz)
        original_questions = get_quiz_questions(source_course_id, quiz["id"])
        print(f"   📊 Found {len(original_questions)} questions to copy")

        for q in original_questions:
            skipped_comments = create_question(target_course_id, new_quiz["id"], q)
            for comment in skipped_comments:
                manual_followup.append((quiz["title"], q["id"], comment))

        print(f"✅ Completed quiz: {quiz['title']}\n")
        time.sleep(1)

    if manual_followup:
        print("\n⚠️  MANUAL FOLLOW-UP NEEDED - per-answer comments can't be copied by this API:")
        for quiz_title, question_id, comment in manual_followup:
            print(f"   - Quiz '{quiz_title}', question {question_id}: {comment}")

if __name__ == "__main__":
    copy_all_quizzes()
