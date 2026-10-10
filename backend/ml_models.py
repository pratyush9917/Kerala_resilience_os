"""
Pure-NumPy Resilient Machine Learning Engine
Implements:
  - GradientBoostingClassifier (Rainfall Hazard Stage A)
  - GradientBoostingRegressor (Risk Refinement Stage C)
  - RandomForestMultiLabel (Action Planner Module 3)

Engineered for 100% cross-platform resilience and zero DLL dependency failure.
Exposes standard scikit-learn compatible fit(), predict(), predict_proba() interfaces.
"""
import numpy as np

class DecisionStump:
    def __init__(self):
        self.feature_idx = 0
        self.threshold = 0.0
        self.left_val = 0.0
        self.right_val = 0.0

    def fit(self, X, residuals, max_features=None):
        n_samples, n_features = X.shape
        features_to_check = range(n_features)
        if max_features and max_features < n_features:
            features_to_check = np.random.choice(n_features, max_features, replace=False)

        best_loss = float("inf")
        best_feat = 0
        best_thresh = 0.0
        best_left_val = float(np.mean(residuals))
        best_right_val = best_left_val

        for f in features_to_check:
            vals = X[:, f]
            thresholds = np.percentile(vals, np.linspace(10, 90, 9))
            for t in thresholds:
                left_mask = vals <= t
                right_mask = ~left_mask
                if not np.any(left_mask) or not np.any(right_mask):
                    continue
                l_val = float(np.mean(residuals[left_mask]))
                r_val = float(np.mean(residuals[right_mask]))
                loss = np.sum((residuals[left_mask] - l_val) ** 2) + np.sum((residuals[right_mask] - r_val) ** 2)
                if loss < best_loss:
                    best_loss = loss
                    best_feat = f
                    best_thresh = t
                    best_left_val = l_val
                    best_right_val = r_val

        self.feature_idx = best_feat
        self.threshold = best_thresh
        self.left_val = best_left_val
        self.right_val = best_right_val
        return self

    def predict(self, X):
        mask = X[:, self.feature_idx] <= self.threshold
        return np.where(mask, self.left_val, self.right_val)


class TreeNode:
    def __init__(self, depth=0, max_depth=3):
        self.depth = depth
        self.max_depth = max_depth
        self.stump = None
        self.left_child = None
        self.right_child = None
        self.leaf_val = 0.0

    def fit(self, X, y, max_features=None):
        self.leaf_val = float(np.mean(y)) if len(y) > 0 else 0.0
        if self.depth >= self.max_depth or len(y) < 10 or np.all(y == y[0]):
            return self

        self.stump = DecisionStump().fit(X, y, max_features=max_features)
        mask = X[:, self.stump.feature_idx] <= self.stump.threshold

        if np.any(mask) and np.any(~mask):
            self.left_child = TreeNode(depth=self.depth + 1, max_depth=self.max_depth).fit(X[mask], y[mask], max_features)
            self.right_child = TreeNode(depth=self.depth + 1, max_depth=self.max_depth).fit(X[~mask], y[~mask], max_features)
        return self

    def predict(self, X):
        if self.stump is None or self.left_child is None or self.right_child is None:
            return np.full(X.shape[0], self.leaf_val)

        mask = X[:, self.stump.feature_idx] <= self.stump.threshold
        preds = np.zeros(X.shape[0])
        if np.any(mask):
            preds[mask] = self.left_child.predict(X[mask])
        if np.any(~mask):
            preds[~mask] = self.right_child.predict(X[~mask])
        return preds


class ResilientGradientBoostingRegressor:
    """
    Gradient Boosting Regressor matching scikit-learn API.
    Used for non-linear risk score refinement.
    """
    def __init__(self, n_estimators=60, learning_rate=0.08, max_depth=2, random_state=42):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.random_state = random_state
        self.trees = []
        self.init_val = 0.0
        self.feature_importances_ = None

    def fit(self, X, y):
        np.random.seed(self.random_state)
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        n_samples, n_features = X.shape

        self.init_val = float(np.mean(y))
        y_pred = np.full(n_samples, self.init_val)
        self.trees = []
        feat_counts = np.zeros(n_features)

        for _ in range(self.n_estimators):
            residuals = y - y_pred
            tree = TreeNode(max_depth=self.max_depth).fit(X, residuals)
            step_pred = tree.predict(X)
            y_pred += self.learning_rate * step_pred
            self.trees.append(tree)
            if tree.stump:
                feat_counts[tree.stump.feature_idx] += 1

        total = np.sum(feat_counts)
        self.feature_importances_ = feat_counts / (total if total > 0 else 1)
        return self

    def predict(self, X):
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        y_pred = np.full(X.shape[0], self.init_val, dtype=float)
        for t in self.trees:
            y_pred += self.learning_rate * t.predict(X)
        return np.clip(y_pred, 0.0, 1.0)


