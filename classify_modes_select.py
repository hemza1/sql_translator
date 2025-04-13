import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from collections import Counter

df = pd.read_csv("training_dataset.csv")
X = df["query_french"]
y = df["select_label"]  

vectorizer = CountVectorizer()
X_vectorized = vectorizer.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_vectorized, y, test_size=0.2, random_state=42)

clf_none = LogisticRegression(max_iter=1000, class_weight=None)
clf_none.fit(X_train, y_train)
y_pred_none = clf_none.predict(X_test)

clf_balanced = LogisticRegression(max_iter=1000, class_weight='balanced')
clf_balanced.fit(X_train, y_train)
y_pred_balanced = clf_balanced.predict(X_test)

counts = dict(Counter(y_train))
total = sum(counts.values())
manual_weights = {label: total / (len(counts) * freq) for label, freq in counts.items()}
clf_manual = LogisticRegression(max_iter=1000, class_weight=manual_weights)
clf_manual.fit(X_train, y_train)
y_pred_manual = clf_manual.predict(X_test)

def eval_model(name, y_test, y_pred):
    print(f"\n🔎 Évaluation - {name}")
    print(classification_report(y_test, y_pred, zero_division=0))
    print("Confusion matrix:\n", confusion_matrix(y_test, y_pred))
    print(f" Accuracy: {accuracy_score(y_test, y_pred)*100:.2f}%")

eval_model("Sans pondération (None)", y_test, y_pred_none)
eval_model("Avec class_weight='balanced'", y_test, y_pred_balanced)
eval_model("Avec class_weight=manuel", y_test, y_pred_manual)
