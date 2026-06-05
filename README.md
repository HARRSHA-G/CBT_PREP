# CIL MT Practice Engine

This is a CBT (Computer Based Test) practice engine specifically designed for Coal India Limited (CIL) Management Trainee (MT) exams.

## Structure
- **APPLICATION/**: Contains the main Django web application.
  - `cbt_app`: The core Django application.
  - `exam_project`: The Django project configuration.
  - `run_project.sh`: Startup script for the portal.
- **DOCUMENTATION/**: Contains project documentation.
- `sample_data.json`: Example question data.

## Getting Started

To run the application:
```bash
cd APPLICATION
./run_project.sh
```

## Features
- Complete 200 marks structure.
- Auto database seeding if questions are missing.
- Dynamic interface with Dark Mode by default.
