from . import db
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

class Employer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    job_offers = db.relationship('JobOffer', backref='employer', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    


class JobSeeker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    applications = db.relationship('Application', backref='job_seeker', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    

class JobOffer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    criteria = db.Column(db.JSON, nullable=False)
    employer_id = db.Column(db.Integer, db.ForeignKey('employer.id'), nullable=False)
    applications = db.relationship('Application', backref='job_offer', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_seeker_id = db.Column(db.Integer, db.ForeignKey('job_seeker.id'), nullable=False)
    job_offer_id = db.Column(db.Integer, db.ForeignKey('job_offer.id'), nullable=False)
    cv_score = db.Column(db.Float, nullable=False)
    ga_result = db.Column(db.Float, nullable=False)
    ahp_result = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
