import sys
import os
sys.path.append(os.path.dirname(__file__))

from celery import Celery
import csv

from models import Application, Drive

celery = Celery(
    "tasks",
    broker="redis://localhost:6379/0"
)

@celery.task
def export_csv(student_id):

    # Import inside function to avoid Celery loading Flask as the app
    from app import app

    with app.app_context():

        apps = Application.query.filter_by(student_id=student_id).all()

        filename = f"applications_{student_id}.csv"

        with open(filename, "w") as file:
            writer = csv.writer(file)
            writer.writerow(["Drive", "Status", "Date"])

            for a in apps:
                drive = Drive.query.get(a.drive_id)

                writer.writerow([
                    drive.title,
                    a.status,
                    a.date
                ])

        print("CSV Export Complete")


@celery.task
def daily_reminder():
    print("Sending reminders for upcoming deadlines")


@celery.task
def monthly_report():
    print("Generating monthly placement report")