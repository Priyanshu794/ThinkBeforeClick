# Phase 3: dataset loading/cleaning, TF-IDF vectorization,
# Logistic Regression training, evaluation, saves classifier.joblib
#
# Run from backend/ with the venv active:
#     python -m app.ml.train_model
#
# Dataset: backend/app/ml/dataset/phishing_dataset.csv (columns: text, label)
#   label = 1 -> phishing/spam, label = 0 -> safe/ham
# Combined from SMS Spam Collection + a multi-source phishing/ham compilation
# (Enron ham, phishing email corpora, SMS phishing) — see PROJECT_STATE.md for
# provenance notes. Already cleaned: deduped, whitespace-normalized, capped length.

import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, recall_score


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "new_data_to_merge.csv")
MODEL_DIR = os.path.join(BASE_DIR, "model")
MODEL_PATH = os.path.join(MODEL_DIR, "classifier.joblib")
VECTORIZER_PATH = os.path.join(MODEL_DIR, "vectorizer.joblib")


def load_data():
    df = pd.read_csv(DATASET_PATH)
    df = df.dropna(subset=["text", "label"])
    return df["text"], df["label"].astype(int)


def train():
    X, y = load_data()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # TF-IDF: unigrams + bigrams catch phrases like "click here", "act now"
    # that single words miss. min_df drops one-off noise; max_df drops
    # near-universal tokens that carry no signal.
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=3,
        max_df=0.9,
        max_features=50000,
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # class_weight="balanced" + a recall-favoring decision keeps false
    # negatives (missed phishing) rarer than false positives, per project
    # goal: a missed phishing message is worse than a false alarm.
    clf = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        C=1.0,
        random_state=42,
    )
    clf.fit(X_train_vec, y_train)

    y_pred = clf.predict(X_test_vec)

    print("=== Evaluation on held-out test set ===")
    print(classification_report(y_test, y_pred, target_names=["safe", "phishing"], digits=4))
    print("Confusion matrix (rows=actual, cols=predicted) [safe, phishing]:")
    print(confusion_matrix(y_test, y_pred))
    print(f"Recall on phishing class: {recall_score(y_test, y_pred):.4f}")

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(clf, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    print(f"\nSaved model to {MODEL_PATH}")
    print(f"Saved vectorizer to {VECTORIZER_PATH}")


if __name__ == "__main__":
    train()
