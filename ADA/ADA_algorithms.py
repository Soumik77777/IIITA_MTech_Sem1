import math
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

def load_dataset(path, x_cols, y_cols):
    df = pd.read_csv(path)
    X = df[x_cols]
    y = df[y_cols]
    if len(y_cols) == 1:
        y = y.iloc[:, 0]
    return X, y

def preprocess(df, one_hot=False, missing="fill"):
    df = df.copy()
    if missing == "drop":
        df = df.dropna(axis=1)
    elif missing == "fill":
        for col in df.columns:
            if df[col].isna().any():
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].mean())
                else:
                    df[col] = df[col].fillna(df[col].mode()[0])
    else:
        raise ValueError("missing must be 'fill' or 'drop'")
    if one_hot:
        df = pd.get_dummies(df, dtype=int)
    return df

def split_data(X, y, test_size=0.2, random_state=42):
    return train_test_split(X, y, test_size=test_size, random_state=random_state)

def standardize(X_train, X_test=None):
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    if X_test is None:
        return X_train, scaler
    return X_train, scaler.transform(X_test), scaler

def naive_bayes(X_train, y_train, X_test):
    X_train = np.asarray(X_train)
    X_test = np.asarray(X_test)
    y_train = np.asarray(y_train).astype(int)
    classes = np.unique(y_train)
    priors = {}
    likelihoods = {}
    for c in classes:
        Xc = X_train[y_train == c]
        priors[c] = len(Xc) / len(X_train)
        likelihoods[c] = (Xc.sum(axis=0) + 1) / (Xc.sum(axis=0).sum() + Xc.shape[1])
    predictions = []
    for x in X_test:
        scores = {}
        for c in classes:
            scores[c] = math.log(priors[c]) + np.sum(x * np.log(likelihoods[c] + 1e-12))
        predictions.append(max(scores, key=scores.get))
    return np.array(predictions)

def svm(X_train, y_train, X_test, C=1.0, learning_rate=0.001, epochs=1000):
    X_train = np.asarray(X_train, dtype=float)
    X_test = np.asarray(X_test, dtype=float)
    y = np.where(np.asarray(y_train).astype(int) == 1, 1.0, -1.0)
    w = np.zeros(X_train.shape[1])
    b = 0.0
    for _ in range(epochs):
        margin = y * (X_train @ w + b)
        mask = margin < 1
        if np.any(mask):
            dw = w / C - np.sum(y[mask, None] * X_train[mask], axis=0)
            db = -np.sum(y[mask])
        else:
            dw = w / C
            db = 0.0
        w -= learning_rate * dw
        b -= learning_rate * db
    return (X_test @ w + b >= 0).astype(int)

def dnn(X_train, y_train, X_test, hidden1=16, hidden2=8, learning_rate=0.01, epochs=1000, seed=42):
    X_train = np.asarray(X_train, dtype=float)
    X_test = np.asarray(X_test, dtype=float)
    y = np.asarray(y_train).reshape(-1, 1).astype(float)
    rng = np.random.default_rng(seed)
    W1 = rng.standard_normal((X_train.shape[1], hidden1)) * 0.01
    b1 = np.zeros((1, hidden1))
    W2 = rng.standard_normal((hidden1, hidden2)) * 0.01
    b2 = np.zeros((1, hidden2))
    W3 = rng.standard_normal((hidden2, 1)) * 0.01
    b3 = np.zeros((1, 1))
    for _ in range(epochs):
        Z1 = X_train @ W1 + b1
        A1 = np.maximum(0, Z1)
        Z2 = A1 @ W2 + b2
        A2 = np.maximum(0, Z2)
        Z3 = A2 @ W3 + b3
        A3 = 1 / (1 + np.exp(-np.clip(Z3, -500, 500)))
        m = len(X_train)
        dZ3 = A3 - y
        dW3 = A2.T @ dZ3 / m
        db3 = dZ3.mean(axis=0, keepdims=True)
        dA2 = dZ3 @ W3.T
        dZ2 = dA2 * (Z2 > 0)
        dW2 = A1.T @ dZ2 / m
        db2 = dZ2.mean(axis=0, keepdims=True)
        dA1 = dZ2 @ W2.T
        dZ1 = dA1 * (Z1 > 0)
        dW1 = X_train.T @ dZ1 / m
        db1 = dZ1.mean(axis=0, keepdims=True)
        W3 -= learning_rate * dW3
        b3 -= learning_rate * db3
        W2 -= learning_rate * dW2
        b2 -= learning_rate * db2
        W1 -= learning_rate * dW1
        b1 -= learning_rate * db1
    Z1 = X_test @ W1 + b1
    A1 = np.maximum(0, Z1)
    Z2 = A1 @ W2 + b2
    A2 = np.maximum(0, Z2)
    Z3 = A2 @ W3 + b3
    return (1 / (1 + np.exp(-np.clip(Z3.ravel(), -500, 500))) >= 0.5).astype(int)

def accuracy(y_true, y_pred):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    return np.mean(y_true == y_pred)

def confusion_matrix(y_true, y_pred):
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)
    labels = np.unique(np.concatenate([y_true, y_pred]))
    matrix = np.zeros((len(labels), len(labels)), dtype=int)
    for i, a in enumerate(labels):
        for j, b in enumerate(labels):
            matrix[i, j] = np.sum((y_true == a) & (y_pred == b))
    return matrix
