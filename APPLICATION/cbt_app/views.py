import json
import random
import hashlib
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from django.db.models import Avg, Max
from .models import Question, ExamSession, TestPackage

def get_shuffled_question_data(session, question):
    """
    Deterministically shuffles options A, B, C, D of a question based on session.id and question.id,
    and returns a dictionary with the shuffled option texts and correct option letter.
    This guarantees options are randomized/jumbled differently per candidate session,
    but remains perfectly repeatable and consistent across page loads, restarts, and grading.
    """
    seed_key = f"{session.id}_{question.id}".encode('utf-8')
    seed_hash = hashlib.md5(seed_key).hexdigest()
    seed = int(seed_hash, 16)
    
    rng = random.Random(seed)
    
    original_choices = [
        ('A', question.option_a),
        ('B', question.option_b),
        ('C', question.option_c),
        ('D', question.option_d)
    ]
    
    shuffled_choices = original_choices.copy()
    rng.shuffle(shuffled_choices)
    
    shuffled_data = {
        'option_a': shuffled_choices[0][1],
        'option_b': shuffled_choices[1][1],
        'option_c': shuffled_choices[2][1],
        'option_d': shuffled_choices[3][1],
    }
    
    correct_letter = None
    for idx, (orig_letter, _) in enumerate(shuffled_choices):
        if orig_letter == question.correct_option:
            correct_letter = ['A', 'B', 'C', 'D'][idx]
            break
            
    shuffled_data['correct_option'] = correct_letter
    return shuffled_data

def candidate_profile_view(request):
    return render(request, 'cbt_app/profile.html')

