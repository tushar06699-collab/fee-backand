from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()

# --------------------------------------------------------
# STUDENT MODEL
# --------------------------------------------------------
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    father = db.Column(db.String(100))
    class_name = db.Column(db.String(50))
    roll = db.Column(db.String(20))
    previous_due = db.Column(db.Integer, default=0)
    advance = db.Column(db.Integer, default=0)
    months = db.Column(db.JSON)   # store monthly fee structure

    # ❌ REMOVE THIS LINE
    # receipts = db.relationship("Receipt", backref="student", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "father": self.father,
            "class_name": self.class_name,
            "roll": self.roll,
            "previous_due": self.previous_due,
            "advance": self.advance,
            "months": self.months
        }


# --------------------------------------------------------
# FINAL + ONLY Receipt MODEL
# --------------------------------------------------------
class Receipt(db.Model):
    __tablename__ = "receipt"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer,db.ForeignKey("student.id"), nullable=True)

    name = db.Column(db.String(100))
    father = db.Column(db.String(100))
    class_name = db.Column(db.String(20))
    roll = db.Column(db.String(20))

    date = db.Column(db.String(50))

    total_paid = db.Column(db.Integer, default=0)
    total_due = db.Column(db.Integer, default=0)
    advance = db.Column(db.Integer, default=0)

    months_json = db.Column(db.Text)

    receipt_key = db.Column(db.String(200), unique=True)


    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "name": self.name,
            "father": self.father,
            "class_name": self.class_name,
            "roll": self.roll,
            "date": self.date,
            "total_paid": self.total_paid,
            "total_due": self.total_due,
            "advance": self.advance,
            "months": json.loads(self.months_json) if self.months_json else []
        }

class FeeStructure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(50), unique=True)
    monthly_fee = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "class_name": self.class_name,
            "monthly_fee": self.monthly_fee
        }
