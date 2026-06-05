import uuid
from django.db import models


class TestPackage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    category = models.CharField(max_length=20, default='ALL') # ALL, PAPER1, PAPER2
    marks_per_correct = models.FloatField(default=1.0)
    negative_marks = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.category})"

class Question(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test_package = models.ForeignKey(TestPackage, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    subject = models.CharField(max_length=100)
    subtopic = models.CharField(max_length=255)
    question_text = models.TextField()
    option_a = models.TextField()
    option_b = models.TextField()
    option_c = models.TextField()
    option_d = models.TextField()
    correct_option = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    explanation = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"[{self.subject}] {self.question_text[:60]}..."

class ExamSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    total_score = models.FloatField(null=True, blank=True)
    # A JSONField to preserve user choice mapping snapshot records, e.g.:
    # {
    #   "question_id": {
    #     "answer": "A",
    #     "flagged": true,
    #     "visited": true
    #   }
    # }
    user_answers = models.JSONField(default=dict, blank=True)
    # Store the exact order of questions for this test session to maintain consistency
    question_order = models.JSONField(default=list, blank=True)
    is_completed = models.BooleanField(default=False)
    test_package = models.ForeignKey(TestPackage, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        status = "Completed" if self.is_completed else "In Progress"
        package_name = self.test_package.name if self.test_package else 'Unknown'
        return f"Session {str(self.id)[:8]}... ({package_name}) - Score: {self.total_score}"
