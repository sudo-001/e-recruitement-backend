import os
from flask import Blueprint, request, jsonify
import numpy as np

from app.utils import generate_genome, run_ahp, run_genetic_algorithm
from .models import db, Employer, JobSeeker, JobOffer, Application
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from werkzeug.utils import secure_filename

main = Blueprint('main', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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


@main.route('/applications', methods=['GET'])
@jwt_required()
def get_applications():
    user_identity = get_jwt_identity()
    job_seeker_id = user_identity["id"]

    applications = Application.query.filter_by(job_seeker_id=job_seeker_id).all()
    if not applications:
        return jsonify({"message": "No applications found"}), 404

    result = [
        {
            "id": app.id,
            "job_offer_id": app.job_offer_id,
            "cv_score": app.cv_score,
            "ga_result": app.ga_result,
            "ahp_result": app.ahp_result
        }
        for app in applications
    ]
    return jsonify(result), 200


@main.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    user = Employer.query.get(user_id) or JobSeeker.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    user_info = {
        "id": user.id,
        "username": user.username,
        "type": "employer" if isinstance(user, Employer) else "job_seeker",
    }

    return jsonify(user_info), 200


@main.route('/job_offers/<int:job_offer_id>', methods=['DELETE'])
@jwt_required()
def delete_job_offer(job_offer_id):
    employer_identity = get_jwt_identity()
    job_offer = JobOffer.query.get(job_offer_id)

    if not job_offer:
        return jsonify({"message": "Job offer not found"}), 404

    if job_offer.employer_id != employer_identity["id"]:
        return jsonify({"message": "Unauthorized to delete this job offer"}), 403

    db.session.delete(job_offer)
    db.session.commit()
    return jsonify({"message": "Job offer deleted successfully"}), 200




@main.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = Employer.query.filter_by(username=data['username']).first() or JobSeeker.query.filter_by(username=data['username']).first()
    print("User:", data)
    if user and check_password_hash(user.password, data['password']):
        # Créez un jeton avec une durée de validité de 1 heure
        user_type = 'employer' if isinstance(user, Employer) else 'job_seeker'
        access_token = create_access_token(identity={"id": user.id, "type": user_type}, expires_delta=timedelta(hours=24))
        return jsonify(access_token=access_token, user_id=user.id), 200
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

    employer_identity = get_jwt_identity()
    new_job_offer = JobOffer(
        title=data['title'],
        description=data['description'],
        criteria=criteria,
        employer_id=employer_identity['id']
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
    user_identity = get_jwt_identity()
    job_seeker_id = user_identity["id"]

    if 'job_offer_id' not in request.form or 'cv' not in request.files:
        return jsonify({"message": "Missing job_offer_id or CV file"}), 400

    job_offer_id = int(request.form['job_offer_id'])
    cv_file = request.files['cv']

    if not allowed_file(cv_file.filename):
        return jsonify({"message": "Invalid file type"}), 400

    job_offer = JobOffer.query.get(job_offer_id)
    if not job_offer:
        return jsonify({"message": "Job offer not found"}), 404

    existing = Application.query.filter_by(job_seeker_id=job_seeker_id, job_offer_id=job_offer_id).first()
    if existing:
        return jsonify({"message": "Already applied to this job offer"}), 409

    # Sauvegarde du CV
    filename = secure_filename(f"user_{job_seeker_id}_job_{job_offer_id}_" + cv_file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    cv_file.save(file_path)

    # Appel de ta fonction
    genome = generate_genome(cv_path=file_path, criteria_dict=job_offer.criteria)

    # Placeholder pour les autres scores
    cv_score = 0
    ga_result = 0
    ahp_result = 0

    # Création de l'application
    new_application = Application(
        job_seeker_id=job_seeker_id,
        job_offer_id=job_offer_id,
        cv_score=cv_score,
        ga_result=ga_result,
        ahp_result=ahp_result,
        genome=genome
    )

    db.session.add(new_application)
    db.session.commit()

    return jsonify({"message": "Application submitted successfully"}), 201


@main.route('/analyze/<int:job_offer_id>', methods=['POST'])
@jwt_required()
def analyze_job_offer(job_offer_id):
    job = JobOffer.query.get(job_offer_id)
    if not job:
        return jsonify({'message': 'Job offer not found'}), 404

    applications = Application.query.filter_by(job_offer_id=job_offer_id).all()
    if not applications:
        return jsonify({'message': 'No applications for this job offer'}), 404

    # Récupération des critères et poids depuis l'offre d'emploi
    criteria = job.criteria
    if not criteria:
        return jsonify({'message': 'No criteria defined for this job offer'}), 400

    # Création de la population et du mapping genome -> application
    genome_to_application = {}
    population = []

    for app in applications:
        genome = app.genome.get(str(job_offer_id)) if isinstance(app.genome, dict) else None
        if genome:
            population.append(genome)
            genome_to_application[tuple(genome)] = app

    if not population:
        return jsonify({'message': 'No genomes available for applicants'}), 400

    # Lancer l'algorithme génétique
    skills = list(criteria.keys())
    weights = np.array(list(criteria.values()))
    finalists, _ = run_genetic_algorithm(skills, weights, population)

    # Appliquer AHP sur les finalistes
    final_scores = run_ahp(finalists, skills, weights)

    # Construire la réponse avec informations utilisateurs
    response = {
        "job_offer_id": job_offer_id,
        "finalists_with_ahp": []
    }

    for i, candidate in enumerate(finalists):
        app_obj = genome_to_application.get(tuple(candidate))
        user = app_obj.user if app_obj else None

        response["finalists_with_ahp"].append({
            "candidate": candidate,
            "ahp_score": round(final_scores[f"C{i+1}"], 4),
            "user": {
                "id": user.id if user else None,
                "firstname": user.firstname if user else "",
                "lastname": user.lastname if user else "",
                "email": user.email if user else ""
            }
        })

    return jsonify(response), 200

@main.route('/job_offers/<int:job_offer_id>/applications', methods=['GET'])
@jwt_required()
def get_candidates_for_job(job_offer_id):
    employer_identity = get_jwt_identity()

    # Vérifie si l'offre d'emploi appartient à l'employeur connecté
    job_offer = JobOffer.query.get(job_offer_id)
    if not job_offer:
        return jsonify({"message": "Job offer not found"}), 404

    if job_offer.employer_id != employer_identity["id"]:
        return jsonify({"message": "Unauthorized access to this job offer"}), 403

    # Récupérer toutes les candidatures pour cette offre
    applications = Application.query.filter_by(job_offer_id=job_offer_id).all()
    if not applications:
        return jsonify({"message": "No applications found for this job offer"}), 404

    # Construction de la réponse avec les infos du candidat
    result = []
    for app in applications:
        job_seeker = JobSeeker.query.get(app.job_seeker_id)
        result.append({
            "application_id": app.id,
            "job_seeker_id": job_seeker.id,
            "job_seeker_username": job_seeker.username,
            "cv_score": app.cv_score,
            "ga_result": app.ga_result,
            "ahp_result": app.ahp_result,
            "genome": app.genome
        })

    return jsonify(result), 200