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
            "hide_results": None,  # Allow students to see results/feedback
            "show_correct_answers": True,  # Show correct answers to enable feedback
            "allowed_attempts": quiz_data.get("allowed_attempts", 1),
            "scoring_policy": quiz_data.get("scoring_policy", "keep_highest"),
        }
    }
    resp = requests.post(f"{CANVAS_URL}/api/v1/courses/{course_id}/quizzes", headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()

def update_question_comments(course_id, quiz_id, question_id, original_question):
    """
    Alternative approach: Try different methods to set answer comments
    """
    print(f"   🔧 Starting comment update workaround for question {question_id}")
    
    if "answers" not in original_question:
        print(f"   🔧 No answers in original question, skipping")
        return
        
    # Get the created question first
    try:
        print(f"   🔧 Fetching created question details...")
        get_resp = requests.get(
            f"{CANVAS_URL}/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions/{question_id}",
            headers=headers
        )
        get_resp.raise_for_status()
        created_question = get_resp.json()
        
        # Try Method 1: Update the entire question with comments in different format
        print(f"   🔧 METHOD 1: Trying full question update with answer AND question-level comments...")
        
        update_data = {
            "question": {
                "question_name": created_question.get("question_name", ""),
                "question_text": created_question.get("question_text", ""),
                "question_type": created_question["question_type"],
                "points_possible": created_question.get("points_possible", 1),
                "answers": []
            }
        }
        
        # Add question-level comments (general feedback)
        question_comment_fields = [
            "correct_comments", "incorrect_comments", "neutral_comments",
            "correct_comments_html", "incorrect_comments_html", "neutral_comments_html"
        ]
        
        for field in question_comment_fields:
            if field in original_question and original_question[field]:
                update_data["question"][field] = original_question[field]
                print(f"   🔧 Adding question-level {field}: {original_question[field][:50]}...")
        
        # Add answer-level comments
        created_answers = created_question.get("answers", [])
        original_answers = original_question["answers"]
        
        for i, original_answer in enumerate(original_answers):
            if i < len(created_answers):
                # Try Canvas's expected format
                answer_update = {
                    "answer_text": created_answers[i].get("text", ""),
                    "answer_weight": created_answers[i].get("weight", 0),
                }
                
                # Try multiple comment field variations
                comment_text = ""
                if original_answer.get("comments_html"):
                    comment_text = original_answer["comments_html"]
                elif original_answer.get("comments"):
                    comment_text = original_answer["comments"]
                
                if comment_text:
                    # Try all possible field names Canvas might accept
                    answer_update["answer_comments"] = comment_text
                    answer_update["comments"] = comment_text
                    answer_update["answer_comment"] = comment_text  # singular
                    answer_update["comment"] = comment_text  # singular
                    answer_update["answer_comments_html"] = comment_text
                    answer_update["comments_html"] = comment_text
                    print(f"   🔧 Adding answer-level comment to answer {i}: {comment_text[:50]}...")
                
                update_data["question"]["answers"].append(answer_update)
        
        # Send the update
        put_resp = requests.put(
            f"{CANVAS_URL}/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions/{question_id}",
            headers=headers,
            json=update_data
        )
        
        print(f"   🔧 Method 1 response: {put_resp.status_code}")
        
        if put_resp.status_code != 200:
            print(f"   🔧 METHOD 2: Trying form-encoded data with question-level comments...")
            
            # Try Method 2: Form-encoded data (sometimes Canvas prefers this)
            form_data = {
                f"question[question_name]": created_question.get("question_name", ""),
                f"question[question_text]": created_question.get("question_text", ""),
                f"question[question_type]": created_question["question_type"],
                f"question[points_possible]": created_question.get("points_possible", 1),
            }
            
            # Add question-level comments to form data
            question_comment_fields = [
                "correct_comments", "incorrect_comments", "neutral_comments",
                "correct_comments_html", "incorrect_comments_html", "neutral_comments_html"
            ]
            
            for field in question_comment_fields:
                if field in original_question and original_question[field]:
                    form_data[f"question[{field}]"] = original_question[field]
            
            # Add answer-level comments to form data
            for i, original_answer in enumerate(original_answers):
                if i < len(created_answers):
                    form_data[f"question[answers][{i}][answer_text]"] = created_answers[i].get("text", "")
                    form_data[f"question[answers][{i}][answer_weight]"] = created_answers[i].get("weight", 0)
                    
                    comment_text = original_answer.get("comments_html") or original_answer.get("comments", "")
                    if comment_text:
                        form_data[f"question[answers][{i}][answer_comments]"] = comment_text
            
            put_resp2 = requests.put(
                f"{CANVAS_URL}/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions/{question_id}",
                headers=headers,
                data=form_data
            )
            print(f"   🔧 Method 2 response: {put_resp2.status_code}")
        
        # Verify what was actually saved
        verify_resp = requests.get(
            f"{CANVAS_URL}/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions/{question_id}",
            headers=headers
        )
        
        if verify_resp.status_code == 200:
            updated_question = verify_resp.json()
            print(f"   🔍 VERIFICATION: Checking if comments were saved...")
            
            # Check question-level comments
            question_comment_fields = [
                "correct_comments", "incorrect_comments", "neutral_comments",
                "correct_comments_html", "incorrect_comments_html", "neutral_comments_html"
            ]
            
            question_comments_saved = 0
            for field in question_comment_fields:
                if field in updated_question and updated_question[field] and updated_question[field].strip():
                    print(f"   ✅ Question has {field}: {updated_question[field][:50]}...")
                    question_comments_saved += 1
            
            # Check answer-level comments
            answer_comments_saved = 0
            for i, answer in enumerate(updated_question.get("answers", [])):
                comment_fields = ['comments', 'comments_html', 'answer_comments']
                found_comment = False
                
                for field in comment_fields:
                    if field in answer and answer[field] and answer[field].strip():
                        print(f"   ✅ Answer {i} has {field}: {answer[field][:50]}...")
                        found_comment = True
                        answer_comments_saved += 1
                        break
                
                if not found_comment:
                    print(f"   ❌ Answer {i} has NO comments stored")
            
            total_saved = question_comments_saved + answer_comments_saved
            if total_saved > 0:
                print(f"   🎉 SUCCESS: {question_comments_saved} question comments + {answer_comments_saved} answer comments saved!")
            else:
                print(f"   😞 FAILED: No comments were saved by Canvas")
        
    except Exception as e:
        print(f"   ⚠️ Comment update error: {str(e)[:100]}...")
        import traceback
        print(f"   ⚠️ Traceback: {traceback.format_exc()[:300]}...")

def create_question(course_id, quiz_id, question):
    print(f"🆕 SIMPLIFIED VERSION - Creating question: {question.get('question_name', 'Unnamed')}")
    
    qtype = question["question_type"]
    print(f"   📝 Question type: {qtype}")
    
    # Build basic question structure
    data = {
        "question": {
            "question_name": question.get("question_name", ""),
            "question_text": question.get("question_text", ""),
            "question_type": qtype,
            "points_possible": question.get("points_possible", 1),
        }
    }
    
    # Add answers based on question type
    if "answers" in question and question["answers"]:
        data["question"]["answers"] = []
        for answer in question["answers"]:
            answer_data = {
                "answer_text": answer.get("text", ""),
                "answer_weight": answer.get("weight", 0),
            }
            
            # Try to add comments during creation
            if answer.get("comments_html"):
                answer_data["answer_comments"] = answer["comments_html"]
            elif answer.get("comments"):
                answer_data["answer_comments"] = answer["comments"]
            
            # Handle matching questions
            if qtype == "matching_question":
                if answer.get("left"):
                    answer_data["answer_match_left"] = answer["left"]
                if answer.get("right"):
                    answer_data["answer_match_right"] = answer["right"]
            
            data["question"]["answers"].append(answer_data)
    
    # Create the question
    try:
        print(f"   🚀 Posting question to Canvas...")
        resp = requests.post(
            f"{CANVAS_URL}/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions",
            headers=headers,
            json=data
        )
        resp.raise_for_status()
        
        question_response = resp.json()
        print(f"   ✅ Question created successfully!")
        
        # Check if we need to run the workaround
        if "answers" in question and question["answers"]:
            # Check for answer-level comments
            has_answer_comments = any(
                answer.get("comments") or answer.get("comments_html") 
                for answer in question["answers"]
            )
            
            # Check for question-level comments
            question_comment_fields = [
                "correct_comments", "incorrect_comments", "neutral_comments",
                "correct_comments_html", "incorrect_comments_html", "neutral_comments_html"
            ]
            has_question_comments = any(
                question.get(field) for field in question_comment_fields
            )
            
            has_comments = has_answer_comments or has_question_comments
            
            if has_comments:
                print(f"   🔧 Running comment workaround...")
                if has_answer_comments:
                    print(f"   📝 Found answer-level comments")
                if has_question_comments:
                    print(f"   📝 Found question-level comments")
                update_question_comments(course_id, quiz_id, question_response["id"], question)
            else:
                print(f"   🔧 No comments found, skipping workaround")
        
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
        time.sleep(1)  # Small delay to be nice to the API

if __name__ == "__main__":
    copy_all_quizzes()