def dashboard_view(request):
    """
    Renders the candidate performance analytics dashboard.
    Computes averages, historical attempts, and subject-wise accuracy metrics.
    """
    completed_sessions = ExamSession.objects.filter(is_completed=True).order_by('-end_time')
    total_completed = completed_sessions.count()

    # We will compute accurate percentages by tracking sum of scores and max possible scores
    total_score_sum = 0.0
    total_max_sum = 0.0
    percentages = []

    # Calculate subject-wise performance
    all_questions = {str(q.id): q for q in Question.objects.all()}
    
    unique_subjects = Question.objects.values_list('subject', flat=True).distinct()
    subject_correct = {sub: 0 for sub in unique_subjects}
    subject_total = {sub: 0 for sub in unique_subjects}

    for session in completed_sessions:
        user_answers = session.user_answers or {}
        for qid_str in session.question_order:
            question = all_questions.get(qid_str)
            if question:
                if question.subject not in subject_total:
                    subject_total[question.subject] = 0
                    subject_correct[question.subject] = 0
                subject_total[question.subject] += 1
                user_ans = user_answers.get(qid_str)
                if user_ans:
                    shuffled = get_shuffled_question_data(session, question)
                    if user_ans == shuffled['correct_option']:
                        subject_correct[question.subject] += 1

    subject_metrics = []
    for sub_name in unique_subjects:
        total = subject_total[sub_name]
        correct = subject_correct[sub_name]
        accuracy = round((correct / total) * 100, 1) if total > 0 else 0.0
        subject_metrics.append({
            "name": sub_name,
            "total": total,
            "correct": correct,
            "accuracy": accuracy,
        })

    # Compile enriched list of attempts for the logs table
    attempts_history = []
    for sess in completed_sessions:
        total_q = len(sess.question_order)
        
        # Calculate precise duration spent (minutes and seconds)
        duration_str = "--"
        if sess.end_time and sess.start_time:
            duration = sess.end_time - sess.start_time
            mins, secs = divmod(int(duration.total_seconds()), 60)
            duration_str = f"{mins}m {secs}s"
            
        pkg = sess.test_package
        marks_correct = float(pkg.marks_per_correct) if pkg and pkg.marks_per_correct is not None else 1.0
        max_possible = total_q * marks_correct
        
        pct = round((sess.total_score / max_possible) * 100, 1) if max_possible > 0 else 0.0
        percentages.append(pct)
        total_score_sum += sess.total_score or 0.0
        total_max_sum += max_possible
        
        # Performance tag and styling
        if pct >= 75.0:
            status = "Excellent"
            status_color = "text-green-500 bg-green-500/10 border-green-500/30"
        elif pct >= 60.0:
            status = "Borderline"
            status_color = "text-orange-500 bg-orange-500/10 border-orange-500/30"
        else:
            status = "Revision"
            status_color = "text-red-500 bg-red-500/10 border-red-500/30"

        attempts_history.append({
            "id": sess.id,
            "ref_id": str(sess.id)[:8],
            "date": sess.end_time.strftime("%Y-%m-%d %H:%M") if sess.end_time else "--",
            "duration": duration_str,
            "score": sess.total_score,
            "total_q": total_q,
            "percentage": pct,
            "status": status,
            "status_color": status_color
        })

    # Prepare timeline data for Chart (Normalizing relative scores out of 200)
    history_list = []
    for idx, sess in enumerate(reversed(completed_sessions)):
        total_q = len(sess.question_order)
        pkg = sess.test_package
        marks_correct = float(pkg.marks_per_correct) if pkg and pkg.marks_per_correct is not None else 1.0
        max_possible = total_q * marks_correct
        
        pct = round((sess.total_score / max_possible) * 100, 1) if max_possible > 0 else 0.0
        history_list.append({
            "attempt": idx + 1,
            "score": round(sess.total_score, 1),
            "real_score": round(sess.total_score, 1),
            "total_q": total_q,
            "percentage": pct,
            "date": sess.end_time.strftime("%b %d") if sess.end_time else ""
        })

    avg_score = round((total_score_sum / total_completed), 1) if total_completed > 0 else 0
    max_score = round(max([s.total_score or 0 for s in completed_sessions] + [0]), 1)
    avg_percentage = round(sum(percentages) / len(percentages), 1) if percentages else 0
    max_percentage = round(max(percentages + [0]), 1)

    all_sessions = ExamSession.objects.exclude(test_package__isnull=True)
    packages = TestPackage.objects.all().order_by('-created_at')

    def build_mock_entry(package):
        """Build a rich mock entry dict with pre-computed display metadata."""
        sess = ExamSession.objects.filter(test_package=package).order_by('-start_time').first()
        duration_str = None
        date_str = None
        pct = None
        total_q = package.questions.count()
        if sess:
            if sess.end_time and sess.start_time:
                delta = sess.end_time - sess.start_time
                mins, secs = divmod(int(delta.total_seconds()), 60)
                duration_str = f"{mins}m {secs}s"
            if sess.end_time:
                date_str = sess.end_time.strftime("%d %b %Y, %I:%M %p")
            if sess.total_score is not None and total_q:
                pct = round((sess.total_score / total_q) * 100, 1)
                
        start_url = f"/mock/{package.id}/"
        
        return {
            'id': package.id,
            'name': package.name,
            'category': package.category,
            'session': sess,
            'duration': duration_str,
            'date': date_str,
            'percentage': pct,
            'total_q': total_q,
            'start_url': start_url,
        }

    # Structure mock test list
    mock_tests = [build_mock_entry(p) for p in packages]

    context = {
        'attempts_history': attempts_history,
        'total_completed': total_completed,
        'avg_score': avg_score,
        'max_score': max_score,
        'avg_percentage': avg_percentage,
        'max_percentage': max_percentage,
        'subject_metrics': subject_metrics,
        'history_json': json.dumps(history_list),
        'active_session': ExamSession.objects.filter(is_completed=False).first(),
        'mock_tests': mock_tests,
    }
    return render(request, 'cbt_app/dashboard.html', context)


def start_session_view(request, package_id):
    """
    Creates a new Exam Session from a TestPackage.
    """
    package = get_object_or_404(TestPackage, id=package_id)
        
    # Check if there is already an in-progress session for this specific test
    in_progress = ExamSession.objects.filter(test_package=package, is_completed=False).first()
    if in_progress:
        return redirect('exam_view', session_id=in_progress.id)
        
    # Check if there is already a completed session for this specific test
    completed = ExamSession.objects.filter(test_package=package, is_completed=True).first()
    if completed:
        return redirect('result_view', session_id=completed.id)

    # Get all questions from this package
    questions = list(package.questions.values_list('id', flat=True))
    ordered_ids = [str(uid) for uid in questions]
    random.shuffle(ordered_ids)

    # Create the exam session
    session = ExamSession.objects.create(
        test_package=package,
        question_order=ordered_ids,
        user_answers={},
        is_completed=False,
    )
    return redirect('exam_view', session_id=session.id)


