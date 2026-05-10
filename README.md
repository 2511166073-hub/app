# RSD Scoring System

A Flask-based web application for tracking and managing member scores, meeting attendance, tasks, and evidence submissions for club/organization management.

## Features

- **User Management**: Registration, login, and role-based access control (admin/member)
- **Meeting Tracking**: Schedule and track CLB (Club) and Ban (Board) meetings
- **Attendance Management**: Record attendance with excuse handling and automatic score penalties
- **Task Assignment**: Create and track tasks with deadlines
- **Evidence Submission**: Members can submit evidence for points (ideas, initiatives, agenda, minutes, etc.)
- **Score Calculation**: Automatic score updates based on attendance, task completion, and evidence
- **Violation Tracking**: Track consecutive absences and apply penalties
- **Bonus Points**: Admin can grant bonus points for special contributions
- **Leaderboard**: Public ranking of members by score

## Project Structure

```
rsd_scoring/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── static/
│   ├── style.css         # Custom styles
│   └── script.js         # Client-side JavaScript
└── templates/
    ├── base.html         # Base template
    ├── index.html        # Public leaderboard
    ├── login.html        # Login page
    ├── register.html     # Registration page
    ├── admin.html        # Admin dashboard
    ├── admin_meetings.html
    ├── admin_tasks.html
    ├── admin_evidences.html
    ├── admin_bonus.html
    ├── admin_violations.html
    ├── admin_reports.html
    ├── attendance.html   # Attendance management
    ├── create_meeting.html
    ├── create_task.html
    ├── my_tasks.html     # Member task view
    ├── my_evidences.html # Member evidence view
    └── submit_evidence.html
```

## Installation

### Prerequisites

- Python 3.8+
- pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd rsd_scoring
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python rsd_scoring/app.py
```

4. Access the application at `http://localhost:5000`

## Configuration

The application uses the following default configuration in `app.py`:

- **SECRET_KEY**: `'rsd-scoring-secret-key-2024'` (change for production)
- **DATABASE_URI**: `'sqlite:///instance/rsd.db'` (SQLite database)

## Database Models

- **User**: Member information with score and violations
- **Group**: Member groups/clubs
- **Meeting**: Meeting schedules (CLB/Ban types)
- **Attendance**: Meeting attendance records
- **Task**: Assigned tasks with deadlines
- **Evidence**: Submitted evidence for review
- **Violation**: Rule violation records
- **BonusPoint**: Bonus point awards

## Scoring Rules

### Meeting Attendance
- **CLB Meeting**:
  - Unexcused absence: -2 points
  - Excused absence: -1 point
- **Ban Meeting**:
  - Unexcused absence: -1 point
  - Excused absence: No penalty

### Consecutive Absence Penalties
- More than 3 consecutive CLB absences: Warning triggered
- More than 2 consecutive Ban absences: Warning triggered

### Evidence Types
- Task completion
- Idea submissions
- Initiative projects
- Agenda preparation
- Minutes taking

## Usage

### For Members

1. **Register**: Create an account with your group affiliation
2. **View Leaderboard**: Check your ranking on the home page
3. **Submit Evidence**: Upload evidence for tasks, ideas, or initiatives
4. **View Tasks**: Check assigned tasks and deadlines
5. **Track Scores**: Monitor your score and violations

### For Admins

1. **Dashboard**: Overview of users, meetings, tasks, and pending reviews
2. **Manage Meetings**: Create meetings, assign agenda/minutes responsibilities
3. **Take Attendance**: Record attendance and approve excuses
4. **Manage Tasks**: Create and assign tasks to members
5. **Review Evidence**: Approve/reject evidence submissions and award points
6. **Grant Bonuses**: Award bonus points for special contributions
7. **Track Violations**: Monitor and manage member violations
8. **Generate Reports**: View scoring reports and analytics

## Security Notes

⚠️ **Before deploying to production:**

1. Change the `SECRET_KEY` to a secure random value
2. Use a production-ready database (PostgreSQL, MySQL)
3. Enable HTTPS
4. Implement proper password policies
5. Consider adding rate limiting and CSRF protection

## Technologies Used

- **Backend**: Flask, Flask-SQLAlchemy, Flask-Login
- **Database**: SQLite (development), configurable for production
- **Frontend**: HTML, CSS, JavaScript
- **Security**: Werkzeug password hashing

## License

This project is internal software for RSD scoring management.

## Support

For issues or questions, please contact the development team.
