from flask import Blueprint, request, jsonify
from .models import db, Employer, JobSeeker, JobOffer, Application
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

main = Blueprint('main', __name__)

@main.route('/register/employer', methods=['POST'])
def register_employer():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'])
    new_employer = Employer(username=data['username'], password=hashed_password)
    db.session.add(new_employer)
    db.session.commit()
    return jsonify({"message": "Employer registered successfully"}), 201

@main.route('/register/job_seeker', methods=['POST'])
def register_job_seeker():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'])
    new_job_seeker = JobSeeker(username=data['username'], password=hashed_password)
    db.session.add(new_job_seeker)
    db.session.commit()
    return jsonify({"message": "Job seeker registered successfully"}), 201


@main.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = Employer.query.filter_by(username=data['username']).first() or JobSeeker.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password, data['password']):
        # Créez un jeton avec une durée de validité de 1 heure
        user_type = 'employer' if isinstance(user, Employer) else 'job_seeker'
        access_token = create_access_token(identity={"id": user.id, "type": user_type}, expires_delta=timedelta(hours=24))
        return jsonify(access_token=access_token, user_type=user_type), 200
    return jsonify({"message": "Invalid credentials"}), 401


@main.route('/job_offers', methods=['POST'])
@jwt_required()
def create_job_offer():
    data = request.get_json()
    print(f"Received data: {data}")
    
    # Vérifiez que les critères sont fournis et qu'il y en a exactement 7
    criteria = data.get('criteria', {})
    if len(criteria) != 7:
        return jsonify({"message": "Exactly 7 criteria are required"}), 400

    # Vérifiez que chaque critère a un nom et un poids
    for criterion_name, weight in criteria.items():
        if not criterion_name or not isinstance(weight, (int, float)) or not (0 <= weight <= 1):
            return jsonify({"message": "Each criterion must have a name and a weight between 0 and 1"}), 400

    employer_id = get_jwt_identity()
    new_job_offer = JobOffer(
        title=data['title'],
        description=data['description'],
        criteria=criteria,
        employer_id=employer_id
    )
    db.session.add(new_job_offer)
    db.session.commit()
    return jsonify({"message": "Job offer created successfully"}), 201

@main.route('/job_offers', methods=['GET'])
def get_all_job_offers():
    job_offers = JobOffer.query.all()
    result = [
        {
            "id": job_offer.id,
            "title": job_offer.title,
            "description": job_offer.description,
            "criteria": job_offer.criteria,
            "employer_id": job_offer.employer_id,
        }
        for job_offer in job_offers
    ]
    return jsonify(result), 200

@main.route('/job_offers/<int:job_offer_id>', methods=['GET'])
def get_job_offer(job_offer_id):
    job_offer = JobOffer.query.get(job_offer_id)
    if not job_offer:
        return jsonify({"message": "Job offer not found"}), 404

    result = {
        "id": job_offer.id,
        "title": job_offer.title,
        "description": job_offer.description,
        "criteria": job_offer.criteria,
        "employer_id": job_offer.employer_id,
    }
    return jsonify(result), 200

@main.route('/apply', methods=['POST'])
@jwt_required()
def apply_for_job():
    data = request.get_json()
    job_seeker_id = get_jwt_identity()
    job_offer = JobOffer.query.get(data['job_offer_id'])
    if not job_offer:
        return jsonify({"message": "Job offer not found"}), 404

    # Here you would call Gemini to extract CV scores
    cv_score = 0  # Placeholder for actual CV score
    ga_result = 0  # Placeholder for GA result
    ahp_result = 0  # Placeholder for AHP result

    new_application = Application(job_seeker_id=job_seeker_id, job_offer_id=data['job_offer_id'], cv_score=cv_score, ga_result=ga_result, ahp_result=ahp_result)
    db.session.add(new_application)
    db.session.commit()
    return jsonify({"message": "Application submitted successfully"}), 201

@main.route('/analyze/<int:job_offer_id>', methods=['POST'])
@jwt_required()
def analyze_applications(job_offer_id):
    employer_id = get_jwt_identity()
    job_offer = JobOffer.query.get(job_offer_id)

    if not job_offer or job_offer.employer_id != employer_id:
        return jsonify({"message": "Job offer not found or unauthorized access"}), 404

    applications = Application.query.filter_by(job_offer_id=job_offer_id).all()

    # Extract CV scores using Gemini
    for application in applications:
        cv_content = get_cv_content(application.id)  # Implement this function
        cv_scores = extract_cv_scores(cv_content)

        # Run GA with the extracted scores
        ga_result = run_ga(job_offer.criteria, cv_scores)

        # Run AHP with GA results
        ahp_result = run_ahp(ga_result)

        # Update application with results
        application.cv_score = cv_scores
        application.ga_result = ga_result
        application.ahp_result = ahp_result

    db.session.commit()
    return jsonify({"message": "Analysis completed successfully"}), 200
