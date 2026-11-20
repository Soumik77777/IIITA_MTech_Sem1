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

def split_data(X, y, test_size=0.2, random_state=42, stratify='no'):
    if stratify == 'yes':
        return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)
    else:
        return train_test_split(X, y, test_size=test_size, random_state=random_state)

def standardize(X_train, X_test=None):
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    if X_test is None:
        return X_train, scaler
    return X_train, scaler.transform(X_test), scaler

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


def decision_tree_id3(X, y, max_depth=4, min_samples_split=2, test_size=0.2, random_state=42):
    X = np.asarray(X, dtype=float)
    y = np.asarray(y).reshape(-1)
    rng = np.random.default_rng(random_state)
    indices = rng.permutation(len(X))
    n_test = max(1, int(np.ceil(len(X) * test_size)))
    test_idx, train_idx = indices[:n_test], indices[n_test:]
    X_train, X_test, y_train, y_test = X[train_idx], X[test_idx], y[train_idx], y[test_idx]
    classes = np.unique(y_train)
    nodes = [{"indices": np.arange(len(X_train)), "depth": 0, "parent": None, "side": None}]
    tree = []
    cursor = 0
    while cursor < len(nodes):
        node = nodes[cursor]
        ids = node["indices"]
        labels, counts = np.unique(y_train[ids], return_counts=True)
        prediction = labels[np.argmax(counts)]
        record = {"feature": None, "threshold": None, "left": None, "right": None, "prediction": prediction}
        stop = len(labels) == 1 or node["depth"] >= max_depth or len(ids) < min_samples_split
        best_gain, best_feature, best_threshold = 0.0, None, None
        if not stop:
            parent_p = counts / counts.sum()
            parent_entropy = -np.sum(parent_p * np.log2(parent_p + 1e-15))
            for feature in range(X_train.shape[1]):
                values = np.unique(X_train[ids, feature])
                if len(values) < 2:
                    continue
                thresholds = (values[:-1] + values[1:]) / 2
                for threshold in thresholds:
                    left_mask = X_train[ids, feature] <= threshold
                    right_mask = ~left_mask
                    if not left_mask.any() or not right_mask.any():
                        continue
                    gain = parent_entropy
                    for mask in (left_mask, right_mask):
                        _, c = np.unique(y_train[ids[mask]], return_counts=True)
                        p = c / c.sum()
                        gain -= mask.sum() / len(ids) * (-np.sum(p * np.log2(p + 1e-15)))
                    if gain > best_gain:
                        best_gain, best_feature, best_threshold = gain, feature, threshold
        if best_feature is not None:
            left_ids = ids[X_train[ids, best_feature] <= best_threshold]
            right_ids = ids[X_train[ids, best_feature] > best_threshold]
            record["feature"], record["threshold"] = best_feature, best_threshold
            record["left"] = len(nodes)
            nodes.append({"indices": left_ids, "depth": node["depth"] + 1, "parent": cursor, "side": "left"})
            record["right"] = len(nodes)
            nodes.append({"indices": right_ids, "depth": node["depth"] + 1, "parent": cursor, "side": "right"})
        tree.append(record)
        cursor += 1
    predictions = []
    for row in X_test:
        position = 0
        while tree[position]["feature"] is not None:
            current = tree[position]
            position = current["left"] if row[current["feature"]] <= current["threshold"] else current["right"]
        predictions.append(tree[position]["prediction"])
    predictions = np.asarray(predictions)
    return {"y_test": y_test, "y_pred": predictions, "accuracy": float(np.mean(predictions == y_test)), "tree": tree, "train_indices": train_idx, "test_indices": test_idx}


