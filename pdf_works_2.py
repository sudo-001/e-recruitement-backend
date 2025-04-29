# Placeholder for actual utility functions
import random
from app.services import extract_resume_information, extract_text_from_pdf
import numpy as np
import ahpy


import pypdf
import pypdf
import google.generativeai as genai
import os
import json
import numpy as np
import random
from copy import deepcopy
import pypdf
import matplotlib.pyplot as plt
import ahpy


# Configure Gemini API (replace with your actual API key)
GOOGLE_API_KEY = "AIzaSyCoGPcEuJifNcE_BqTCZB533P0qizuJ4xk"# os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
MODEL_NAME = "gemini-1.5-pro"
model = genai.GenerativeModel(MODEL_NAME)


def extract_text_from_pdf(pdf_path):
    """Extracts text content from a PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()
        return text
    except FileNotFoundError:
        print(f"Error: PDF file not found at {pdf_path}")
        return None
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return None

def extract_resume_information(resume_text, criteria_dict, weights):
    
    prompt = f"""
    This is the list of criteria give by an employer {criteria_dict}, this is the weight for each criteria {weights}, and this is the resume of the CV of the job_seeker : {resume_text}.
    
    Consider all these informations and just give me a unique genome of size 7 like the number of criteria, and where each value is a float between 0 and 50 with 0 and 50 reachable, and also each value represent the score of that candidate based on his CV. That genome is for this candidate, the genome is going to be saved in this field "genome = db.Column(JSON, nullable=True)", so you have to give to me the genome like this by example [10, 20.5,...]

    Make sure to give me just the genome in the JSON form so i'll extract it, give it to me like this, just give me the genome don't add any comment just the genome like this : 
    {{
        "genome": [10, 20, 20.05, ...]
    }}
    """
    try:
        response = model.generate_content(prompt)  # Use generate_content for text-only input
        json_string = response.text
        # Attempt to parse the JSON
        import json
        extracted_data = json.loads(json_string)
        print("Extracted data GENOOOOOMEEEEE !!!!!!!!:", extracted_data["genome"])
        return extracted_data
    except Exception as e:
        print(f"Error extracting information: {e}")
        print(f"Response text: {response.text if 'response' in locals() else 'No response received'}")
        return None


def generate_genome(cv_path, criteria_dict, weights):
    """
    Génère le genome d’un candidat à partir de son CV et des critères de l’employeur.

    - cv_path: Chemin vers le fichier PDF du CV.
    - criteria_dict: Dictionnaire avec {nom_critère: poids}
    Retourne une liste ordonnée de scores sur 50 pour chaque critère.
    """
    resume_text = extract_text_from_pdf(cv_path)
    if not resume_text:
        print("❌ Échec de l'extraction du texte depuis le CV.")
        return [0.0] * 7

    extracted_data = extract_resume_information(resume_text, criteria_dict, weights)
    # if not extracted_data:
    #     print("❌ Échec de l'extraction des informations via Gemini.")
    #     return [0.0] * 7

    print("✅ Extraction réussie via Gemini.")
    print("Données extraites!!!!!!!!!!!!!:", extracted_data)
    
    genome = []
    # resume_skills = [s.lower() for s in extracted_data.get("skills", [])]
    # years_exp = float(extracted_data.get("number_of_years_experience", "0") or "0")
    # test_scores = extracted_data.get("test_scores", {})
    # number_of_experiences = extracted_data.get("number_of_experiences", 0)
    # resume_text_lower = resume_text.lower()

    # Vérifier la taille
    while len(genome) < 7:
        genome.append(0.0)
    return genome[:7]


# Définition des compétences et des poids donnés par l'employeur
skills = ['Ability to work in different business units', 'Past experience', 'Team player', 'Fluency in a foreign language', 'Strategic thinking', 'Oral communication skills', 'Computer skills']
weights = np.array([0.15, 0.20, 0.10, 0.10, 0.15, 0.15, 0.15])  # Importance des compétences

generate_genome("./Carick-Appolinaire-ATEZONG-YMELE-FlowCV-Resume-20250215.pdf", skills, weights)
