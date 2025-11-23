from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, Student, Receipt, FeeStructure   # ✔ FIXED – Added FeeStructure
import json

app = Flask(__name__)

# FULL CORS FIX
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True
)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///school.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()


# -------------------------------------------------------
# HEALTH CHECK
# -------------------------------------------------------
@app.route("/health")
def health():
    return jsonify({"status": "Backend is running"})

@app.route("/")
def home():
    return {"status": "Backend Running", "success": True}



# -------------------------------------------------------
# ADD STUDENT
# -------------------------------------------------------
@app.route("/student/add", methods=["POST"])
def add_student():
    data = request.get_json()

    student = Student(
        name=data["name"],
        father=data["father"],
        class_name=data["class_name"],
        roll=data["roll"],
        previous_due=data.get("previous_due", 0),
        advance=data.get("advance", 0),
        months=data.get("months", {})
    )
    db.session.add(student)
    db.session.commit()

    return jsonify({"success": True, "student": student.to_dict()})


# -------------------------------------------------------
# GET ALL STUDENTS
# -------------------------------------------------------
@app.route("/students", methods=["GET"])
def get_students():
    students = Student.query.all()

    return jsonify({
        "success": True,
        "students": [s.to_dict() for s in students]
    })


# -------------------------------------------------------
# GET SINGLE STUDENT
# -------------------------------------------------------
@app.route("/student/<class_name>/<roll>", methods=["GET"])
def get_single_student(class_name, roll):

    student = Student.query.filter_by(class_name=class_name, roll=roll).first()

    if not student:
        return jsonify({"success": False, "message": "Student not found"}), 404

    return jsonify({"success": True, "student": student.to_dict()})


# -------------------------------------------------------
# UPDATE STUDENT
# -------------------------------------------------------
@app.route("/update_student", methods=["POST", "OPTIONS"])
def update_student():

    # Handle CORS preflight
    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200

    data = request.get_json()

    class_name = data.get("class")
    roll = data.get("roll")
    student_data = data.get("student")

    student = Student.query.filter_by(class_name=class_name, roll=roll).first()

    if not student:
        return jsonify({"success": False, "message": "Student not found"}), 404

    student.name = student_data.get("name", student.name)
    student.father = student_data.get("father", student.father)
    student.previous_due = student_data.get("previous_due", student.previous_due)
    student.advance = student_data.get("advance", student.advance)
    student.months = student_data.get("months", student.months)

    db.session.commit()

    return jsonify({"success": True, "message": "Student updated successfully"})