def naive_bayes(X, y, test_size=0.2, random_state=42, variance_smoothing=1e-9):
    X = np.asarray(X, dtype=float)
    y = np.asarray(y).reshape(-1)
    rng = np.random.default_rng(random_state)
    indices = rng.permutation(len(X))
    n_test = max(1, int(np.ceil(len(X) * test_size)))
    test_idx, train_idx = indices[:n_test], indices[n_test:]
    X_train, X_test, y_train, y_test = X[train_idx], X[test_idx], y[train_idx], y[test_idx]
    classes = np.unique(y_train)
    global_var = np.var(X_train, axis=0)
    epsilon = variance_smoothing * (np.max(global_var) if np.max(global_var) > 0 else 1.0)
    means, variances, priors = [], [], []
    for c in classes:
        subset = X_train[y_train == c]
        means.append(np.mean(subset, axis=0))
        variances.append(np.var(subset, axis=0) + epsilon)
        priors.append(len(subset) / len(X_train))
    means, variances, priors = np.asarray(means), np.asarray(variances), np.asarray(priors)
    scores = np.empty((len(X_test), len(classes)))
    for j in range(len(classes)):
        scores[:, j] = np.log(priors[j]) - 0.5 * np.sum(np.log(2 * np.pi * variances[j]) + (X_test - means[j]) ** 2 / variances[j], axis=1)
    predictions = classes[np.argmax(scores, axis=1)]
    return {"y_test": y_test, "y_pred": predictions, "accuracy": float(np.mean(predictions == y_test)), "classes": classes, "means": means, "variances": variances, "priors": priors, "train_indices": train_idx, "test_indices": test_idx}


def perceptron(X, y, learning_rate=0.1, epochs=20, test_size=0.2, random_state=42, threshold=0.0):
    X = np.asarray(X, dtype=float)
    y = np.asarray(y).reshape(-1)
    classes = np.unique(y)
    if len(classes) != 2:
        raise ValueError("Perceptron supports binary classification.")
    encoded = np.where(y == classes[1], 1.0, -1.0)
    rng = np.random.default_rng(random_state)
    indices = rng.permutation(len(X))
    n_test = max(1, int(np.ceil(len(X) * test_size)))
    test_idx, train_idx = indices[:n_test], indices[n_test:]
    X_train, X_test, y_train = X[train_idx], X[test_idx], encoded[train_idx]
    weights = np.zeros(X.shape[1])
    bias = 0.0
    history = []
    for _ in range(epochs):
        mistakes = 0
        for i in rng.permutation(len(X_train)):
            if y_train[i] * (X_train[i] @ weights + bias) <= threshold:
                weights += learning_rate * y_train[i] * X_train[i]
                bias += learning_rate * y_train[i]
                mistakes += 1
        history.append(mistakes)
    scores = X_test @ weights + bias
    predictions = np.where(scores >= threshold, classes[1], classes[0])
    y_test = y[test_idx]
    return {"y_test": y_test, "y_pred": predictions, "accuracy": float(np.mean(predictions == y_test)), "weights": weights, "bias": bias, "mistakes_history": np.asarray(history), "classes": classes, "train_indices": train_idx, "test_indices": test_idx}


