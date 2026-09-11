"""
Assignment 2: Classification Decision Tree using the ID3 Algorithm
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                              f1_score, classification_report)



# ------------------------------------------------------------------



# Dataset Selection and Preprocessing
df = pd.read_csv(os.path.dirname(__file__) + "/" + "Titanic-Dataset - Titanic-Dataset - Titanic-Dataset - Titanic-Dataset.csv")

print(f"\nShape: {df.shape[0]} rows, {df.shape[1]} columns")



# ------------------------------------------------------------------



# Handling missing values

print("\nMissing values in each column:")
print(df.isnull().sum())

# - Age: ~20% missing, numeric : using median
# - Embarked: only 2 missing, categorical, string : using mode
# - Cabin: ~77% missing -> median/ mode would not be reliable, dropping the column

df["Age"] = df["Age"].fillna(df["Age"].median())
df["Embarked"] = df["Embarked"].fillna(df["Embarked"].mode()[0])
df = df.drop(columns=["Cabin"])

# Dropping columns that are identifiers (non-predictive),
# PassengerId, Name, Ticket
df = df.drop(columns=["PassengerId", "Name", "Ticket"])

# Changing the discrete strings to numeric data with encoder
le_sex = LabelEncoder()
df["Sex"] = le_sex.fit_transform(df["Sex"])          # male=1, female=0
le_embarked = LabelEncoder()
df["Embarked"] = le_embarked.fit_transform(df["Embarked"])

print("\nData after cleaning and encoding:")
print(df.head())
print(f"\nRemaining missing values: {df.isnull().sum().sum()}")



# ------------------------------------------------------------------



# Train-test split
X = df.drop(columns=["Survived"])
y = df["Survived"]

# 80:20 train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
print(f"\nTraining set: {X_train.shape[0]} rows | Testing set: {X_test.shape[0]} rows")



# ------------------------------------------------------------------



# Implementing ID3

def entropy(y):
    counts = np.bincount(y)                 # counts for each bin
    probs = counts[counts > 0] / len(y)     # probability of each bin
    return - np.sum(probs * np.log2(probs))

def information_gain(X_col, y):
    base_entropy = entropy(y.to_numpy())    # entropy_y
    values, counts = np.unique(X_col, return_counts=True)   # for weighted entropy
    weighted_entropy = 0.0
    for v, c in zip(values, counts):
        subset_y = y[X_col == v]
        weighted_entropy += (c / len(X_col)) * entropy(subset_y.to_numpy())
    return base_entropy - weighted_entropy


base_entropy = entropy(y_train.to_numpy())
print(f"\nEntropy of target y on training data: {base_entropy:.4f}")

print("\nInformation gain per feature (training data):")
gains = {}
for col in X_train.columns:
    gains[col] = information_gain(X_train[col], y_train)
gains_sorted = dict(sorted(gains.items(), key=lambda item: item[1], reverse=True))
for col, gain in gains_sorted.items():
    print(f"  {col}: {gain:.4f}")



# ------------------------------------------------------------------



# Training the Decision Tree
# criterion = entropy

clf = DecisionTreeClassifier(criterion="entropy", max_depth=4, random_state=42)
clf.fit(X_train, y_train)

print(f"\nTree depth: {clf.get_depth()}")
print(f"Number of leaves: {clf.get_n_leaves()}")
print("\nFeature importances (based on information gain contribution):")
for col, imp in sorted(zip(X.columns, clf.feature_importances_),
                        key=lambda x: x[1], reverse=True):
    print(f"  {col}: {imp:.4f}")



# ------------------------------------------------------------------



# Testing and Evaluation

y_pred = clf.predict(X_test)

acc = accuracy_score(y_test, y_pred)
prec = precision_score(y_test, y_pred)
rec = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)

print(f"\nAccuracy:  {acc:.4f}")
print(f"Precision: {prec:.4f}")
print(f"Recall:    {rec:.4f}")
print(f"F1-score:  {f1:.4f}")

print("\nFull classification report:")
print(classification_report(y_test, y_pred, target_names=["Did not survive", "Survived"]))

# Visualize the decision tree

print("\nThe map between numeric values of age and embarked and actual strings (to understand the plot):")
print("     Sex encoding:", dict(zip(le_sex.classes_, le_sex.transform(le_sex.classes_))))
print("     Embarked encoding:", dict(zip(le_embarked.classes_, le_embarked.transform(le_embarked.classes_))))

plt.figure(figsize=(20, 10))
plot_tree(clf, feature_names=X.columns, class_names=["Not Survived", "Survived"],
          filled=True, rounded=True, fontsize=8)
plt.title("ID3 Decision Tree - Titanic Survival")
plt.tight_layout()
plt.show()
# plt.savefig(os.path.dirname(__file__) + "/" + "Titanic_data_ID3_visualization.png", dpi=150)
plt.close()


'''

 Analysis and Conclusion
^^^^^^^^^^^^^^^^^^^^^^^^^

The ID3 decision tree (criterion= entropy) works with the motivation of splitting
branches that maximizes information gain. It achieved an accuracy of 0.79 on the 
test set. The precision on survived class is 0.84.

The results show that the root node is sex, which makes sense, as women were
prioritised when leaving on life-boats. The passenger class and fare comes next,
which is again consistent with popular theories that economical status influenced
the boat-filling as well. Age appears right next, as the extreme conditions made it
difficult for older people to survive. The other columns are fairly irrelevant 
compared to these four.

The performance of ID3 is fairly satisfactory (for ID3). Since ID3 has an intrinsic
tendency to overfit small, noisy datasets, we set max_depth to 4. And that
costs the accuracy. But for a small dataset like this (891 rows), gaining accuracy
causes serious problems of overfitting.

'''