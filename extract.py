import csv
import re
import json

# Fonction pour lire les concepts depuis le fichier CSV
def read_concepts_from_csv(csv_file):
    concepts = {}
    with open(csv_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            for header, value in row.items():
                # Fusionner acteur1/2/3 en un seul concept 'acteur'
                if header.startswith('acteur'):
                    header = 'acteur'
                if header not in concepts:
                    concepts[header] = set()
                parts = [v.strip() for v in value.split(',') if v.strip()]
                for part in parts:
                    concepts[header].add(part)
        for header in concepts:
            concepts[header] = list(concepts[header])
    return concepts

# Normalisation des clauses WHERE pour les requêtes françaises
def normalize_french_where(where_clauses):
    normalized = {}
    for concept, values in where_clauses.items():
        # Élimine les doublons dans les valeurs
        unique_values = list(set(values))
        if concept.lower() == 'annee':
            # Remplace les années par 'year' et normalise les opérateurs
            normalized[concept] = [
                re.sub(r'\b(après|apres)\b', '>', v.lower())
                .replace('<', '<')
                .replace('>', '>')
                .replace(r'(\d{4})', 'year')
                for v in unique_values
            ]
        else:
            normalized[concept] = unique_values
    return normalized

# Extraction des concepts à partir d'une requête française
def extract_concepts(query, concepts):
    found = {}
    matched_values = set()

    for concept, values in concepts.items():
        for value in values:
            if value in matched_values:
                continue
            pattern = r'\b' + re.escape(value) + r'\b'
            if re.search(pattern, query, re.IGNORECASE):
                if concept not in found:
                    found[concept] = []
                found[concept].append(value)
                matched_values.add(value)

        # Gestion spécifique des années
        if concept.lower() == 'annee':
            year_pattern = r'\b(annee|année)\s*(>|<|>=|<=|après|apres|avant)\s*(\d{4})\b'
            year_matches = re.findall(year_pattern, query, re.IGNORECASE)
            for match in year_matches:
                operator = match[1].lower()
                year = match[2]
                found_value = f"{operator} {year}"
                if concept not in found:
                    found[concept] = []
                found[concept].append(found_value)
                matched_values.add(year)

    return found

# Extraction des intentions SELECT et WHERE
def extract_intentions(query, concepts):
    select_intent = None

    # Recherche de l'intention SELECT
    select_match = re.search(
        r'\b(montrer|afficher|donner|voir|liste)\s+(le|les|l\'|la)?\s*(\w+)',
        query,
        re.IGNORECASE
    )
    if select_match:
        target = select_match.group(3).lower()
        for concept in concepts:
            if concept.lower() == target:
                select_intent = concept
                break

    where_part = query
    where_clauses = {}
    if 'où' in query.lower():
        parts = re.split(r'\boù\b', query, flags=re.IGNORECASE)
        if len(parts) > 1:
            where_part = parts[1].strip()
    where_clauses = extract_concepts(where_part, concepts)
    where_clauses = normalize_french_where(where_clauses)

    return select_intent, where_clauses

def generate_intents_from_json(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    queries = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and 'sql' in item:
                queries.append(item['sql'])

    intents = []
    seen_intents = set()  
    for idx, query in enumerate(queries, 1):
        intent_name = f'intent{idx}'
        parsed = parse_sql_query(query)
        
        intent_key = f"select={parsed['select']};where='{parsed['where']}'"
        if intent_key not in seen_intents:
            intents.append({
                intent_name: {
                    'select': parsed['select'],
                    'where': parsed['where']
                }
            })
            seen_intents.add(intent_key) 
    return intents

def parse_sql_query(sql):
    intent = {'select': [], 'where': ''}
    try:
        select_match = re.search(r"SELECT\s+(.*?)\s+FROM", sql, re.IGNORECASE)
        if select_match:
            select_part = select_match.group(1).strip()
            if select_part == '*':
                intent['select'] = ['*']
            else:
                columns = [c.strip().split(' AS ')[0] for c in select_part.split(',')]
                columns = [re.sub(r'\(.*?\)', '', c).strip() for c in columns]
                columns = [c.split('.')[-1] for c in columns]
                intent['select'] = list(set(columns))  # Élimine les doublons

        where_match = re.search(r"WHERE\s+(.*)", sql, re.IGNORECASE | re.DOTALL)
        if where_match:
            where_clause = where_match.group(1).strip()
            where_clause = re.sub(r'^\(\((.*)\)\)$', r'\1', where_clause)
            where_clause = re.sub(r'\s+', ' ', where_clause)
            intent['where'] = normalize_sql_where(where_clause)
    except Exception as e:
        print(f"Erreur : {e}")
    return intent

def normalize_sql_where(where_clause):
    where_clause = re.sub(r"'[^']*'", "'name'", where_clause)
    where_clause = re.sub(r'\b(acteur[123])\b', 'acteur', where_clause)
    where_clause = re.sub(r'(\d{4})', 'year', where_clause)
    where_clause = re.sub(r'\b(après|apres)\b', '>', where_clause)
    where_clause = re.sub(r'\b(avant)\b', '<', where_clause)
    return where_clause

csv_file = 'base_films_500.csv'
concepts = read_concepts_from_csv(csv_file)

query_french = "Veuillez me montrer le titre des films où Meryl Streep joue et Hugh Jackman joue après 2005."
select_intent, where_intent = extract_intentions(query_french, concepts)

print(f"Requête: {query_french}")
print(f"Intention SELECT: {select_intent}")
print(f"Intention WHERE: {where_intent}")

json_file = 'queries_french_para.json'
intents = generate_intents_from_json(json_file)

for intent in intents:
    for name, clauses in intent.items():
        select = f"select={list(set(clauses['select']))}" if clauses['select'] else ""
        where = f"where='{clauses['where']}'" if clauses['where'] else ""
        print(f"{select}; {where}")



def generate_training_dataset(json_file, output_csv):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rows = []
    for entry in data:
        sql = entry.get('sql')
        if not sql:
            continue

        parsed = parse_sql_query(sql)
        select_label = f"select={sorted(parsed['select'])}"
        where_label = f"where='{parsed['where']}'"

        # On prend la requête principale + les paraphrases
        all_queries = []

        if "french" in entry:
            if "query_french" in entry["french"]:
                all_queries.append(entry["french"]["query_french"])
            if "paraphrase_french" in entry["french"]:
                all_queries.extend(entry["french"]["paraphrase_french"])

        for q in all_queries:
            rows.append((q, select_label, where_label))

    # Écriture dans un fichier CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['query_french', 'select_label', 'where_label'])
        writer.writerows(rows)

    print(f"✅ Fichier d'entraînement généré : {output_csv}")
generate_training_dataset("queries_french_para.json", "training_dataset.csv")