def mlp(X, y, hidden1=16, hidden2=8, activation="relu", learning_rate=0.01, epochs=2000, seed=42, test_size=0.2, threshold=0.5, alpha=0.01):
    X = np.asarray(X, dtype=float)
    y = np.asarray(y).reshape(-1, 1).astype(float)
    classes = np.unique(y)
    if len(classes) != 2:
        raise ValueError("MLP currently supports binary classification.")
    y_encoded = (y == classes[1]).astype(float)
    rng = np.random.default_rng(seed)
    indices = rng.permutation(len(X))
    n_test = max(1, int(np.ceil(len(X) * test_size)))
    test_idx, train_idx = indices[:n_test], indices[n_test:]
    A, B = X[train_idx], y_encoded[train_idx]
    X_test, y_test = X[test_idx], y[test_idx].ravel()
    if activation not in ("sigmoid", "tanh", "relu", "leaky_relu", "prelu", "elu", "selu", "gelu"):
        raise ValueError("Unsupported activation.")
    scale = np.sqrt(2 / max(1, X.shape[1]))
    W1 = rng.normal(0, scale, (X.shape[1], hidden1))
    W2 = rng.normal(0, np.sqrt(2 / hidden1), (hidden1, hidden2))
    W3 = rng.normal(0, np.sqrt(1 / hidden2), (hidden2, 1))
    b1, b2, b3 = np.zeros((1, hidden1)), np.zeros((1, hidden2)), np.zeros((1, 1))
    loss_history = []
    for _ in range(epochs):
        Z1 = A @ W1 + b1
        Z2_pre = Z1
        if activation == "sigmoid":
            H1 = 1 / (1 + np.exp(-np.clip(Z1, -500, 500)))
            D1 = H1 * (1 - H1)
        elif activation == "tanh":
            H1 = np.tanh(Z1)
            D1 = 1 - H1 ** 2
        elif activation in ("relu", "leaky_relu", "prelu"):
            H1 = np.maximum(alpha * Z1, Z1)
            D1 = np.where(Z1 > 0, 1.0, alpha)
        elif activation == "elu":
            H1 = np.where(Z1 > 0, Z1, alpha * (np.exp(np.clip(Z1, -500, 500)) - 1))
            D1 = np.where(Z1 > 0, 1.0, H1 + alpha)
        elif activation == "selu":
            H1 = 1.0507 * np.where(Z1 > 0, Z1, 1.67326 * (np.exp(np.clip(Z1, -500, 500)) - 1))
            D1 = 1.0507 * np.where(Z1 > 0, 1.0, 1.67326 * np.exp(np.clip(Z1, -500, 500)))
        else:
            H1 = 0.5 * Z1 * (1 + np.tanh(np.sqrt(2 / np.pi) * (Z1 + 0.044715 * Z1 ** 3)))
            D1 = 0.5 * (1 + np.tanh(np.sqrt(2 / np.pi) * (Z1 + 0.044715 * Z1 ** 3))) + 0.5 * Z1 * (1 - np.tanh(np.sqrt(2 / np.pi) * (Z1 + 0.044715 * Z1 ** 3)) ** 2) * np.sqrt(2 / np.pi) * (1 + 0.134145 * Z1 ** 2)
        Z2 = H1 @ W2 + b2
        if activation == "sigmoid":
            H2 = 1 / (1 + np.exp(-np.clip(Z2, -500, 500)))
            D2 = H2 * (1 - H2)
        elif activation == "tanh":
            H2 = np.tanh(Z2)
            D2 = 1 - H2 ** 2
        elif activation in ("relu", "leaky_relu", "prelu"):
            H2 = np.maximum(alpha * Z2, Z2)
            D2 = np.where(Z2 > 0, 1.0, alpha)
        elif activation == "elu":
            H2 = np.where(Z2 > 0, Z2, alpha * (np.exp(np.clip(Z2, -500, 500)) - 1))
            D2 = np.where(Z2 > 0, 1.0, H2 + alpha)
        elif activation == "selu":
            H2 = 1.0507 * np.where(Z2 > 0, Z2, 1.67326 * (np.exp(np.clip(Z2, -500, 500)) - 1))
            D2 = 1.0507 * np.where(Z2 > 0, 1.0, 1.67326 * np.exp(np.clip(Z2, -500, 500)))
        else:
            T = np.tanh(np.sqrt(2 / np.pi) * (Z2 + 0.044715 * Z2 ** 3))
            H2 = 0.5 * Z2 * (1 + T)
            D2 = 0.5 * (1 + T) + 0.5 * Z2 * (1 - T ** 2) * np.sqrt(2 / np.pi) * (1 + 0.134145 * Z2 ** 2)
        Z3 = H2 @ W3 + b3
        P = 1 / (1 + np.exp(-np.clip(Z3, -500, 500)))
        m = len(A)
        dZ3 = P - B
        dW3 = H2.T @ dZ3 / m
        db3 = np.mean(dZ3, axis=0, keepdims=True)
        dZ2 = (dZ3 @ W3.T) * D2
        dW2 = H1.T @ dZ2 / m
        db2 = np.mean(dZ2, axis=0, keepdims=True)
        dZ1 = (dZ2 @ W2.T) * D1
        dW1 = A.T @ dZ1 / m
        db1 = np.mean(dZ1, axis=0, keepdims=True)
        W3 -= learning_rate * dW3
        b3 -= learning_rate * db3
        W2 -= learning_rate * dW2
        b2 -= learning_rate * db2
        W1 -= learning_rate * dW1
        b1 -= learning_rate * db1
        loss_history.append(float(-np.mean(B * np.log(P + 1e-12) + (1 - B) * np.log(1 - P + 1e-12))))
    Z1 = X_test @ W1 + b1
    if activation == "sigmoid":
        H1 = 1 / (1 + np.exp(-np.clip(Z1, -500, 500)))
    elif activation == "tanh":
        H1 = np.tanh(Z1)
    elif activation in ("relu", "leaky_relu", "prelu"):
        H1 = np.maximum(alpha * Z1, Z1)
    elif activation == "elu":
        H1 = np.where(Z1 > 0, Z1, alpha * (np.exp(np.clip(Z1, -500, 500)) - 1))
    elif activation == "selu":
        H1 = 1.0507 * np.where(Z1 > 0, Z1, 1.67326 * (np.exp(np.clip(Z1, -500, 500)) - 1))
    else:
        H1 = 0.5 * Z1 * (1 + np.tanh(np.sqrt(2 / np.pi) * (Z1 + 0.044715 * Z1 ** 3)))
    Z2 = H1 @ W2 + b2
    if activation == "sigmoid":
        H2 = 1 / (1 + np.exp(-np.clip(Z2, -500, 500)))
    elif activation == "tanh":
        H2 = np.tanh(Z2)
    elif activation in ("relu", "leaky_relu", "prelu"):
        H2 = np.maximum(alpha * Z2, Z2)
    elif activation == "elu":
        H2 = np.where(Z2 > 0, Z2, alpha * (np.exp(np.clip(Z2, -500, 500)) - 1))
    elif activation == "selu":
        H2 = 1.0507 * np.where(Z2 > 0, Z2, 1.67326 * (np.exp(np.clip(Z2, -500, 500)) - 1))
    else:
        H2 = 0.5 * Z2 * (1 + np.tanh(np.sqrt(2 / np.pi) * (Z2 + 0.044715 * Z2 ** 3)))
    probabilities = (1 / (1 + np.exp(-np.clip(H2 @ W3 + b3, -500, 500)))).ravel()
    predictions = np.where(probabilities >= threshold, classes[1], classes[0])
    return {"y_test": y_test, "y_pred": predictions, "probabilities": probabilities, "accuracy": float(np.mean(predictions == y_test)), "weights": (W1, W2, W3), "biases": (b1, b2, b3), "loss_history": np.asarray(loss_history), "classes": classes, "train_indices": train_idx, "test_indices": test_idx}


