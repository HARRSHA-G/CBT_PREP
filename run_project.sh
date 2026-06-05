#!/bin/bash
echo "========================================================================="
echo "              COAL INDIA LIMITED MT SYSTEMS PRACTICE ENGINE              "
echo "========================================================================="
echo "   [Theme]: Light Mode Default (Obsidian & Orange Accents)"
echo "   [Offline]: Enabled (SQLite Local Database)"
echo "   [Structure]: Dynamic Mock Test Engine"
echo "-------------------------------------------------------------------------"

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "Python is not installed. Please install Python to run this project."
    exit 1
fi

if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

PORT=${PORT:-8000}
ADMIN_USER=${ADMIN_USER:-admin}
ADMIN_PASS=${ADMIN_PASS:-admin123}
ADMIN_EMAIL=${ADMIN_EMAIL:-admin@example.com}

cd APPLICATION || exit

echo "  ⚙️ Checking SQLite database schema migrations..."
$PYTHON_CMD manage.py migrate

Q_COUNT=$($PYTHON_CMD -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_project.settings'); django.setup(); from cbt_app.models import Question; print(Question.objects.count())" 2>/dev/null)

if [ "$Q_COUNT" = "0" ] || [ -z "$Q_COUNT" ]; then
    echo "  📥 No questions detected. Automatically seeding the question bank..."
    $PYTHON_CMD manage.py seed_questions
else
    echo "  📚 Database verified: $Q_COUNT high-quality competitive questions pre-loaded."
fi

SU_EXISTS=$($PYTHON_CMD -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_project.settings'); django.setup(); from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(username='$ADMIN_USER').exists())" 2>/dev/null)

if [ "$SU_EXISTS" != "True" ]; then
    echo "  👤 Creating default administrator credentials..."
    $PYTHON_CMD -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_project.settings'); django.setup(); from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('$ADMIN_USER', '$ADMIN_EMAIL', '$ADMIN_PASS')" 2>/dev/null
fi

echo "-------------------------------------------------------------------------"
echo "  🚀 Starting local offline server..."
echo "  🌐 Dashboard URL: http://127.0.0.1:$PORT/"
echo "  🔐 Control Panel: http://127.0.0.1:$PORT/admin/"
echo "  🔑 Credentials  : Username: $ADMIN_USER | Password: $ADMIN_PASS"
echo "-------------------------------------------------------------------------"
echo "Press CTRL+C to terminate the session."
echo "========================================================================="

# Try to clear port
fuser -k $PORT/tcp 2>/dev/null || lsof -t -i:$PORT | xargs kill -9 2>/dev/null || true

$PYTHON_CMD manage.py runserver "0.0.0.0:$PORT"
