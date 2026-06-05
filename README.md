# CBT Exam Practice App

A simple, offline app to help you practice for any Computer-Based Test (CBT) like SSC, Banking, GATE, or PSU exams. It looks and feels exactly like a real exam center screen so you can practice your time management.

## How to Run It

You don't need any complex setup. Just download this folder to your computer and run the startup script.

**For Linux/Mac:**
Open your terminal inside the folder and type:
```bash
chmod +x run_project.sh
./run_project.sh
```

**For Windows:**
Open your command prompt inside the folder and type:
```cmd
python run_project.py
```

The script will automatically install everything it needs and open the app.

## How to Add Your Own Questions

By default, the app is empty. You can easily add your own questions to practice with:

1. Once the app is running, go to **http://127.0.0.1:8000/** in your browser.
2. Click on **Admin Control Panel** on the left menu (Username: `admin`, Password: `admin`).
3. Click on **Bulk Import Questions** on the bottom left.
4. Paste your questions there.

The app will automatically group your questions and create ready-to-play Mock Tests for you!