@ensure_csrf_cookie
def exam_view(request, session_id):
    """
    Renders the zero-flicker Single-Page Application (SPA) Exam Engine interface.
    Injects the serialized questions array and current session state directly.
    """
    session = get_object_or_404(ExamSession, id=session_id)
    
    if session.is_completed:
        return redirect('result_view', session_id=session.id)

    # Fetch questions and preserve random sequence order
    questions = Question.objects.filter(id__in=session.question_order)
    q_dict = {str(q.id): q for q in questions}
    ordered_questions = [q_dict[qid] for qid in session.question_order if qid in q_dict]

    # Serialize questions into standard dictionary format for Vanilla JS interface
    serialized_questions = []
    for idx, q in enumerate(ordered_questions):
        shuffled = get_shuffled_question_data(session, q)
        serialized_questions.append({
            "id": str(q.id),
            "num": idx + 1,
            "subject": q.subject,
            "subject_display": q.get_subject_display(),
            "subtopic": q.subtopic,
            "question_text": q.question_text,
            "option_a": shuffled['option_a'],
            "option_b": shuffled['option_b'],
            "option_c": shuffled['option_c'],
            "option_d": shuffled['option_d'],
        })

    # Calculate remaining time dynamically
    elapsed_seconds = (timezone.now() - session.start_time).total_seconds()
    total_questions = len(session.question_order)
    if total_questions <= 10:
        allowed_mins = 10
    elif total_questions == 100:
        allowed_mins = 90
    else:
        allowed_mins = 180
    total_allowed_seconds = allowed_mins * 60
    remaining_seconds = max(0, int(total_allowed_seconds - elapsed_seconds))

    context = {
        'session': session,
        'remaining_seconds': remaining_seconds,
        'questions_json': json.dumps(serialized_questions),
        'user_answers_json': json.dumps(session.user_answers),
    }
    return render(request, 'cbt_app/exam.html', context)


