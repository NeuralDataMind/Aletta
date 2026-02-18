import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, f1_score, mean_squared_error, r2_score

class AutoModeler:
    def __init__(self, df: pd.DataFrame, target_col: str, project_id: int):
        self.df = df
        self.target_col = target_col
        self.project_id = project_id
        self.report = {}
        
        # Handle case where EDA encoded the target
        if target_col not in df.columns:
            if f"{target_col}_encoded" in df.columns:
                self.target_col = f"{target_col}_encoded"
            else:
                raise ValueError(f"Target column '{target_col}' not found. Run Analysis first.")

    def run_training(self):
        X = self.df.drop(columns=[self.target_col])
        y = self.df[self.target_col]
        
        # 1. Clean NaN in features
        X = X.fillna(0)
        
        # 2. Identify Task Type
        is_classification = self._is_classification(y)
        task_type = "Classification" if is_classification else "Regression"
        
        # 3. FIX: If Classification but target is float (due to scaling), fix it
        if is_classification and pd.api.types.is_float_dtype(y):
            y = LabelEncoder().fit_transform(y)

        # 4. Split Data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.report["task_type"] = task_type
        self.report["target_variable"] = self.target_col
        self.report["data_split"] = f"Train: {len(X_train)}, Test: {len(X_test)}"

        # 5. Race Models (WRAPPED IN PIPELINES)
        best_score = -np.inf
        best_pipeline = None
        best_model_name = "None"
        
        if is_classification:
            pipelines = {
                "Logistic Regression": Pipeline([
                    ('scaler', StandardScaler()), 
                    ('clf', LogisticRegression(max_iter=1000))
                ]),
                "Random Forest": Pipeline([
                    ('scaler', StandardScaler()), 
                    ('clf', RandomForestClassifier(n_estimators=100))
                ])
            }
            metric_name = "Accuracy"
        else:
            pipelines = {
                "Linear Regression": Pipeline([
                    ('scaler', StandardScaler()), 
                    ('reg', LinearRegression())
                ]),
                "Random Forest": Pipeline([
                    ('scaler', StandardScaler()), 
                    ('reg', RandomForestClassifier(n_estimators=100))
                ])
            }
            metric_name = "R2 Score"

        results = {}
        
        for name, pipeline in pipelines.items():
            try:
                pipeline.fit(X_train, y_train)
                preds = pipeline.predict(X_test)
                
                if is_classification:
                    score = accuracy_score(y_test, preds)
                else:
                    score = r2_score(y_test, preds)
                
                results[name] = {metric_name: round(float(score), 4)}
                
                if score > best_score:
                    best_score = score
                    best_pipeline = pipeline
                    best_model_name = name
            except Exception as e:
                results[name] = {"error": str(e)}

        # 6. JSON FAILSAFE
        if best_score == -np.inf:
            best_score = 0.0
            
        self.report["model_performance"] = results
        self.report["best_model"] = best_model_name
        self.report["best_score"] = round(float(best_score), 4)

        # 7. Feature Importance (EXTRACT FROM PIPELINE)
        if best_pipeline:
            # Get the actual model step (either 'clf' or 'reg')
            step_name = 'clf' if is_classification else 'reg'
            model_step = best_pipeline.named_steps[step_name]
            self._calculate_importance(model_step, best_model_name, X, is_classification)
        else:
            self.report["top_features"] = {}

        # 8. Save Pipeline (The Full Package)
        if best_pipeline:
            if not os.path.exists("data/models"):
                os.makedirs("data/models")
            model_path = f"data/models/project_{self.project_id}.pkl"
            joblib.dump(best_pipeline, model_path)
            self.report["model_path"] = model_path
        
        return self.report

    def _is_classification(self, y):
        if pd.api.types.is_integer_dtype(y) or pd.api.types.is_object_dtype(y):
            return True
        if y.nunique() <= 20: 
            return True
        return False

    def _calculate_importance(self, model, name, X, is_classification):
        try:
            importances = None
            if "Random Forest" in name:
                importances = model.feature_importances_
            elif "Linear" in name or "Logistic" in name:
                if is_classification and hasattr(model, "coef_"):
                    importances = np.mean(np.abs(model.coef_), axis=0)
                else:
                    importances = np.abs(model.coef_)
            
            if importances is not None:
                feature_names = X.columns
                indices = np.argsort(importances)[::-1][:5]
                top_features = {feature_names[i]: round(float(importances[i]), 3) for i in indices}
                self.report["top_features"] = top_features
            else:
                 self.report["top_features"] = {}
        except:
            self.report["top_features"] = {}

def run_auto_modeling(df: pd.DataFrame, target_col: str, project_id: int):
    modeler = AutoModeler(df, target_col, project_id)
    return modeler.run_training()