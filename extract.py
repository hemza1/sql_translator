import csv
import re

def read_concepts_from_csv(csv_file):
    concepts = {}
    
    with open(csv_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            for header, value in row.items():
                if header not in concepts:
                    concepts[header] = set()
                parts = [v.strip() for v in value.split(',') if v.strip()]
                for part in parts:
                    concepts[header].add(part)
        for header in concepts:
            concepts[header] = list(concepts[header])
    return concepts

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
    return found

def extract_intentions(query, concepts):
    select_intent = None
    
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
    
    return select_intent, where_clauses

csv_file = 'base_films_500.csv'  
concepts = read_concepts_from_csv(csv_file)

query_french = "Veuillez me montrer le titre des films où Meryl Streep joue après 2005."
select_intent, where_intent = extract_intentions(query_french, concepts)

print(f"Requête: {query_french}")
print(f"Intention SELECT: {select_intent}")
print(f"Intention WHERE: {where_intent}")


import json
import re

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
                columns = [c.split('.')[-1] for c in columns]  # Enlève les alias de table
                intent['select'] = [c for c in columns if c]
        
        where_match = re.search(r"WHERE\s+(.*)", sql, re.IGNORECASE | re.DOTALL)
        if where_match:
            where_clause = where_match.group(1).strip()
            where_clause = re.sub(r'^\(\((.*)\)\)$', r'\1', where_clause)  # Enlève les doubles parenthèses
            where_clause = re.sub(r'\s+', ' ', where_clause)  # Normalise les espaces
            intent['where'] = normalize_where_clause(where_clause)
        
    except Exception as e:
        print(f"Erreur lors de l'analyse de la requête : {sql}")
        print(e)
    
    return intent

def normalize_where_clause(where_clause):
    where_clause = re.sub(r"'[^']*'", "'name'", where_clause)
    
    where_clause = re.sub(r'\b(acteur[123])\b', 'acteur', where_clause)
    
    where_clause = re.sub(r'=\s*"', '= ', where_clause)  # Pour les cas avec guillemets
    
    return where_clause

def generate_intents_from_json(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    queries = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and 'sql' in item:
                queries.append(item['sql'])
    
    intents = []
    for idx, query in enumerate(queries, 1):
        parsed = parse_sql_query(query)
        if parsed['select'] or parsed['where']:
            intent_name = f'intent{idx}'
            intents.append({
                intent_name: {
                    'select': parsed['select'],
                    'where': parsed['where']
                }
            })
    
    return intents

json_file = 'queries_french_para.json' 

intents = generate_intents_from_json(json_file)

for intent in intents:
    for name, clauses in intent.items():
        select = f"select={clauses['select']}" if clauses['select'] else ""
        where = f"where='{clauses['where']}'" if clauses['where'] else ""
        print(f"— {name} : {select}; {where}")