def svm_classifier(X, y, kernel="rbf", C=1.0, gamma=0.01, degree=3, learning_rate=0.001, epochs=1000, test_size=0.2, random_state=42):
    X = np.asarray(X, dtype=float)
    y = np.asarray(y).reshape(-1)
    classes = np.unique(y)
    if len(classes) != 2:
        raise ValueError("This SVM implementation supports binary classification.")
    targets = np.where(y == classes[1], 1.0, -1.0)
    rng = np.random.default_rng(random_state)
    indices = rng.permutation(len(X))
    n_test = max(1, int(np.ceil(len(X) * test_size)))
    test_idx, train_idx = indices[:n_test], indices[n_test:]
    A, B = X[train_idx], targets[train_idx]
    T, y_test = X[test_idx], y[test_idx]
    if kernel == "linear":
        transform = lambda a, b: a @ b.T
    elif kernel == "rbf":
        transform = lambda a, b: np.exp(-gamma * np.maximum(0, np.sum(a*a, axis=1)[:, None] + np.sum(b*b, axis=1)[None, :] - 2 * a @ b.T))
    elif kernel == "poly":
        transform = lambda a, b: (gamma * (a @ b.T) + 1) ** degree
    elif kernel == "sigmoid":
        transform = lambda a, b: np.tanh(gamma * (a @ b.T) + 1)
    else:
        raise ValueError("kernel must be linear, poly, rbf, or sigmoid.")
    K = transform(A, A)
    alpha = np.zeros(len(A))
    for _ in range(epochs):
        margins = B * (K @ alpha)
        for i in range(len(A)):
            if margins[i] < 1:
                alpha[i] = min(C, alpha[i] + learning_rate * (1 - margins[i]))
    scores = transform(T, A) @ (alpha * B)
    predictions = np.where(scores >= 0, classes[1], classes[0])
    return {"y_test": y_test, "y_pred": predictions, "accuracy": float(np.mean(predictions == y_test)), "support_indices": train_idx[alpha > 1e-8], "dual_coefficients": alpha * B, "training_X": A, "kernel": kernel, "classes": classes, "train_indices": train_idx, "test_indices": test_idx}


