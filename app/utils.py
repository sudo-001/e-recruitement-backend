# Placeholder for actual utility functions
import random
from app.services import extract_resume_information, extract_text_from_pdf
import numpy as np
import ahpy



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
    
    return extracted_data["genome"]

    # genome = []
    
    # # Vérifier la taille
    
    # while len(genome) < 7:
    #     genome.append(0.0)
    # return genome[:7]


# Définition des compétences et des poids donnés par l'employeur
skills = ['Ability to work in different business units', 'Past experience', 'Team player', 'Fluency in a foreign language', 'Strategic thinking', 'Oral communication skills', 'Computer skills']
weights = np.array([0.15, 0.20, 0.10, 0.10, 0.15, 0.15, 0.15])  # Importance des compétences

# generate_genome("../Carick-Appolinaire-ATEZONG-YMELE-FlowCV-Resume-20250215.pdf", skills, weights)

# # Génération aléatoire des candidats (100 candidats, scores de 50 à 100 par compétence)
# num_candidates = 100
# population = np.random.randint(1, 50, (num_candidates, len(skills)))
# original_population = population.copy()  # On garde la population initiale


# def fitness(candidate):
#         """ Calcule la fitness d'un candidat en fonction des poids des compétences """
#         return np.dot(candidate, weights)


# def mutation(candidate, mutation_rate=1):
#     """ Modifie légèrement un score de compétence en échangeant deux compétences """
#     if random.random() < mutation_rate:
#         idx1, idx2 = random.sample(range(len(candidate)), 2)  # Choisir deux indices au hasard
#         candidate[idx1], candidate[idx2] = candidate[idx2], candidate[idx1]  # Échange les valeurs
#     return candidate


# def genetic_algorithm(max_generations=1, num_finalists=10):
#     """ Exécute l'algorithme génétique avec sélection aléatoire sur une moitié de la population """
#     global population
    
#     for generation in range(max_generations):
#         # print(f"Génération {generation + 1}")
        
#         # Sélection de la moitié de la population aléatoirement
#         selected_indices = np.random.choice(len(population), size=len(population) // 2, replace=False)
#         selected_candidates = [population[i] for i in selected_indices]
        
#         best_candidate = max(selected_candidates, key=fitness)  # Trouver le meilleur parmi eux
        
#         new_population = [best_candidate]  # Conserver le meilleur sans modification
#         for candidate in selected_candidates:
#             if not np.array_equal(candidate, best_candidate):  # Ne pas modifier le meilleur
#                 new_population.append(mutation(candidate.copy()))
        
#         # Complétion avec des candidats initiaux
#         new_population_list = [c.tolist() for c in new_population]
#         remaining_candidates = [c for c in original_population if c.tolist() not in new_population_list]

#         # Mélange aléatoire des candidats restants
#         random.shuffle(remaining_candidates)


#         # Completion
#         new_population += remaining_candidates[:(num_candidates - len(new_population))//2]

#         print(len(new_population))

        
#         population = np.array(new_population)
    
#         # Trier la dernière génération selon la fitness
#         population = sorted(population, key=fitness, reverse=True)
        
#         # Sélection des 10 meilleurs pour AHP parmi ceux qui ont déposé leur CV
#         population_list = [c.tolist() for c in population]
#         final_candidates = [c for c in original_population if c.tolist() in population_list]

#         finalists_mutate = sorted(population, key=fitness, reverse=True)[:num_finalists]
#         finalists_including_init_candidates = sorted(final_candidates, key=fitness, reverse=True)[:num_finalists]
        
#         print("\nDix meilleurs parmi ceux existant")
#         for i, f in enumerate(finalists_including_init_candidates):
#             print(f"Candidat {i+1}: {f}, Score_fitness = {fitness(f):.2f}")
        
#         print("\nDix meilleurs parmi ceux mutés")
#         for i, f in enumerate(finalists_mutate):
#             print(f"Candidat {i+1}: {f}, Score_fitness = {fitness(f):.2f}")

#         return finalists_including_init_candidates, finalists_mutate

# def run_ahp(finalists, skills, weights):
#     # Construire la structure AHP
#     # 1. Comparaison des critères (les skills) en utilisant leurs poids
#     comparisons = {}
#     for i in range(len(skills)):
#         for j in range(i + 1, len(skills)):
#             ratio = weights[i] / weights[j] if weights[j] != 0 else 1
#             comparisons[(skills[i], skills[j])] = ratio

#     criteria_cmp = ahpy.Compare('Skills', comparisons, precision=3, random_index='saaty')

#     # 2. Pour chaque critère, comparer les candidats selon leur score pour ce critère
#     subcriteria = {}
#     for i, skill in enumerate(skills):
#         skill_comparisons = {}
#         for x in range(len(finalists)):
#             for y in range(x + 1, len(finalists)):
#                 try:
#                     score_x = float(finalists[x][i])  # Sécuriser la conversion en float
#                     score_y = float(finalists[y][i])  # Sécuriser la conversion en float
#                     ratio = score_x / score_y if score_y != 0 else 1
#                     skill_comparisons[(f'C{x+1}', f'C{y+1}')] = ratio
#                 except ValueError as e:
#                     print(f"Erreur AHP: conversion score => {finalists[x][i]}, {finalists[y][i]} -> {e}")
#         subcriteria[skill] = ahpy.Compare(skill, skill_comparisons, precision=3)

#     # 3. Créer le modèle global AHP
#     model = ahpy.Compare('Final', {}, precision=3)
#     model.add_children([subcriteria[s] for s in skills])
#     model.add_children([criteria_cmp])

#     # 4. Renvoyer les scores AHP pour chaque candidat
#     final_scores = model.target_weights
#     return [{"candidate": candidate, "ahp_score": round(final_scores[f"C{i+1}"], 4)} for i, candidate in enumerate(finalists)]
