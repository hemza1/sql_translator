import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import Perceptron
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

df = pd.read_csv("training_dataset.csv")

X = df["query_french"]
y_select = df["select_label"]
y_where = df["where_label"]

vectorizer = CountVectorizer()
X_vectorized = vectorizer.fit_transform(X)

X_train_s, X_test_s, y_train_s, y_test_s = train_test_split(X_vectorized, y_select, test_size=0.2, random_state=42)
X_train_w, X_test_w, y_train_w, y_test_w = train_test_split(X_vectorized, y_where, test_size=0.2, random_state=42)

clf_select = Perceptron(max_iter=1000, tol=1e-3)
clf_select.fit(X_train_s, y_train_s)

clf_where = Perceptron(max_iter=1000, tol=1e-3)
clf_where.fit(X_train_w, y_train_w)

print(" Performance du classifieur SELECT :")
y_pred_s = clf_select.predict(X_test_s)
print(classification_report(y_test_s, y_pred_s))
print("Confusion matrix SELECT:\n", confusion_matrix(y_test_s, y_pred_s))

print("\n Performance du classifieur WHERE :")
y_pred_w = clf_where.predict(X_test_w)
print(classification_report(y_test_w, y_pred_w))
print("Confusion matrix WHERE:\n", confusion_matrix(y_test_w, y_pred_w))

acc_select = accuracy_score(y_test_s, y_pred_s)
acc_where = accuracy_score(y_test_w, y_pred_w)
print(f"\n Accuracy SELECT: {acc_select*100:.2f}%")
print(f" Accuracy WHERE: {acc_where*100:.2f}%")
