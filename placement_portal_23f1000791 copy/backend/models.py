from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    role = db.Column(db.String(20))
    approved = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    branch = db.Column(db.String(50))
    cgpa = db.Column(db.Float)
    year = db.Column(db.Integer)
    resume = db.Column(db.String(200))


class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    company_name = db.Column(db.String(100))
    website = db.Column(db.String(200))
    hr_contact = db.Column(db.String(100))


class Drive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    branch = db.Column(db.String(50))
    cgpa_required = db.Column(db.Float)
    deadline = db.Column(db.String(50))
    status = db.Column(db.String(20), default="pending")


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer)
    drive_id = db.Column(db.Integer)
    status = db.Column(db.String(20), default="applied")
    date = db.Column(db.String(50))