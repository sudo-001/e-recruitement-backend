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


# Fonction principale pour l'algorithme génétique et l'AHP
def run_genetic_algorithm_and_ahp(skills, weights, population_from_db, max_generations=1, num_finalists=10):
    # print("Début de l'algorithme génétique et de l'AHP")
    # print("Compétences :", skills)
    print("Poids :", weights)
    # print("Population initiale :", population_from_db)
    # print("Taille de la population :", len(population_from_db))
    
    
    """Exécute l'algorithme génétique et sélectionne les finalistes avec AHP."""
    
    # La population est passée en paramètre, donc pas besoin de la générer
    population = np.array(population_from_db)
    original_population = population.copy()

    def fitness(candidate):
        return np.dot(candidate, weights)

    def mutation(candidate, mutation_rate=1.0, mutation_type="swap"):
        """Appliquer une mutation au candidat selon le type spécifié"""
        if random.random() >= mutation_rate:
            return candidate  # Pas de mutation

        if mutation_type == "swap":
            idx1, idx2 = random.sample(range(len(candidate)), 2)
            candidate[idx1], candidate[idx2] = candidate[idx2], candidate[idx1]

        elif mutation_type == "shuffle":
            start, end = sorted(random.sample(range(len(candidate)), 2))
            sublist = candidate[start : end + 1]
            random.shuffle(sublist)
            candidate[start : end + 1] = sublist

        elif mutation_type == "random_reset":
            idx = random.randint(0, len(candidate) - 1)
            candidate[idx] = random.randint(0, 50)  # Compétences du candidat

        elif mutation_type == "gaussian":
            idx = random.randint(0, len(candidate) - 1)
            candidate[idx] += int(np.random.normal(0, 1))  # Petite perturbation
            candidate[idx] = max(0, min(10, candidate[idx]))  # Clamp si nécessaire

        else:
            raise ValueError(f"Type de mutation inconnu : {mutation_type}")

        return candidate

    # Exécution de l'algorithme génétique
    mutation_types = ["swap", "shuffle", "random_reset", "gaussian"]
    for generation in range(max_generations):
        # Sélection de la moitié de la population aléatoirement
        selected_indices = np.random.choice(len(population), size=len(population) // 2, replace=False)
        selected_candidates = [population[i] for i in selected_indices]

        best_candidate = max(selected_candidates, key=fitness)  # Trouver le meilleur parmi eux

        new_population = [best_candidate]  # Conserver le meilleur sans modification
        for candidate in selected_candidates:
            if not np.array_equal(candidate, best_candidate):  # Ne pas modifier le meilleur
                random_mutation_type = random.choice(mutation_types)
                mutated = mutation(candidate.copy(), mutation_type=random_mutation_type)
                new_population.append(mutated)

        # Complétion avec des candidats initiaux
        new_population_list = [c.tolist() for c in new_population]
        remaining_candidates = [
            c for c in original_population if c.tolist() not in new_population_list
        ]

        # Mélange aléatoire des candidats restants
        random.shuffle(remaining_candidates)

        # Compléter la population
        new_population += remaining_candidates[:(len(population) - len(new_population)) // 2]

        population = np.array(new_population)

    # Trier la dernière génération selon la fitness
    population = sorted(population, key=fitness, reverse=True)

    # Sélection des 10 meilleurs pour AHP parmi ceux qui ont déposé leur CV
    population_list = [c.tolist() for c in population]
    final_candidates = [c for c in original_population if c.tolist() in population_list]

    finalists_mutate = sorted(population, key=fitness, reverse=True)[:num_finalists]
    finalists_including_init_candidates = sorted(final_candidates, key=fitness, reverse=True)[:num_finalists]

    # AHP
    criteria_comparisons = {
        ("C_1", "C_2"): 2,
        ("C_1", "C_3"): 2,
        ("C_1", "C_4"): 4,
        ("C_1", "C_5"): 3,
        ("C_1", "C_6"): 2,
        ("C_1", "C_7"): 3,
        ("C_2", "C_3"): 1,
        ("C_2", "C_4"): 3,
        ("C_2", "C_5"): 2,
        ("C_2", "C_6"): 1,
        ("C_2", "C_7"): 2,
        ("C_3", "C_4"): 3,
        ("C_3", "C_5"): 2,
        ("C_3", "C_6"): 1,
        ("C_3", "C_7"): 2,
        ("C_4", "C_5"): 1 / 2,
        ("C_4", "C_6"): 1 / 3,
        ("C_4", "C_7"): 2,
        ("C_5", "C_6"): 1 / 2,
        ("C_5", "C_7"): 1,
        ("C_6", "C_7"): 2,
    }

    skills_comparison = ahpy.Compare(name='Skills', comparisons=criteria_comparisons, precision=3, random_index='saaty')

    # Extraire les poids finaux des compétences
    def extract_number(key):
        return int(''.join(filter(str.isdigit, key)))

    sorted_skills_weight = dict(sorted(skills_comparison.target_weights.items(), key=lambda item: extract_number(item[0])))
    final_skills_weight = np.array(list(sorted_skills_weight.values()))

    # Calculer et trier les candidats en fonction du score AHP
    ahp_selection = []
    for i, candidate in enumerate(finalists_mutate):
        np_candidate = np.array(candidate)
        score = np.dot(np_candidate, final_skills_weight)
        ahp_selection.append((candidate.tolist(), score))

    # Trier la sélection AHP par score décroissant
    ahp_selection_sorted = sorted(ahp_selection, key=lambda x: x[1], reverse=True)

    return finalists_including_init_candidates, finalists_mutate, ahp_selection_sorted

# resume_text = extract_text_from_pdf("./Carick-Appolinaire-ATEZONG-YMELE-FlowCV-Resume-20250215.pdf")
# if resume_text:
#     extracted_data = extract_resume_information(resume_text)
#     print(extracted_data)
# else:
#     print("No text extracted from the PDF.")
# Test the function with a sample PDF file