def linear_regression(X, y, learning_rate=0.01, n_iters=1000, method="gradient_descent", test_size=0.2, random_state=42):
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float).reshape(-1, 1)
    rng = np.random.default_rng(random_state)
    indices = rng.permutation(len(X))
    n_test = max(1, int(np.ceil(len(X) * test_size)))
    test_idx, train_idx = indices[:n_test], indices[n_test:]
    A, B = X[train_idx], y[train_idx]
    T, y_test = X[test_idx], y[test_idx]
    if method == "analytical":
        design = np.column_stack([np.ones(len(A)), A])
        params = np.linalg.pinv(design) @ B
        bias, weights = params[0], params[1:]
        history = np.array([])
    elif method == "gradient_descent":
        weights = np.zeros((X.shape[1], 1))
        bias = np.zeros((1, 1))
        history = []
        for _ in range(n_iters):
            error = A @ weights + bias - B
            weights -= learning_rate * (2 / len(A)) * (A.T @ error)
            bias -= learning_rate * (2 / len(A)) * np.sum(error, axis=0, keepdims=True)
            history.append(float(np.mean(error ** 2)))
        history = np.asarray(history)
    else:
        raise ValueError("method must be gradient_descent or analytical.")
    predictions = T @ weights + bias
    mse = float(np.mean((predictions - y_test) ** 2))
    denominator = np.sum((y_test - np.mean(y_test)) ** 2)
    r2 = float(1 - np.sum((predictions - y_test) ** 2) / denominator) if denominator > 0 else float("nan")
    return {"y_test": y_test, "y_pred": predictions, "mse": mse, "r2": r2, "weights": weights, "bias": bias, "cost_history": history, "train_indices": train_idx, "test_indices": test_idx}


def apriori(X, min_support=0.2, min_confidence=0.7):
    X = np.asarray(X, dtype=object)
    transactions = []
    for row in X:
        transactions.append(frozenset((j, str(value)) for j, value in enumerate(row) if value is not None and str(value) != "nan"))
    n = len(transactions)
    item_counts = {}
    for transaction in transactions:
        for item in transaction:
            item_counts[item] = item_counts.get(item, 0) + 1
    current = {frozenset([item]): count / n for item, count in item_counts.items() if count / n >= min_support}
    frequent = dict(current)
    k = 2
    while current:
        previous = list(current.keys())
        candidates = set()
        for i in range(len(previous)):
            for j in range(i + 1, len(previous)):
                candidate = previous[i] | previous[j]
                if len(candidate) == k and all(frozenset(subset) in current for subset in __import__("itertools").combinations(candidate, k - 1)):
                    candidates.add(candidate)
        next_level = {}
        for candidate in candidates:
            count = sum(candidate.issubset(transaction) for transaction in transactions)
            support = count / n
            if support >= min_support:
                next_level[candidate] = support
        frequent.update(next_level)
        current = next_level
        k += 1
    rules = []
    for itemset, support in frequent.items():
        if len(itemset) < 2:
            continue
        items = list(itemset)
        for mask in range(1, (1 << len(items)) - 1):
            antecedent = frozenset(items[i] for i in range(len(items)) if mask & (1 << i))
            consequent = itemset - antecedent
            antecedent_support = frequent.get(antecedent, sum(antecedent.issubset(t) for t in transactions) / n)
            confidence = support / antecedent_support
            if confidence >= min_confidence:
                rules.append({"antecedent": antecedent, "consequent": consequent, "support": support, "confidence": confidence, "lift": confidence / (frequent.get(consequent, sum(consequent.issubset(t) for t in transactions) / n))})
    return {"frequent_itemsets": frequent, "rules": rules}


