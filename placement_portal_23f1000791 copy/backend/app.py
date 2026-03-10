from flask import Flask, request, jsonify
from models import db, User, Student, Company, Drive, Application
import datetime
import redis
import json
import tasks
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
cache = redis.Redis(host='localhost', port=6379, db=0)

db.init_app(app)


@app.route("/")
def home():
    return "Placement Portal Backend Running"


# ------------------------
# Student Registration
# ------------------------

@app.route("/register/student", methods=["POST"])
def register_student():
    data = request.json

    user = User(
        name=data["name"],
        email=data["email"],
        password=data["password"],
        role="student",
        approved=True
    )

    db.session.add(user)
    db.session.commit()

    student = Student(
        user_id=user.id,
        branch=data["branch"],
        cgpa=data["cgpa"],
        year=data["year"]
    )

    db.session.add(student)
    db.session.commit()

    return jsonify({"message": "Student registered successfully"})


# ------------------------
# Company Registration
# ------------------------

@app.route("/register/company", methods=["POST"])
def register_company():
    data = request.json

    user = User(
        name=data["name"],
        email=data["email"],
        password=data["password"],
        role="company",
        approved=False
    )

    db.session.add(user)
    db.session.commit()

    company = Company(
        user_id=user.id,
        company_name=data["company_name"],
        website=data["website"],
        hr_contact=data["hr_contact"]
    )

    db.session.add(company)
    db.session.commit()

    return jsonify({"message": "Company registered. Waiting for admin approval"})


# ------------------------
# Login
# ------------------------

@app.route("/login", methods=["POST"])
def login():
    data = request.json

    user = User.query.filter_by(email=data["email"], password=data["password"]).first()

    if not user:
        return jsonify({"message": "Invalid credentials"}), 401

    if not user.approved:
        return jsonify({"message": "Account not approved by admin"}), 403

    return jsonify({
        "message": "Login successful",
        "role": user.role,
        "user_id": user.id
    })


# ADMIN -- View Companies

@app.route("/admin/companies")
def view_companies():
    companies = User.query.filter_by(role="company").all()

    data = []
    for c in companies:
        data.append({
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "approved": c.approved
        })

    return jsonify(data)


# ADMIN -- Approve Company

@app.route("/admin/approve_company/<int:user_id>", methods=["POST"])
def approve_company(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"})

    user.approved = True
    db.session.commit()

    return jsonify({"message": "Company approved"})


# Company -- Create Drive

@app.route("/company/create_drive", methods=["POST"])
def create_drive():
    data = request.json

    drive = Drive(
        company_id=data["company_id"],
        title=data["title"],
        description=data["description"],
        branch=data["branch"],
        cgpa_required=data["cgpa_required"],
        deadline=data["deadline"],
        status="pending"
    )

    db.session.add(drive)
    db.session.commit()

    return jsonify({"message": "Drive created. Waiting for admin approval"})


# ADMIN -- View Drives

@app.route("/admin/drives")
def view_drives():
    drives = Drive.query.all()

    data = []

    for d in drives:
        data.append({
            "id": d.id,
            "title": d.title,
            "company_id": d.company_id,
            "status": d.status
        })

    return jsonify(data)


# ADMIN -- Approve Drive
@app.route("/admin/approve_drive/<int:drive_id>", methods=["POST"])
def approve_drive(drive_id):
    drive = Drive.query.get(drive_id)

    if not drive:
        return jsonify({"message": "Drive not found"})

    drive.status = "approved"
    db.session.commit()

    return jsonify({"message": "Drive approved"})


# Student — View Approved Drives
@app.route("/drives")
def get_drives():

    cached = cache.get("drives")

    if cached:
        return cached

    drives = Drive.query.filter_by(status="approved").all()

    data = []

    for d in drives:
        data.append({
            "id": d.id,
            "title": d.title,
            "description": d.description,
            "branch": d.branch,
            "cgpa_required": d.cgpa_required,
            "deadline": d.deadline
        })

    result = json.dumps(data)

    cache.setex("drives",60,result)

    return result


#  Student — Apply to Drive
@app.route("/apply", methods=["POST"])
def apply_drive():
    data = request.json

    existing = Application.query.filter_by(
        student_id=data["student_id"],
        drive_id=data["drive_id"]
    ).first()

    if existing:
        return jsonify({"message": "Already applied to this drive"})

    application = Application(
        student_id=data["student_id"],
        drive_id=data["drive_id"],
        status="applied",
        date=str(datetime.datetime.now())
    )

    db.session.add(application)
    db.session.commit()

    return jsonify({"message": "Application submitted"})



# Company — View Applications for a Drive

@app.route("/company/applications/<int:drive_id>")
def view_applications(drive_id):
    apps = Application.query.filter_by(drive_id=drive_id).all()

    data = []

    for a in apps:
        student = Student.query.filter_by(id=a.student_id).first()

        data.append({
            "application_id": a.id,
            "student_id": a.student_id,
            "status": a.status,
            "date": a.date
        })

    return jsonify(data)


# Company — Update Application Status
@app.route("/company/update_status", methods=["POST"])
def update_status():
    data = request.json

    app_obj = Application.query.get(data["application_id"])

    if not app_obj:
        return jsonify({"message": "Application not found"})

    app_obj.status = data["status"]
    db.session.commit()

    return jsonify({"message": "Application status updated"})




# Student — View My Applications
@app.route("/student/applications/<int:student_id>")
def student_applications(student_id):

    apps = Application.query.filter_by(student_id=student_id).all()

    data = []

    for a in apps:
        drive = Drive.query.get(a.drive_id)

        data.append({
            "drive_title": drive.title,
            "status": a.status,
            "date": a.date
        })

    return jsonify(data)




@app.route("/export_csv/<int:student_id>")
def export(student_id):

    tasks.export_csv.delay(student_id)

    return {"message":"CSV export started"}



# ------------------------
# Create Admin Automatically
# ------------------------

with app.app_context():
    db.create_all()

    admin = User.query.filter_by(email="admin@portal.com").first()

    if not admin:
        admin = User(
            name="Admin",
            email="admin@portal.com",
            password="admin123",
            role="admin",
            approved=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created")


if __name__ == "__main__":
    app.run(debug=True)