def save_progress_api(request, session_id):
    """
    Background POST API to save candidate progress asynchronously.
    Avoids flickers or page reloads, ensuring state is persistent in SQLite.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)
    
    session = get_object_or_404(ExamSession, id=session_id)
    if session.is_completed:
        return JsonResponse({"error": "Exam is already completed"}, status=400)
    
    # Strict server-side time verification
    elapsed_seconds = (timezone.now() - session.start_time).total_seconds()
    total_questions = len(session.question_order)
    if total_questions <= 10:
        allowed_mins = 10
    elif total_questions == 100:
        allowed_mins = 90
    else:
        allowed_mins = 180
    if elapsed_seconds > (allowed_mins * 60) + 30: # network grace
        # Auto-conclude and calculate final score based on saved answers
        questions = Question.objects.filter(id__in=session.question_order)
        q_dict = {str(q.id): q for q in questions}
        pkg = session.test_package
        marks_correct = float(pkg.marks_per_correct) if pkg and pkg.marks_per_correct is not None else 1.0
        marks_wrong = float(pkg.negative_marks) if pkg and pkg.negative_marks is not None else 0.0

        score = 0.0
        answers_ref = session.user_answers
        for qid in session.question_order:
            q = q_dict.get(qid)
            if q:
                shuffled = get_shuffled_question_data(session, q)
                user_choice = answers_ref.get(qid)
                if user_choice:
                    if user_choice == shuffled['correct_option']:
                        score += marks_correct
                    else:
                        score -= marks_wrong
        
        session.total_score = score
        session.end_time = session.start_time + timezone.timedelta(minutes=allowed_mins)
        session.is_completed = True
        session.save()
        return JsonResponse({"error": "Exam time has expired", "redirect_url": f"/result/{session.id}/"}, status=403)
        
    try:
        data = json.loads(request.body)
        answers = data.get("answers", {})
        session.user_answers = answers
        session.save()
        return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def submit_exam_api(request, session_id):
    """
    Submits the exam, scores it instantly, and marks the session as finished.
    Calculates final score dynamically based on test package settings.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=400)
        
    session = get_object_or_404(ExamSession, id=session_id)
    if session.is_completed:
        return JsonResponse({"status": "already_submitted", "redirect_url": f"/result/{session.id}/"})

    # Strict server-side time verification
    elapsed_seconds = (timezone.now() - session.start_time).total_seconds()
    total_questions = len(session.question_order)
    if total_questions <= 10:
        allowed_mins = 10
    elif total_questions == 100:
        allowed_mins = 90
    else:
        allowed_mins = 180
    is_expired = (elapsed_seconds > (allowed_mins * 60) + 30)

    try:
        data = json.loads(request.body)
        answers = data.get("answers", {})
        
        # If time is expired, discard request modifications and lock in existing server answers
        if is_expired:
            answers = session.user_answers
            
        session.user_answers = answers
        
        # Calculate score
        questions = Question.objects.filter(id__in=session.question_order)
        q_dict = {str(q.id): q for q in questions}
        
        pkg = session.test_package
        marks_correct = float(pkg.marks_per_correct) if pkg and pkg.marks_per_correct is not None else 1.0
        marks_wrong = float(pkg.negative_marks) if pkg and pkg.negative_marks is not None else 0.0
        
        score = 0.0
        for qid in session.question_order:
            q = q_dict.get(qid)
            if q:
                shuffled = get_shuffled_question_data(session, q)
                user_choice = answers.get(qid)
                if user_choice:
                    if user_choice == shuffled['correct_option']:
                        score += marks_correct
                    else:
                        score -= marks_wrong
                
        session.total_score = score
        
        if is_expired:
            session.end_time = session.start_time + timezone.timedelta(minutes=allowed_mins)
        else:
            session.end_time = timezone.now()
            
        session.is_completed = True
        session.save()
        
        return JsonResponse({"status": "success", "redirect_url": f"/result/{session.id}/"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def result_view(request, session_id):
    """
    Renders detailed diagnostics and performance feedback for a completed exam session.
    Lists each question with color coding for correct, incorrect, or skipped answers.
    """
    session = get_object_or_404(ExamSession, id=session_id)
    if not session.is_completed:
        return redirect('exam_view', session_id=session.id)
        
    # Fetch questions and preserve order
    questions = Question.objects.filter(id__in=session.question_order)
    q_dict = {str(q.id): q for q in questions}
    ordered_questions = [q_dict[qid] for qid in session.question_order if qid in q_dict]

    # Metrics calculations
    total_questions = len(ordered_questions)
    user_answers = session.user_answers or {}
    
    attempted_count = sum(1 for qid in session.question_order if user_answers.get(qid))
    unattempted_count = total_questions - attempted_count
    
    correct_count = 0
    incorrect_count = 0
    
    questions_analysis = []
    
    # Calculate subject-wise accuracy specifically for this session
    session_unique_subjects = set([q.subject for q in ordered_questions])
    sub_total = {sub: 0 for sub in session_unique_subjects}
    sub_correct = {sub: 0 for sub in session_unique_subjects}

    for idx, q in enumerate(ordered_questions):
        qid_str = str(q.id)
        user_choice = user_answers.get(qid_str)
        
        shuffled = get_shuffled_question_data(session, q)
        correct_option_for_session = shuffled['correct_option']
        
        is_correct = (user_choice == correct_option_for_session)
        is_attempted = bool(user_choice)
        
        sub_total[q.subject] += 1
        if is_attempted:
            if is_correct:
                correct_count += 1
                sub_correct[q.subject] += 1
            else:
                incorrect_count += 1

        questions_analysis.append({
            "num": idx + 1,
            "question": q,
            "shuffled_option_a": shuffled['option_a'],
            "shuffled_option_b": shuffled['option_b'],
            "shuffled_option_c": shuffled['option_c'],
            "shuffled_option_d": shuffled['option_d'],
            "shuffled_correct_option": correct_option_for_session,
            "user_choice": user_choice,
            "is_correct": is_correct,
            "is_attempted": is_attempted
        })

    accuracy_percentage = round((correct_count / total_questions) * 100, 1) if total_questions > 0 else 0

    session_subject_metrics = []
    for sub_name in session_unique_subjects:
        total = sub_total[sub_name]
        correct = sub_correct[sub_name]
        accuracy = round((correct / total) * 100, 1) if total > 0 else 0.0
        session_subject_metrics.append({
            "name": sub_name,
            "total": total,
            "correct": correct,
            "accuracy": accuracy
        })

    duration_str = ""
    if session.end_time:
        duration = session.end_time - session.start_time
        mins, secs = divmod(int(duration.total_seconds()), 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            duration_str = f"{hours}h {mins}m {secs}s"
        else:
            duration_str = f"{mins}m {secs}s"

    if total_questions <= 10:
        allowed_mins = 10
    elif total_questions == 100:
        allowed_mins = 90
    else:
        allowed_mins = 180

    context = {
        'session': session,
        'total_questions': total_questions,
        'attempted_count': attempted_count,
        'unattempted_count': unattempted_count,
        'correct_count': correct_count,
        'incorrect_count': incorrect_count,
        'accuracy_percentage': accuracy_percentage,
        'questions_analysis': questions_analysis,
        'session_subject_metrics': session_subject_metrics,
        'duration_str': duration_str,
        'allowed_mins': allowed_mins,
    }
    return render(request, 'cbt_app/result.html', context)

from django.db import transaction

def import_questions_view(request):
    success_count = None
    error_message = None

    if request.method == "POST":
        json_data = request.POST.get("json_data", "").strip()
        try:
            if not json_data:
                raise ValueError("No script pasted. Please paste a valid JSON array.")

            parsed_list = json.loads(json_data)
            if not isinstance(parsed_list, list):
                raise ValueError("Parsed data is not a JSON array. Must be enclosed in [ ].")

            if len(parsed_list) == 0:
                raise ValueError("JSON array is empty. Paste at least 1 question.")

            test_name = request.POST.get("test_name", "").strip()
            marks_per_correct = float(request.POST.get("marks_per_correct", "1.0"))
            negative_marks = float(request.POST.get("negative_marks", "0.0"))
            
            if marks_per_correct <= 0:
                raise ValueError("Marks per correct answer must be greater than 0.")
            if negative_marks < 0:
                raise ValueError("Negative penalty cannot be a negative number (e.g. enter 0.25, not -0.25).")
            if not test_name:
                raise ValueError("Test Package Name is required.")

            package, created = TestPackage.objects.get_or_create(
                name=test_name,
                defaults={
                    'category': 'ALL',
                    'marks_per_correct': marks_per_correct,
                    'negative_marks': negative_marks
                }
            )
            
            if not created:
                package.marks_per_correct = marks_per_correct
                package.negative_marks = negative_marks
                package.save()

            # Dynamic Pool: No strict length checks anymore, accept any number of valid questions

            valid_options = ['A', 'B', 'C', 'D']

            questions_to_create = []
            for idx, q in enumerate(parsed_list):
                subj = q.get("subject", "").strip().upper()
                subt = q.get("subtopic", "").strip()
                qtxt = q.get("question_text", "").strip()
                op_a = q.get("option_a", "").strip()
                op_b = q.get("option_b", "").strip()
                op_c = q.get("option_c", "").strip()
                op_d = q.get("option_d", "").strip()
                corr = q.get("correct_option", "").strip().upper()
                expl = q.get("explanation", "").strip() if q.get("explanation") else ""

                if not subj:
                    raise ValueError(f"Item {idx+1}: Missing or empty subject field.")
                if not subt:
                    raise ValueError(f"Item {idx+1}: Missing subtopic field.")
                if not qtxt:
                    raise ValueError(f"Item {idx+1}: Missing question_text field.")
                if not op_a or not op_b or not op_c or not op_d:
                    raise ValueError(f"Item {idx+1}: Missing one of option_a, option_b, option_c, or option_d.")
                if not corr or corr not in valid_options:
                    raise ValueError(f"Item {idx+1}: Invalid correct_option value. Must be A, B, C, or D.")

                questions_to_create.append(Question(
                    test_package=package,
                    subject=subj,
                    subtopic=subt,
                    question_text=qtxt,
                    option_a=op_a,
                    option_b=op_b,
                    option_c=op_c,
                    option_d=op_d,
                    correct_option=corr,
                    explanation=expl
                ))

            # Database atomic block to ensure zero dirty reads/writes
            with transaction.atomic():
                Question.objects.bulk_create(questions_to_create)

            success_count = len(questions_to_create)

        except json.JSONDecodeError as jde:
            error_message = f"Invalid JSON syntax structure: {jde}"
        except Exception as e:
            error_message = str(e)

    context = {
        'success_count': success_count,
        'error_message': error_message,
    }
    return render(request, 'cbt_app/import_questions.html', context)


def delete_session_view(request, session_id):
    """
    Deletes an existing completed or in-progress exam attempt,
    allowing the candidate to rewrite that specific mock test.
    This also cleans up any duplicate sessions for the same test.
    """
    session = get_object_or_404(ExamSession, id=session_id)
    
    # Delete all sessions for this specific mock test to fully reset it
    # in case the user has clicked "Launch" multiple times
    ExamSession.objects.filter(
        test_package=session.test_package
    ).delete()
    
    return redirect('dashboard')


def delete_mock_package_view(request, package_id):
    """
    Permanently deletes all questions associated with this specific mock test package.
    """
    package = get_object_or_404(TestPackage, id=package_id)
    package.delete()
    return redirect('dashboard')


from django.contrib.auth import login
from django.contrib.auth.models import User

def auto_admin_login(request):
    """
    Automatically logs in as a superuser and redirects to the Django admin panel.
    Creates a default 'admin' user with password 'admin' if no superuser exists.
    """
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    
    # Specify the backend since we are logging in manually without authentication
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    
    return redirect('/admin/')