def fp_growth(X, min_support=0.2, min_confidence=0.7):
    X = np.asarray(X, dtype=object)
    transactions = [frozenset((j, str(value)) for j, value in enumerate(row) if value is not None and str(value) != "nan") for row in X]
    n = len(transactions)
    counts = {}
    for transaction in transactions:
        for item in transaction:
            counts[item] = counts.get(item, 0) + 1
    minimum = int(np.ceil(min_support * n))
    frequent_items = {item: count for item, count in counts.items() if count >= minimum}
    ordered_transactions = []
    for transaction in transactions:
        ordered_transactions.append(sorted([item for item in transaction if item in frequent_items], key=lambda item: (-frequent_items[item], item)))
    root = {"item": None, "count": 0, "parent": None, "children": {}, "links": []}
    header = {}
    for transaction in ordered_transactions:
        node = root
        for item in transaction:
            if item not in node["children"]:
                child = {"item": item, "count": 0, "parent": node, "children": {}, "links": []}
                node["children"][item] = child
                if item not in header:
                    header[item] = []
                header[item].append(child)
            node = node["children"][item]
            node["count"] += 1
    frequent = {}
    stack = [(frozenset(), dict(header))]
    while stack:
        suffix, local_header = stack.pop()
        for item in sorted(local_header, key=lambda z: (sum(node["count"] for node in local_header[z]), z)):
            support_count = sum(node["count"] for node in local_header[item])
            pattern = suffix | frozenset([item])
            frequent[pattern] = support_count / n
            conditional_counts = {}
            conditional_paths = []
            for node in local_header[item]:
                path = []
                parent = node["parent"]
                while parent is not None and parent["item"] is not None:
                    path.append(parent["item"])
                    parent = parent["parent"]
                if path:
                    conditional_paths.append((path, node["count"]))
                    for ancestor in path:
                        conditional_counts[ancestor] = conditional_counts.get(ancestor, 0) + node["count"]
            conditional_counts = {key: value for key, value in conditional_counts.items() if value >= minimum}
            if conditional_counts:
                conditional_header = {key: [] for key in conditional_counts}
                conditional_root = {"item": None, "count": 0, "parent": None, "children": {}}
                for path, path_count in conditional_paths:
                    filtered = [z for z in path if z in conditional_counts]
                    filtered.sort(key=lambda z: (-conditional_counts[z], z))
                    current_node = conditional_root
                    for ancestor in filtered:
                        if ancestor not in current_node["children"]:
                            child = {"item": ancestor, "count": 0, "parent": current_node, "children": {}}
                            current_node["children"][ancestor] = child
                            conditional_header[ancestor].append(child)
                        current_node = current_node["children"][ancestor]
                        current_node["count"] += path_count
                stack.append((pattern, conditional_header))
    rules = []
    for itemset, support in frequent.items():
        if len(itemset) < 2:
            continue
        items = list(itemset)
        for mask in range(1, (1 << len(items)) - 1):
            antecedent = frozenset(items[i] for i in range(len(items)) if mask & (1 << i))
            consequent = itemset - antecedent
            antecedent_support = sum(antecedent.issubset(t) for t in transactions) / n
            consequent_support = sum(consequent.issubset(t) for t in transactions) / n
            confidence = support / antecedent_support
            if confidence >= min_confidence:
                rules.append({"antecedent": antecedent, "consequent": consequent, "support": support, "confidence": confidence, "lift": confidence / consequent_support})
    return {"frequent_itemsets": frequent, "rules": rules}


