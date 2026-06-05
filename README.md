# CBT Mock Prep Engine

An advanced, offline-first Computer-Based Test (CBT) simulation engine designed to help candidates prepare for competitive exams. Built with a focus on replicating real-world exam environments, this engine is perfect for practicing time management, evaluating accuracy, and building exam-day confidence.

While originally designed with a 200-question structure in mind, the platform is highly adaptable and can be configured or populated with any question bank for any competitive exam (e.g., SSC, Banking, GATE, PSU exams, etc.).

## 🚀 Features

- **Hyper-Realistic CBT Interface:** A distraction-free, zero-flicker Single-Page Application (SPA) designed to exactly mimic professional test center software.
- **Dynamic Question Bank:** Includes a built-in admin dashboard allowing you to easily import your own MCQ questions via bulk JSON uploads.
- **Advanced Analytics Dashboard:** Track your progress over time with a performance matrix, complete with graphical history, accuracy per subject, and detailed score logs.
- **Sectional & Full Mock Tests:** The engine automatically builds full mock tests and sectional mock tests (Paper 1 / Paper 2) dynamically based on the total questions imported.
- **Complete Privacy & Offline Capable:** Runs entirely locally on your own machine. Your data, test history, and uploaded questions never leave your computer.
- **Beautiful UI/UX:** Built with Tailwind CSS, featuring smooth micro-animations, dynamic tabs, and a modern aesthetic with light/dark mode support.

## 📁 Project Structure

- **`APPLICATION/`**: Contains the core Django web application.
  - `cbt_app/`: The main application logic (views, models, templates).
  - `exam_project/`: Django configuration and routing.
- **`run_project.sh`**: Cross-platform startup script that automatically handles the environment and database.
- **`run_project.py`**: Python wrapper for environment consistency.

## 🛠️ Getting Started

Anyone can download and use this engine immediately. 

### Prerequisites
- Python 3.10+ installed on your system.

### Installation & Launch
1. **Clone or Download** this repository to your computer.
2. Open your terminal and navigate to the project directory.
3. Run the startup script:

   **Linux/macOS:**
   ```bash
   chmod +x run_project.sh
   ./run_project.sh
   ```
   **Windows:**
   ```cmd
   python run_project.py
   ```

The script will automatically set up a virtual environment, install the required dependencies (like Django and Tailwind), apply database migrations, and launch the server!

## 🔐 Default Access
Once the local server is running (usually at `http://127.0.0.1:8000/`), you can access the platform.

**Admin Control Panel:**
Navigate to `http://127.0.0.1:8000/admin/` or click the "Admin Control Panel" link in the sidebar to add questions manually.
- **Username:** `admin`
- **Password:** `admin` (or `admin123`)

*(Note: The system features an auto-login route for ease of use during local development).*

## 💡 How to Add Your Own Questions

1. Open the dashboard and click on **Bulk Import Questions** in the bottom left sidebar.
2. Paste your questions using the provided JSON format.
3. The engine will automatically generate new Mock Test packages based on the volume of questions you provide!

## 🤝 Open Source
This engine is completely open-source. Feel free to fork, modify, and tailor the interface to perfectly match the specific competitive exam you are preparing for!
