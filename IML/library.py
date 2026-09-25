import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def split(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    return X_train, X_test, y_train, y_test


def scaling(X_train, X_test):
    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    return X_train_scaled, X_test_scaled


def knn(X_train, y_train, X_test, k):
    from collections import Counter

    def euclidean_distance(point1, point2):
        return np.sqrt(np.sum((np.array(point1) - np.array(point2))**2))

    def knn_predict_single(X_train, y_train, test_point, k):
        distances = []
        for i in range(len(X_train)):
            dist = euclidean_distance(X_train[i], test_point)
            distances.append((dist, y_train[i]))
        
        distances.sort(key=lambda x: x[0])
        k_nearest = distances[:k]
        k_labels = [label for (_, label) in k_nearest]
        majority_vote = Counter(k_labels).most_common(1)[0][0]

        return majority_vote

    predictions = []
    for i in range(len(X_test)):
        pred = knn_predict_single(X_train, y_train.values, X_test[i], k)
        predictions.append(pred)
    
    return predictions


def centroid_based(X_train_scaled, y_train, X_test_scaled):
    def euclidean_distance(point1, point2):
        return np.sqrt(np.sum((np.array(point1) - np.array(point2))**2))

    def compute_centroids(X_train, y_train):
        centroids = {}
        for label in np.unique(y_train):
            class_points = X_train[y_train == label]
            centroids[label] = np.mean(class_points, axis=0)
        return centroids

    def centroid_predict_single(test_point, centroids):
        min_dist = float('inf')
        best_label = None
        for label, centroid in centroids.items():
            dist = euclidean_distance(test_point, centroid)
            if dist < min_dist:
                min_dist = dist
                best_label = label
        return best_label

    def centroid_predict(X_train, y_train, X_test):
        centroids = compute_centroids(X_train, y_train)
        predictions = []
        for i in range(len(X_test)):
            pred = centroid_predict_single(X_test[i], centroids)
            predictions.append(pred)
        return predictions

    y_pred = centroid_predict(X_train_scaled, y_train.values, X_test_scaled)

    return y_pred


def perceptron(X_train_scaled, y_train, X_test_scaled, eta, epochs):
    def step_activation(z):
        return 1 if z >= 0 else 0

    def perceptron_train_single(X, y_binary, eta, epochs):
        n_features = X.shape[1]
        w = np.zeros(n_features)
        b = 0.0

        for _ in range(epochs):
            for i in range(len(X)):
                z = np.dot(w, X[i]) + b
                y_pred = step_activation(z)
                error = y_pred - y_binary[i]
                w = w - eta * error * X[i]
                b = b - eta * error

        return w, b

    def perceptron_train_multiclass(X_train, y_train, classes, eta, epochs):
        models = {}
        for c in classes:
            y_binary = (y_train == c).astype(int)
            w, b = perceptron_train_single(X_train, y_binary, eta, epochs)
            models[c] = (w, b)
        return models

    def perceptron_predict_multiclass(models, x):
        scores = {}
        for c, (w, b) in models.items():
            scores[c] = np.dot(w, x) + b
        return max(scores, key=scores.get)

    def perceptron_predict_all(models, X):
        return [perceptron_predict_multiclass(models, X[i]) for i in range(len(X))]   

    classes = np.unique(y_train)
    models = perceptron_train_multiclass(X_train_scaled, y_train.values, classes, eta, epochs)

    y_train_pred = perceptron_predict_all(models, X_train_scaled)
    y_test_pred = perceptron_predict_all(models, X_test_scaled)

    return y_train_pred, y_test_pred


def linear_regression(X_train_scaled, y_train, X_test_scaled, eta, epochs):
    def train(X, y, eta, epochs):
        n_features = X.shape[1]
        w = np.zeros(n_features)
        b = 0.0

        for _ in range(epochs):
            for i in range(len(X)):
                y_pred = np.dot(w, X[i]) + b
                error = y_pred - y[i]

                w = w - eta * error * X[i]
                b = b - eta * error

        return w, b

    def predict(w, b, X):
        return [np.dot(w, x) + b for x in X]

    w, b = train(
        X_train_scaled,
        y_train.values,
        eta,
        epochs
    )

    y_train_pred = predict(w, b, X_train_scaled)
    y_test_pred = predict(w, b, X_test_scaled)

    return y_train_pred, y_test_pred


def linear_regression_2():
    def predict(X, w, b):
        return X @ w + b

    def mse_cost(y_true, y_pred):
        errors = y_true - y_pred
        return np.mean(errors ** 2)

    def train_linear_regression(X, y, learning_rate=0.01, epochs=1000):
        n_samples, n_features = X.shape

        w = np.zeros(n_features)
        b = 0.0

        mse_history = []

        for epoch in range(epochs):
            y_pred = predict(X, w, b)
            errors = y - y_pred

            dw = -(2 / n_samples) * (X.T @ errors)
            db = -(2 / n_samples) * np.sum(errors)

            w = w - learning_rate * dw
            b = b - learning_rate * db

            current_predictions = predict(X, w, b)
            current_mse = mse_cost(y, current_predictions)
            mse_history.append(current_mse)

        return w, b, mse_history

    