def kmedoids_pam(X, k=3, max_iter=100, metric="euclidean", random_state=42):
    X = np.asarray(X, dtype=float)
    rng = np.random.default_rng(random_state)
    if metric == "euclidean":
        D = np.sqrt(np.maximum(0, np.sum(X * X, axis=1)[:, None] + np.sum(X * X, axis=1)[None, :] - 2 * X @ X.T))
    elif metric == "manhattan":
        D = np.sum(np.abs(X[:, None, :] - X[None, :, :]), axis=2)
    else:
        raise ValueError("metric must be euclidean or manhattan.")
    medoids = rng.choice(len(X), size=k, replace=False)
    for _ in range(max_iter):
        labels = np.argmin(D[:, medoids], axis=1)
        updated = medoids.copy()
        for cluster in range(k):
            members = np.where(labels == cluster)[0]
            if len(members):
                costs = np.sum(D[np.ix_(members, members)], axis=1)
                updated[cluster] = members[np.argmin(costs)]
        if np.array_equal(updated, medoids):
            break
        medoids = updated
    labels = np.argmin(D[:, medoids], axis=1)
    return {"labels": labels, "medoid_indices": medoids, "medoids": X[medoids], "cost": float(np.sum(np.min(D[:, medoids], axis=1))), "distance_matrix": D}


def kmedoids_clara(X, k=3, sample_size=40, num_samples=5, max_iter=100, metric="euclidean", random_state=42):
    X = np.asarray(X, dtype=float)
    rng = np.random.default_rng(random_state)
    sample_size = min(max(k, sample_size), len(X))
    if metric == "euclidean":
        D = np.sqrt(np.maximum(0, np.sum(X * X, axis=1)[:, None] + np.sum(X * X, axis=1)[None, :] - 2 * X @ X.T))
    elif metric == "manhattan":
        D = np.sum(np.abs(X[:, None, :] - X[None, :, :]), axis=2)
    else:
        raise ValueError("metric must be euclidean or manhattan.")
    best_cost, best_medoids = np.inf, None
    for _ in range(num_samples):
        sample = rng.choice(len(X), size=sample_size, replace=False)
        sample_D = D[np.ix_(sample, sample)]
        medoids_local = rng.choice(sample_size, size=k, replace=False)
        for _ in range(max_iter):
            labels = np.argmin(sample_D[:, medoids_local], axis=1)
            updated = medoids_local.copy()
            for cluster in range(k):
                members = np.where(labels == cluster)[0]
                if len(members):
                    updated[cluster] = members[np.argmin(np.sum(sample_D[np.ix_(members, members)], axis=1))]
            if np.array_equal(updated, medoids_local):
                break
            medoids_local = updated
        medoids_global = sample[medoids_local]
        cost = float(np.sum(np.min(D[:, medoids_global], axis=1)))
        if cost < best_cost:
            best_cost, best_medoids = cost, medoids_global.copy()
    labels = np.argmin(D[:, best_medoids], axis=1)
    return {"labels": labels, "medoid_indices": best_medoids, "medoids": X[best_medoids], "cost": best_cost}


def kmedoids_clarans(X, k=3, num_local=5, max_neighbors=20, metric="euclidean", random_state=42):
    X = np.asarray(X, dtype=float)
    rng = np.random.default_rng(random_state)
    if metric == "euclidean":
        D = np.sqrt(np.maximum(0, np.sum(X * X, axis=1)[:, None] + np.sum(X * X, axis=1)[None, :] - 2 * X @ X.T))
    elif metric == "manhattan":
        D = np.sum(np.abs(X[:, None, :] - X[None, :, :]), axis=2)
    else:
        raise ValueError("metric must be euclidean or manhattan.")
    best_cost, best_medoids = np.inf, None
    for _ in range(num_local):
        medoids = rng.choice(len(X), size=k, replace=False)
        current_cost = float(np.sum(np.min(D[:, medoids], axis=1)))
        neighbors = 0
        while neighbors < max_neighbors:
            slot = rng.integers(k)
            candidates = np.setdiff1d(np.arange(len(X)), medoids)
            candidate = rng.choice(candidates)
            proposal = medoids.copy()
            proposal[slot] = candidate
            proposal_cost = float(np.sum(np.min(D[:, proposal], axis=1)))
            if proposal_cost < current_cost:
                medoids, current_cost, neighbors = proposal, proposal_cost, 0
            else:
                neighbors += 1
        if current_cost < best_cost:
            best_cost, best_medoids = current_cost, medoids.copy()
    labels = np.argmin(D[:, best_medoids], axis=1)
    return {"labels": labels, "medoid_indices": best_medoids, "medoids": X[best_medoids], "cost": best_cost}


