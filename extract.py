import csv
import re

def read_concepts_from_csv(csv_file):
    concepts = {}
    
    with open(csv_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)  
        
        for row in reader:
            concept = row[0]  # Nom du concept (par exemple "acteur", "titre", etc.)
            values = row[1:]  # Les valeurs associées à ce concept (noms d'acteurs, titres, etc.)
            concepts[concept] = values
    
    return concepts

# Fonction de string matching pour identifier les concepts dans la requête
def extract_concepts(query, concepts):
    concepts_found = []
    
    # Recherche de chaque concept dans la requête
    for concept, fields in concepts.items():
        for field in fields:
            if re.search(r'\b' + re.escape(field) + r'\b', query, re.IGNORECASE):
                concepts_found.append((concept, field))
    
    return concepts_found

# Fonction pour extraire l'intention (SELECT et WHERE)
def extract_intentions(query):
    select_intent = None
    where_intent = None
    
    # Rechercher le SELECT dans la requête (selon la logique de la phrase)
    if re.search(r'\b(titre|film|films)\b', query, re.IGNORECASE):
        select_intent = 'SELECT'

    # Rechercher le WHERE dans la requête (selon la présence de conditions comme "où")
    if re.search(r'\b(où|where|dans)\b', query, re.IGNORECASE):
        where_intent = 'WHERE'
        
    return select_intent, where_intent

# Charger les concepts depuis le fichier CSV
csv_file = 'base_films_500.csv'  # Remplacez par le chemin de votre fichier CSV
concepts = read_concepts_from_csv(csv_file)

# Tester pour une seule requête en langage naturel
query_french = "Veuillez me montrer le titre des films où Meryl Streep joue et Hugh Jackman joue."

# Extraire les concepts et intentions
concepts_found = extract_concepts(query_french, concepts)
select_intent, where_intent = extract_intentions(query_french)

# Afficher les résultats
print(f"Requête: {query_french}")
print(f"Concepts trouvés: {concepts_found}")
print(f"Intention SELECT: {select_intent}")
print(f"Intention WHERE: {where_intent}")
