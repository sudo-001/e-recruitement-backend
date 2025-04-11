# Placeholder for actual utility functions
import random
from app.services import extract_resume_information, extract_text_from_pdf
import numpy as np
import ahpy


def generate_genome(cv_path, criteria_dict):
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

    extracted_data = extract_resume_information(resume_text)
    if not extracted_data:
        print("❌ Échec de l'extraction des informations via Gemini.")
        return [0.0] * 7

    genome = []
    resume_skills = [s.lower() for s in extracted_data.get("skills", [])]
    years_exp = float(extracted_data.get("number_of_years_experience", "0") or "0")
    test_scores = extracted_data.get("test_scores", {})
    number_of_experiences = extracted_data.get("number_of_experiences", 0)
    resume_text_lower = resume_text.lower()

    for label, weight in criteria_dict.items():
        label_lower = label.lower()
        score = 0.0

        if "experience" in label_lower or "past experience" in label_lower:
            score = min((years_exp / 10) * 50, 50)

        elif "computer skills" in label_lower:
            match_count = sum(1 for skill in resume_skills if "computer" in skill or "programming" in skill or "software" in skill)
            score = min(match_count * 10, 50)

        elif "foreign language" in label_lower:
            if any(lang in resume_text_lower for lang in ["english", "french", "german", "spanish", "chinese", "arabic"]):
                score = 50
            else:
                score = 10  # faible probabilité

        elif "oral communication" in label_lower:
            if "communication" in resume_text_lower or "present" in resume_text_lower:
                score = 40 + random.uniform(0, 10)
            else:
                score = 15 + random.uniform(0, 10)

        elif "strategic thinking" in label_lower:
            if "strategy" in resume_text_lower or "plan" in resume_text_lower:
                score = 35 + random.uniform(0, 15)
            else:
                score = 10 + random.uniform(0, 10)

        elif "team player" in label_lower or "teamwork" in label_lower:
            if "team" in resume_text_lower or "collaborate" in resume_text_lower:
                score = 40 + random.uniform(0, 10)
            else:
                score = 20 + random.uniform(0, 10)

        elif "skill" in label_lower:
            match_count = sum(1 for skill in resume_skills if label_lower in skill)
            score = min(match_count * 10, 50)

        else:
            # Heuristique par défaut
            if label_lower in resume_text_lower:
                score = 25 + random.uniform(0, 15)
            else:
                score = 5 + random.uniform(0, 10)

        # Appliquer le poids (poids de l'employeur entre 0 et 1)
        weighted_score = round(min(score * weight, 50), 2)
        genome.append(weighted_score)

    # Vérifier la taille
    while len(genome) < 7:
        genome.append(0.0)
    return genome[:7]


def run_genetic_algorithm(population, skills, weights, max_generations=3, num_finalists=10):
    population = np.array(population)
    original_population = population.copy()

    def fitness(candidate):
        return np.dot(candidate, weights)

    def mutation(candidate, mutation_rate=1):
        if random.random() < mutation_rate:
            idx1, idx2 = random.sample(range(len(candidate)), 2)
            candidate[idx1], candidate[idx2] = candidate[idx2], candidate[idx1]
        return candidate

    for _ in range(max_generations):
        selected_indices = np.random.choice(len(population), size=len(population) // 2, replace=False)
        selected_candidates = [population[i] for i in selected_indices]

        best_candidate = max(selected_candidates, key=fitness)
        new_population = [best_candidate]

        for candidate in selected_candidates:
            if not np.array_equal(candidate, best_candidate):
                new_population.append(mutation(candidate.copy()))

        remaining_candidates = [c for c in original_population if c.tolist() not in [n.tolist() for n in new_population]]
        random.shuffle(remaining_candidates)
        new_population += remaining_candidates[:(len(original_population) - len(new_population)) // 2]

        population = np.array(new_population)

    # Trier et retourner les num_finalists meilleurs
    sorted_finalists = sorted(population, key=fitness, reverse=True)[:num_finalists]
    return [list(f) for f in sorted_finalists]

def run_ahp(finalists, skills, weights):
    # Construire la structure AHP
    # 1. Comparaison des critères (les skills) en utilisant leurs poids
    comparisons = {}
    for i in range(len(skills)):
        for j in range(i + 1, len(skills)):
            ratio = weights[i] / weights[j] if weights[j] != 0 else 1
            comparisons[(skills[i], skills[j])] = ratio

    criteria_cmp = ahpy.Compare('Skills', comparisons, precision=3, random_index='saaty')

    # 2. Pour chaque critère, comparer les candidats selon leur score pour ce critère
    subcriteria = {}
    for i, skill in enumerate(skills):
        skill_comparisons = {}
        for x in range(len(finalists)):
            for y in range(x + 1, len(finalists)):
                score_x = finalists[x][i]
                score_y = finalists[y][i]
                ratio = score_x / score_y if score_y != 0 else 1
                skill_comparisons[(f'C{x+1}', f'C{y+1}')] = ratio
        subcriteria[skill] = ahpy.Compare(skill, skill_comparisons, precision=3)

    # 3. Créer le modèle global AHP
    model = ahpy.Compare('Final', {}, precision=3)
    model.add_children([subcriteria[s] for s in skills])
    model.add_children([criteria_cmp])

    # 4. Renvoyer les scores AHP pour chaque candidat
    final_scores = model.target_weights
    return [{"candidate": candidate, "ahp_score": round(final_scores[f"C{i+1}"], 4)} for i, candidate in enumerate(finalists)]
