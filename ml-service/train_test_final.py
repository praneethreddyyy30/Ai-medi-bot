#train and testing with saving
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, f1_score, classification_report
from xgboost import XGBClassifier
import matplotlib.pyplot as plt
import joblib 
import sys
sys.stdout.reconfigure(encoding='utf-8')

csv_path = "realistic_infectious_disease_dataset_45.csv"
df = pd.read_csv(csv_path)

y = df["diseases"].astype(str)
X = df.drop(columns=["diseases"])
X = X.apply(pd.to_numeric, errors="coerce").fillna(0).astype(np.float32)

le = LabelEncoder()
y_enc = le.fit_transform(y)
num_classes = len(np.unique(y_enc))


X_train, X_test, y_train, y_test = train_test_split(
    X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
)

#Define XGBoost model with tuned parameters
model = XGBClassifier(
    objective="multi:softmax",  
    num_class=num_classes,
    n_estimators=1000,
    max_depth=10,
    learning_rate=0.03,
    subsample=0.85,
    colsample_bytree=0.85,
    reg_lambda=1.5,
    reg_alpha=0.5,
    min_child_weight=2,
    gamma=0.1,
    tree_method="hist",
    random_state=42,
    n_jobs=-1,
    verbosity=0,
    eval_metric=["mlogloss", "merror"]
)

# 6) Train model (no early stopping)
model.fit(
    X_train, y_train,
    eval_set=[(X_train, y_train), (X_test, y_test)],
    verbose=False
)

# 7) Training results
results = model.evals_result()
train_error = results["validation_0"]["merror"]
test_error = results["validation_1"]["merror"]

# 8) Evaluation
y_pred = model.predict(X_test)
print("\n✅ XGBoost Results ")
print(f"Test Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print(f"Macro F1: {f1_score(y_test, y_pred, average='macro'):.4f}\n")
print("Classification Report:\n")
print(classification_report(y_test, y_pred, target_names=le.classes_, zero_division=0))

# 9) Plot bar chart (Train vs Test Accuracy over iterations)
plt.figure(figsize=(8,6))
plt.bar(range(1, len(train_error)+1), [1-e for e in train_error], alpha=0.6, label="Train Accuracy")
plt.bar(range(1, len(test_error)+1), [1-e for e in test_error], alpha=0.6, label="Test Accuracy")
plt.xlabel("Iteration")
plt.ylabel("Accuracy")
plt.title("Accuracy over Iterations (Bar Chart)")
plt.legend()
plt.tight_layout()
plt.savefig("accuracy_plot.png")

# 🔹 10) Save the trained model + encoder
joblib.dump((model, le), "disease_predictor.pkl")
print("💾 Model and LabelEncoder saved as 'disease_predictor.pkl'")
