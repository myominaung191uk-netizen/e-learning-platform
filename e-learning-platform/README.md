# E-Learning Platform

A simple E-learning web application using HTML, CSS, JavaScript, Python Flask, and SQLite database.

## Features

- Student registration and login
- Admin login
- Add courses
- Add video lessons using video URLs
- Add quiz questions
- Students can view courses, watch lessons, take quizzes, and see results

## How to run

1. Open the project folder in VS Code or terminal.
2. Create a virtual environment:

```bash
python -m venv venv
```

3. Activate it:

Windows:

```bash
venv\Scripts\activate
```

Mac/Linux:

```bash
source venv/bin/activate
```

4. Install requirements:

```bash
pip install -r requirements.txt
```

5. Run the app:

```bash
python app.py
```

6. Open in browser:

```text
http://127.0.0.1:5000
```

## Admin account

Email: `admin@example.com`

Password: `admin123`

## Project structure

```text
e-learning-platform/
├── app.py
├── requirements.txt
├── README.md
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   └── uploads/
└── templates/
    ├── base.html
    ├── index.html
    ├── register.html
    ├── login.html
    ├── dashboard.html
    ├── course_detail.html
    ├── add_course.html
    ├── add_lesson.html
    ├── add_quiz.html
    ├── quiz.html
    └── result.html
```