def dbscan(X, eps=0.8, min_pts=5, metric="euclidean"):
    X = np.asarray(X, dtype=float)
    if metric == "euclidean":
        D = np.sqrt(np.maximum(0, np.sum(X * X, axis=1)[:, None] + np.sum(X * X, axis=1)[None, :] - 2 * X @ X.T))
    elif metric == "manhattan":
        D = np.sum(np.abs(X[:, None, :] - X[None, :, :]), axis=2)
    else:
        raise ValueError("metric must be euclidean or manhattan.")
    labels = np.full(len(X), -1, dtype=int)
    visited = np.zeros(len(X), dtype=bool)
    cluster_id = 0
    for point in range(len(X)):
        if visited[point]:
            continue
        visited[point] = True
        neighbors = np.where(D[point] <= eps)[0]
        if len(neighbors) < min_pts:
            continue
        labels[point] = cluster_id
        queue = list(neighbors)
        queued = set(queue)
        position = 0
        while position < len(queue):
            neighbor = queue[position]
            position += 1
            if not visited[neighbor]:
                visited[neighbor] = True
                neighbor_neighbors = np.where(D[neighbor] <= eps)[0]
                if len(neighbor_neighbors) >= min_pts:
                    for item in neighbor_neighbors:
                        if item not in queued:
                            queue.append(item)
                            queued.add(item)
            if labels[neighbor] == -1:
                labels[neighbor] = cluster_id
        cluster_id += 1
    return {"labels": labels, "n_clusters": int(len(set(labels)) - (1 if -1 in labels else 0)), "n_noise": int(np.sum(labels == -1)), "distance_matrix": D}


def hierarchical_clustering(X, n_clusters=3, linkage="average", metric="euclidean"):
    X = np.asarray(X, dtype=float)
    if metric == "euclidean":
        D = np.sqrt(np.maximum(0, np.sum(X * X, axis=1)[:, None] + np.sum(X * X, axis=1)[None, :] - 2 * X @ X.T))
    elif metric == "manhattan":
        D = np.sum(np.abs(X[:, None, :] - X[None, :, :]), axis=2)
    else:
        raise ValueError("metric must be euclidean or manhattan.")
    if linkage not in ("single", "complete", "average"):
        raise ValueError("linkage must be single, complete, or average.")
    clusters = [{i} for i in range(len(X))]
    merge_history = []
    while len(clusters) > n_clusters:
        best = (None, None, np.inf)
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                distances = D[np.ix_(list(clusters[i]), list(clusters[j]))]
                if linkage == "single":
                    distance = np.min(distances)
                elif linkage == "complete":
                    distance = np.max(distances)
                else:
                    distance = np.mean(distances)
                if distance < best[2]:
                    best = (i, j, distance)
        i, j, distance = best
        merged = clusters[i] | clusters[j]
        merge_history.append((sorted(clusters[i]), sorted(clusters[j]), float(distance)))
        clusters = [cluster for index, cluster in enumerate(clusters) if index not in (i, j)]
        clusters.append(merged)
    labels = np.empty(len(X), dtype=int)
    for cluster_id, cluster in enumerate(clusters):
        for index in cluster:
            labels[index] = cluster_id
    return {"labels": labels, "clusters": [sorted(cluster) for cluster in clusters], "merge_history": merge_history, "distance_matrix": D}
