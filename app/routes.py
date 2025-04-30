import json
import os
import random
from flask import Blueprint, request, jsonify
import numpy as np

from app.services import run_genetic_algorithm_and_ahp
from app.utils import generate_genome 
# genetic_algorithm, run_ahp
from .models import db, Employer, JobSeeker, JobOffer, Application
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
from werkzeug.utils import secure_filename

main = Blueprint('main', __name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

############# POPULATION ROUTES #############
# Liste des critères définis par l'employeur
criteria_keys = [
    "Ability to work in different business units",
    "Past experience",
    "Team player",
    "Fluency in a foreign language",
    "Strategic thinking",
    "Oral communication skills",
    "Computer skills"
]

@main.route('/populate_application', methods=['GET'])
def insert_applications():
    data = [
        (1, 1, 67.32, 49.75, 82.15, '[23.5, 12.33, 41.77, 8.66, 44.12, 36.9, 2.47]'),
        (2, 2, 91.52, 78.95, 72.23, '[47.88, 2.99, 15.1, 36.87, 25.84, 46.49, 18.62]'),
        (3, 3, 55.19, 68.42, 39.73, '[5.02, 40.65, 49.88, 6.87, 29.9, 17.66, 3.14]'),
        (4, 4, 74.66, 59.12, 45.63, '[33.75, 1.89, 25.78, 47.3, 11.92, 28.6, 22.8]'),
        (5, 5, 62.11, 37.44, 64.77, '[18.42, 31.0, 38.89, 24.9, 42.57, 9.87, 13.33]'),
        (6, 6, 48.91, 42.23, 51.16, '[8.74, 44.1, 6.67, 17.35, 38.2, 31.04, 25.9]'),
        (7, 7, 89.22, 91.03, 73.41, '[50.0, 18.65, 12.97, 20.24, 35.75, 26.11, 39.48]'),
        (8, 8, 77.88, 53.68, 59.92, '[10.84, 23.91, 45.83, 32.67, 21.37, 7.77, 42.03]')
    ]

    created_at = datetime.fromisoformat("2025-04-12T10:30:00+00:00")

    for js_id, jo_id, cv, ga, ahp, genome_str in data:
        app_obj = Application(
            job_seeker_id=js_id,
            job_offer_id=jo_id,
            cv_score=cv,
            ga_result=ga,
            ahp_result=ahp,
            genome=json.loads(genome_str),  # on convertit la string JSON en list Python
            created_at=created_at
        )
        db.session.add(app_obj)

    db.session.commit()
    return "Applications ajoutées avec succès 🚀"


@main.route('/register_bulk_job_seekers', methods=['POST'])
def register_bulk_job_seekers():
    # Nombre total visé
    TARGET_COUNT = 200
    
    # Compter combien de JobSeekers il y a déjà
    current_count = JobSeeker.query.count()
    needed = TARGET_COUNT - current_count

    if needed <= 0:
        return jsonify({"message": "Already have 200 or more job seekers."}), 200

    for i in range(current_count + 1, TARGET_COUNT + 1):
        username = f"jobSeeker{i}"
        password = generate_password_hash(f"password{i}")  # tu génères un password sécurisé
        new_job_seeker = JobSeeker(username=username, password=password)
        db.session.add(new_job_seeker)

    db.session.commit()
    
    return jsonify({"message": f"{needed} job seekers created successfully."}), 201

@main.route('/register_bulk_applications', methods=['POST'])
def register_bulk_applications():
    # Récupérer tous les job seekers
    job_seekers = JobSeeker.query.all()

    # Récupérer un JobOffer spécifique (ici tu peux ajuster pour que ce soit dynamique)
    job_offer = JobOffer.query.first()  # Ici je prends le premier job offer

    if not job_seekers or not job_offer:
        return jsonify({"message": "Job seekers or job offer not found."}), 404

    # Fonction pour générer un genome valide avec 7 valeurs entre 0 et 50
    def generate_valid_genome():
        genome = [random.randint(0, 50) for _ in range(7)]
        return genome

    # Créer les applications pour chaque job seeker
    applications = []
    for seeker in job_seekers:
        genome = generate_valid_genome()
        cv_score = random.uniform(0, 10)  # Exemple de score aléatoire pour le CV
        ga_result = random.uniform(0, 10)  # Exemple de score pour GA
        ahp_result = random.uniform(0, 10)  # Exemple de score AHP

        new_application = Application(
            job_seeker_id=seeker.id,
            job_offer_id=job_offer.id,
            cv_score=cv_score,
            ga_result=ga_result,
            ahp_result=ahp_result,
            genome=genome,  # Ajout du genome sous forme de liste de 7 valeurs
            created_at=datetime.utcnow()
        )
        applications.append(new_application)

    # Ajouter toutes les applications à la base de données
    db.session.add_all(applications)
    db.session.commit()

    return jsonify({"message": f"{len(applications)} applications created successfully."}), 201

############## USER ROUTES #############

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
    # Get applications for each job_offer
    
    def get_number_applicants(job_offer_id):
        # Vérifie si l'offre d'emploi appartient à l'employeur connecté
        job_offer = JobOffer.query.get(job_offer_id)
        if not job_offer:
            return jsonify({"message": "Job offer not found"}), 404


        # Récupérer toutes les candidatures pour cette offre
        applications = Application.query.filter_by(job_offer_id=job_offer_id).all()
        if not applications:
            return 0
        
        return len(applications)
    
    
    result = [
        {
            "id": job_offer.id,
            "title": job_offer.title,
            "description": job_offer.description,
            "criteria": job_offer.criteria,
            "employer_id": job_offer.employer_id,
            "number_applications": get_number_applicants(job_offer.id)
        }
        for job_offer in job_offers
    ]
    
    return jsonify(result), 200

@main.route('/job_offers/<int:job_offer_id>', methods=['GET'])
def get_job_offer(job_offer_id):
    job_offer = JobOffer.query.get(job_offer_id)
    if not job_offer:
        return jsonify({"message": "Job offer not found"}), 404

    def get_number_applicants(job_offer_id):
        # Vérifie si l'offre d'emploi appartient à l'employeur connecté
        job_offer = JobOffer.query.get(job_offer_id)
        if not job_offer:
            return jsonify({"message": "Job offer not found"}), 404


        # Récupérer toutes les candidatures pour cette offre
        applications = Application.query.filter_by(job_offer_id=job_offer_id).all()
        if not applications:
            return 0
        
        return len(applications)
    
    result = {
        "id": job_offer.id,
        "title": job_offer.title,
        "description": job_offer.description,
        "criteria": job_offer.criteria,
        "employer_id": job_offer.employer_id,
        "number_applications": get_number_applicants(job_offer.id)

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

    # Getting cretria_dict and weights
    criteria_dict = np.array(job_offer.criteria.keys())
    weights = np.array(job_offer.criteria.values())

    # Appel de ta fonction
    genome = generate_genome(cv_path=file_path, criteria_dict=criteria_dict, weights=weights)

    print(f"Geeeeeeenome ======> {genome}")
    if genome is None:
        return jsonify({"message": "The AI model failed to generate a  genome from this CV"}), 500
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
    # Récupérer l'offre d'emploi
    job = JobOffer.query.get(job_offer_id)
    if not job:
        return jsonify({'message': 'Job offer not found'}), 404

    # Récupérer les applications associées à l'offre d'emploi
    applications = Application.query.filter_by(job_offer_id=job_offer_id).all()
    if not applications:
        return jsonify({'message': 'No applications for this job offer'}), 404

    # Récupération des critères de l'offre d'emploi
    criteria = job.criteria
    # print(f"Criteria ====> {criteria}")
    if not criteria:
        return jsonify({'message': 'No criteria defined for this job offer'}), 400

    # Préparation de la population pour l'algorithme génétique
    genome_to_application = {}
    population = []
    for app in applications:
        # Vérification avant désérialisation
        # print(f"Raw genome data for application {app.id}: {app.genome}")

        # Vérifier si le génome est déjà une liste et la valider
        genome = app.genome if isinstance(app.genome, list) else None
        if not genome or len(genome) != 7:
            print(f"Invalid genome for application {app.id}: {genome}")
            # Générer un génome aléatoire avec 7 valeurs comprises entre 0 et 50 si génome invalide
            genome = list(np.random.uniform(0, 50, size=7))

        # print(f"Genome ====> {genome}")
        if not genome or len(genome) != 7:
            # Générer un génome aléatoire avec 7 valeurs comprises entre 0 et 50 si génome invalide
            genome = list(np.random.uniform(0, 50, size=7))
        genome = list(map(float, genome))  # Sécurisation du génome
        population.append(genome)
        genome_to_application[tuple(genome)] = app

    if not population:
        return jsonify({'message': 'No genomes available for applicants'}), 400

    # Lancer l'algorithme génétique
    skills = list(criteria.keys())
    weights = np.array(list(criteria.values()))  # Assurez-vous que `weights` est un tableau numpy
    # print(f"Weights ====> {weights}")
    # print(f"Insssssssssspection =====> {run_genetic_algorithm_and_ahp(skills, weights, population, max_generations=1, num_finalists=10)}")
    
    finalists1, _, ahp_selection_sorted = run_genetic_algorithm_and_ahp(skills, weights, population, max_generations=10, num_finalists=10)  # L'algorithme génétique prend la population et les poids
    finalists = [candidate for candidate , _ in ahp_selection_sorted]
    
    print(f"finalists ====> {finalists}")

    # Appliquer AHP sur les finalistes (si vous avez cette fonction)
    # final_scores = run_ahp(finalists, skills, weights)

    # Construire la réponse avec informations des candidats
    response = {
        "finalists": finalists,
    }

    # Récupérer les informations sur les candidats
    finalists_with_info = []
    for i, candidate in enumerate(finalists):
        app_obj = genome_to_application.get(tuple(candidate))
        user = app_obj.job_seeker if app_obj else None

        finalists_with_info.append({
            "candidate": candidate,
            # "ahp_score": round(final_scores[f"C{i+1}"], 4) si vous avez des scores AHP
            "ahp_score": round(ahp_selection_sorted[i][1], 4),
            "user": {
                "id": user.id if user else None,
                "username": user.username if user else "",
            }
        })
    
    response["finalists_with_info"] = finalists_with_info
    
    print(f"Response ====> {response}")

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

@main.route('/statistic_job/<int:job_offer_id>/applications', methods=['GET'])
def get_number_application_for_job(job_offer_id):

    # Vérifie si l'offre d'emploi appartient à l'employeur connecté
    job_offer = JobOffer.query.get(job_offer_id)
    if not job_offer:
        return jsonify({"message": "Job offer not found"}), 404


    # Récupérer toutes les candidatures pour cette offre
    applications = Application.query.filter_by(job_offer_id=job_offer_id).all()
    if not applications:
        return jsonify({"message": "No applications found for this job offer"}), 404

    # Construction de la réponse avec les infos du candidat
    result = []
    result.append({
        "number_applications": len(applications)
    })

    return jsonify(result["number_applications"]), 200