# -------------------------------------------------------
# ADD RECEIPT
# -------------------------------------------------------
@app.route("/receipt/add", methods=["POST"])
def add_receipt():
    try:
        data = request.json

        required = ["name", "father", "class", "roll", "date",
                    "totalPaid", "totalDue", "advance", "months", "receiptKey"]

        for f in required:
            if f not in data:
                return jsonify({"success": False, "message": f"Missing field: {f}"})

        # Block duplicate
        exists = Receipt.query.filter_by(receipt_key=data["receiptKey"]).first()
        if exists:
            return jsonify({"success": False, "message": "Duplicate receipt ignored"})

        new_r = Receipt(
            student_id=None,
            name=data["name"],
            father=data["father"],
            class_name=data["class"],
            roll=data["roll"],
            date=data["date"],
            total_paid=data["totalPaid"],
            total_due=data["totalDue"],
            advance=data["advance"],
            months_json=json.dumps(data["months"]),
            receipt_key=data["receiptKey"]
        )

        db.session.add(new_r)
        db.session.commit()

        return jsonify({"success": True, "message": "Receipt saved"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


# -------------------------------------------------------
# RECEIPT HISTORY
# -------------------------------------------------------
@app.route("/receipt/history", methods=["GET"])
def receipt_history():
    try:
        receipts = Receipt.query.order_by(Receipt.id.desc()).all()

        history = []
        for r in receipts:
            history.append({
                "id": r.id,
                "student_id": r.student_id,
                "name": r.name,
                "father": r.father,
                "class": r.class_name,
                "roll": r.roll,
                "date": r.date,
                "totalPaid": r.total_paid,
                "totalDue": r.total_due,
                "advance": r.advance,
                "months": json.loads(r.months_json)
            })

        return jsonify({"success": True, "history": history})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


# -------------------------------------------------------
# GET ALL RECEIPTS
# -------------------------------------------------------
@app.route("/receipts/all")
def all_receipts():
    receipts = Receipt.query.all()
    return jsonify({
        "success": True,
        "receipts": [r.to_dict() for r in receipts]
    })


@app.route("/receipt/all", methods=["GET"])
def get_all_receipts():
    receipts = Receipt.query.all()

    data = []
    for r in receipts:
        data.append({
            "id": r.id,
            "student_id": r.student_id,
            "name": r.name,
            "father": r.father,
            "class": r.class_name,
            "roll": r.roll,
            "date": r.date,
            "totalPaid": r.total_paid,
            "totalDue": r.total_due,
            "advance": r.advance,
            "months": json.loads(r.months_json)
        })

    return jsonify({"success": True, "receipts": data})


# -------------------------------------------------------
# DELETE RECEIPTS
# -------------------------------------------------------
@app.route("/receipt/delete/<int:id>", methods=["DELETE"])
def delete_receipt(id):
    r = Receipt.query.get(id)
    if not r:
        return jsonify({"success": False, "message": "Receipt not found"}), 404

    db.session.delete(r)
    db.session.commit()

    return jsonify({"success": True, "message": "Receipt deleted"})


@app.route("/receipt/delete_all", methods=["DELETE"])
def delete_all_receipts():
    try:
        num_rows = db.session.query(Receipt).delete()
        db.session.commit()

        return jsonify({"success": True, "message": f"Deleted {num_rows} receipts"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


# -------------------------------------------------------
# DELETE STUDENTS
# -------------------------------------------------------
@app.route("/student/delete_class", methods=["POST", "OPTIONS"])
def delete_class_students():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.json
    class_name = data.get("class")

    if not class_name:
        return jsonify({"success": False, "message": "Missing class"}), 400

    students = Student.query.filter_by(class_name=class_name).all()

    if not students:
        return jsonify({"success": False, "message": "No students in this class"}), 404

    for s in students:
        Receipt.query.filter_by(student_id=s.id).delete()

    Student.query.filter_by(class_name=class_name).delete()
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"All students in {class_name} deleted"
    }), 200


@app.route("/student/delete", methods=["POST", "OPTIONS"])
def delete_student():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.json
    class_name = data.get("class")
    roll = data.get("roll")

    if not class_name or not roll:
        return jsonify({"success": False, "message": "Missing class or roll"}), 400

    student = Student.query.filter_by(class_name=class_name, roll=roll).first()

    if not student:
        return jsonify({"success": False, "message": "Student not found"}), 404

    Receipt.query.filter_by(student_id=student.id).delete()
    db.session.delete(student)
    db.session.commit()

    return jsonify({"success": True, "message": "Student deleted"}), 200


# -------------------------------------------------------
# FEES: SETUP DEFAULT VALUES
# -------------------------------------------------------
@app.route("/fees/setup_defaults")
def setup_default_fees():
    default_fees = {
        "Nursery": 1200,
        "LKG": 1300,
        "UKG": 1300,
        "1st": 1300,
        "2nd": 1300,
        "3rd": 1300,
        "4th": 1400,
        "5th": 1400,
        "6th": 1500,
        "7th": 1500,
        "8th": 1700,
        "9th": 1900,
        "10th": 1900,
        "11th_Medical": 2200,
        "11th_Commerce": 2100,
        "11th_Art": 2100,
        "12th_Medical": 2200,
        "12th_Commerce": 2100,
        "12th_Art": 2100
    }

    for cls, fee in default_fees.items():
        row = FeeStructure.query.filter_by(class_name=cls).first()
        if not row:
            db.session.add(FeeStructure(class_name=cls, monthly_fee=fee))

    db.session.commit()

    return jsonify({"success": True, "message": "Default fees inserted"})



# -------------------------------------------------------
# FEES: GET
# -------------------------------------------------------
@app.route("/fees/get", methods=["GET"])
def get_fees():
    fees = FeeStructure.query.all()
    data = [f.to_dict() for f in fees]
    return jsonify({"success": True, "fees": data})


# -------------------------------------------------------
# FEES: UPDATE
# -------------------------------------------------------
@app.route("/fees/update", methods=["POST"])
def update_fee():
    data = request.json
    class_name = data.get("class_name")
    monthly_fee = data.get("monthly_fee")

    if not class_name:
        return jsonify({"success": False, "message": "Missing class name"})

    fee = FeeStructure.query.filter_by(class_name=class_name).first()

    if not fee:
        fee = FeeStructure(class_name=class_name, monthly_fee=monthly_fee)
        db.session.add(fee)
    else:
        fee.monthly_fee = monthly_fee

    db.session.commit()

    return jsonify({"success": True, "message": "Fee Updated"})

@app.route("/fees/reset")
def reset_fees():
    try:
        num = db.session.query(FeeStructure).delete()
        db.session.commit()
        return jsonify({"success": True, "message": f"Deleted {num} fee rows"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# -------------------------------------------------------
# START SERVER
# -------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
