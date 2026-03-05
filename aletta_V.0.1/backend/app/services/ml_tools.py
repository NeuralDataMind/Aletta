import pandas as pd
import numpy as np
import joblib
import os
import re
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import TransformedTargetRegressor
from sklearn.metrics import accuracy_score, r2_score

# Require installation of: lightgbm, xgboost, catboost
from lightgbm import LGBMClassifier, LGBMRegressor
from xgboost import XGBClassifier, XGBRegressor
from catboost import CatBoostClassifier, CatBoostRegressor

class AutoModeler:
    def __init__(self, df: pd.DataFrame, target_col: str, project_id: int):
        self.df = df.copy()
        
        # LightGBM crashes if feature names contain special JSON characters. Fix them.
        self.df = self.df.rename(columns=lambda x: re.sub('[^A-Za-z0-9_]+', '', x))
        
        # Clean target column name in case it had special characters
        self.target_col = re.sub('[^A-Za-z0-9_]+', '', target_col)
        self.project_id = project_id
        self.report = {}
        
        if self.target_col not in self.df.columns:
            if f"{self.target_col}_encoded" in self.df.columns:
                self.target_col = f"{self.target_col}_encoded"
            else:
                raise ValueError(f"Target column '{self.target_col}' not found. Run Analysis first.")

    def _is_classification(self, y):
        if pd.api.types.is_object_dtype(y) or pd.api.types.is_bool_dtype(y):
            return True
        if y.nunique() <= 20: 
            return True
        return False

    def run_training(self):
        self.df = self.df.dropna(subset=[self.target_col])
        
        if pd.api.types.is_numeric_dtype(self.df[self.target_col]) and not self._is_classification(self.df[self.target_col]):
            self.df = self.df[self.df[self.target_col] > 0]
        
        X = self.df.drop(columns=[self.target_col])
        y = self.df[self.target_col]
        
        # REMOVED: X = X.fillna(...)
        # Gradient boosters handle NaNs natively and perform better when you leave them alone.

        is_classification = self._is_classification(y)
        task_type = "Classification" if is_classification else "Regression"
        
        if is_classification and (pd.api.types.is_object_dtype(y) or pd.api.types.is_float_dtype(y)):
            y = LabelEncoder().fit_transform(y.astype(str))

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.report["task_type"] = task_type
        self.report["target_variable"] = self.target_col
        self.report["data_split"] = f"Train: {len(X_train)}, Test: {len(X_test)}"

        best_score = -np.inf
        best_pipeline = None
        best_model_name = "None"
        
        # REMOVED StandardScaler: Tree models do not require feature scaling.
        if is_classification:
            pipelines = {
                "LightGBM": Pipeline([
                    ('clf', LGBMClassifier(random_state=42, verbose=-1))
                ]),
                "XGBoost": Pipeline([
                    ('clf', XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42))
                ]),
                "CatBoost": Pipeline([
                    ('clf', CatBoostClassifier(verbose=0, random_state=42))
                ])
            }
            metric_name = "Accuracy"
        else:
            pipelines = {
                "LightGBM": Pipeline([
                    ('reg', TransformedTargetRegressor(regressor=LGBMRegressor(random_state=42, verbose=-1), func=np.log1p, inverse_func=np.expm1))
                ]),
                "XGBoost": Pipeline([
                    ('reg', TransformedTargetRegressor(regressor=XGBRegressor(random_state=42), func=np.log1p, inverse_func=np.expm1))
                ]),
                "CatBoost": Pipeline([
                    ('reg', TransformedTargetRegressor(regressor=CatBoostRegressor(verbose=0, random_state=42), func=np.log1p, inverse_func=np.expm1))
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

        if best_score == -np.inf:
            best_score = 0.0
            
        self.report["model_performance"] = results
        self.report["best_model"] = best_model_name
        self.report["best_score"] = round(float(best_score), 4)

        if best_pipeline:
            step_name = 'clf' if is_classification else 'reg'
            model_step = best_pipeline.named_steps[step_name]
            
            if isinstance(model_step, TransformedTargetRegressor):
                model_step = model_step.regressor_
                
            self._calculate_importance(model_step, X)
        else:
            self.report["top_features"] = {}

        if best_pipeline:
            os.makedirs("data/models", exist_ok=True)
            model_path = f"data/models/project_{self.project_id}.pkl"
            joblib.dump(best_pipeline, model_path)
            self.report["model_path"] = model_path
        
        return self.report

    def _calculate_importance(self, model, X):
        try:
            importances = None
            if hasattr(model, "feature_importances_"):
                importances = model.feature_importances_
            
            if importances is not None:
                feature_names = X.columns
                indices = np.argsort(importances)[::-1][:5]
                
                total = np.sum(importances)
                if total > 0:
                    importances = importances / total
                    
                top_features = {feature_names[i]: round(float(importances[i]), 3) for i in indices}
                self.report["top_features"] = top_features
            else:
                self.report["top_features"] = {}
        except:
            self.report["top_features"] = {}

def run_auto_modeling(df: pd.DataFrame, target_col: str, project_id: int):
    modeler = AutoModeler(df, target_col, project_id)
    return modeler.run_training()