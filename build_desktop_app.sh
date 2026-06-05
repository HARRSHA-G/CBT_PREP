#!/bin/bash
set -e

echo "Activating virtual environment..."
source .venv/bin/activate

cd APPLICATION

echo "Building standalone desktop executable with PyInstaller..."
pyinstaller --name "CBT_Engine" \
            --onefile \
            --windowed \
            --add-data "cbt_app/templates:cbt_app/templates" \
            --add-data "exam_project:exam_project" \
            --add-data "manage.py:." \
            --hidden-import "django" \
            --hidden-import "django.contrib.admin" \
            --hidden-import "django.contrib.auth" \
            --hidden-import "django.contrib.contenttypes" \
            --hidden-import "django.contrib.sessions" \
            --hidden-import "django.contrib.messages" \
            --hidden-import "django.contrib.staticfiles" \
            --hidden-import "cbt_app" \
            cbt_desktop.py

echo "Build complete. Executable is located in APPLICATION/dist/CBT_Engine"