class ResilientGradientBoostingClassifier:
    """
    Gradient Boosting Classifier matching scikit-learn API.
    Used for Stage A: 118-year Kerala rainfall hazard modeling.
    """
    def __init__(self, n_estimators=50, learning_rate=0.08, random_state=42):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.random_state = random_state
        self.trees = []
        self.init_log_odds = 0.0

    def fit(self, X, y):
        np.random.seed(self.random_state)
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        n_samples = len(y)

        p = max(0.01, min(0.99, np.mean(y)))
        self.init_log_odds = np.log(p / (1.0 - p))
        raw_preds = np.full(n_samples, self.init_log_odds)
        self.trees = []

        for _ in range(self.n_estimators):
            prob = 1.0 / (1.0 + np.exp(-np.clip(raw_preds, -15, 15)))
            residuals = y - prob
            tree = TreeNode(max_depth=2).fit(X, residuals)
            step = tree.predict(X)
            raw_preds += self.learning_rate * step
            self.trees.append(tree)
        return self

    def predict_proba(self, X):
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        raw_preds = np.full(X.shape[0], self.init_log_odds, dtype=float)
        for t in self.trees:
            raw_preds += self.learning_rate * t.predict(X)
        prob_1 = 1.0 / (1.0 + np.exp(-np.clip(raw_preds, -15, 15)))
        prob_0 = 1.0 - prob_1
        return np.column_stack([prob_0, prob_1])

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)


class ResilientRandomForestMultiLabel:
    """
    Random Forest Multi-label Classifier for the 6 emergency actions:
    [Evacuation, Open shelters, Deploy pumps, Close roads, Alert hospitals, Public alert]
    Produces probability for each action per zone.
    """
    def __init__(self, n_estimators=30, max_depth=3, max_features=None, random_state=42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.max_features = max_features
        self.random_state = random_state
        self.label_models = {}
        self.labels = []
        self.feature_importances_ = None

    def fit(self, X, Y, labels=None):
        np.random.seed(self.random_state)
        X = np.asarray(X, dtype=float)
        Y = np.asarray(Y, dtype=float)
        n_samples, n_features = X.shape
        n_labels = Y.shape[1]
        self.labels = labels if labels is not None else [f"action_{i}" for i in range(n_labels)]
        self.label_models = {}

        all_importances = np.zeros(n_features)

        for j, label in enumerate(self.labels):
            y_col = Y[:, j]
            trees = []
            for t_idx in range(self.n_estimators):
                indices = np.random.choice(n_samples, n_samples, replace=True)
                X_b, y_b = X[indices], y_col[indices]
                tree = TreeNode(max_depth=self.max_depth).fit(X_b, y_b, max_features=self.max_features)
                trees.append(tree)
                if tree.stump:
                    all_importances[tree.stump.feature_idx] += 1
            self.label_models[label] = trees

        total = np.sum(all_importances)
        self.feature_importances_ = all_importances / (total if total > 0 else 1)
        return self

    def predict_proba(self, X):
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        n_samples = X.shape[0]

        output = []
        for label in self.labels:
            trees = self.label_models[label]
            preds = np.zeros(n_samples)
            for tree in trees:
                preds += tree.predict(X)
            prob_1 = np.clip(preds / len(trees), 0.02, 0.98)
            prob_0 = 1.0 - prob_1
            output.append(np.column_stack([prob_0, prob_1]))
        return output

    def predict(self, X):
        probas = self.predict_proba(X)
        return np.column_stack([(p[:, 1] >= 0.5).astype(int) for p in probas])
