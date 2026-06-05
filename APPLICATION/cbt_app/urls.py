"""
CIL MT CBT App — URL Configuration
=====================================
All routes for the Coal India Limited MT CBT Practice Engine.

  Page                       | URL                                   | Name
  -------------------------- | ------------------------------------- | --------------------------
  Practice Hub Dashboard     | /                                     | dashboard
  ── Full Mock Tests ──────────────────────────────────────────────────────────
  Full Mock Test 1 (200 MCQ) | /mock/full/1/                         | start_full_mock_1
  Full Mock Test 2 (200 MCQ) | /mock/full/2/                         | start_full_mock_2
  Full Mock Test 3 (200 MCQ) | /mock/full/3/                         | start_full_mock_3
  ── Paper 1 Sectional ────────────────────────────────────────────────────────
  Paper 1 Mock Test 1        | /mock/paper1/1/                       | start_p1_mock_1
  Paper 1 Mock Test 2        | /mock/paper1/2/                       | start_p1_mock_2
  Paper 1 Mock Test 3        | /mock/paper1/3/                       | start_p1_mock_3
  ── Paper 2 Sectional ────────────────────────────────────────────────────────
  Paper 2 Mock Test 1        | /mock/paper2/1/                       | start_p2_mock_1
  Paper 2 Mock Test 2        | /mock/paper2/2/                       | start_p2_mock_2
  Paper 2 Mock Test 3        | /mock/paper2/3/                       | start_p2_mock_3
  ── Session Pages ────────────────────────────────────────────────────────────
  Exam Room (SPA Engine)     | /exam/<uuid>/                         | exam_view
  Exam Results Report        | /result/<uuid>/                       | result_view
  Delete / Reset Attempt     | /delete-session/<uuid>/               | delete_session
  ── Admin ────────────────────────────────────────────────────────────────────
  Bulk MCQ Import Console    | /import/                              | import_questions
  ── Internal APIs ────────────────────────────────────────────────────────────
  [API] Auto-Save Progress   | /api/save_progress/<uuid>/            | save_progress_api
  [API] Final Submit Exam    | /api/submit_exam/<uuid>/              | submit_exam_api
"""

from django.urls import path
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [

    # ── Dashboard ─────────────────────────────────────────────────────────────
    path('', RedirectView.as_view(pattern_name='dashboard', permanent=False), name='root_redirect'),
    path('practice-workspaces/', views.dashboard_view, name='dashboard'),
    path('profile/', views.candidate_profile_view, name='candidate_profile'),

    # ── Mock Test Launches (Dynamic Path) ─────────────────────────────────────
    # Matches URLs like /mock/uuid/
    path('mock/<uuid:package_id>/', views.start_session_view, name='start_mock'),
    path('mock/<uuid:package_id>/delete-package/', views.delete_mock_package_view, name='delete_mock_package'),

    # ── Session Pages ─────────────────────────────────────────────────────────
    path('exam/<uuid:session_id>/', views.exam_view, name='exam_view'),
    path('result/<uuid:session_id>/', views.result_view, name='result_view'),
    path('delete-session/<uuid:session_id>/', views.delete_session_view, name='delete_session'),

    # ── Admin / Seeding ───────────────────────────────────────────────────────
    path('import/', views.import_questions_view, name='import_questions'),
    path('auto-admin/', views.auto_admin_login, name='auto_admin_login'),

    # ── Internal JSON APIs ────────────────────────────────────────────────────
    path('api/save_progress/<uuid:session_id>/', views.save_progress_api, name='save_progress_api'),
    path('api/submit_exam/<uuid:session_id>/', views.submit_exam_api, name='submit_exam_api'),

]
