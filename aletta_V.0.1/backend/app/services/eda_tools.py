import pandas as pd
import numpy as np
import json
import re  # <--- NEW IMPORT
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.impute import SimpleImputer

# Import the AI function
try:
    from app.core.ai import get_engineering_strategy
except ImportError:
    get_engineering_strategy = None

class AutoDataEngineer:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy() 
        self.log = []
        self.original_shape = df.shape

    def log_step(self, message):
        self.log.append(message)

    def run_pipeline(self):
        self.log_step(f"🚀 Starting Auto-Engineering on {self.original_shape[0]} rows, {self.original_shape[1]} columns.")
        
        # --- PHASE 1: CLEANING ---
        ai_success = False
        if get_engineering_strategy:
            try:
                self._apply_ai_cleaning_strategy()
                ai_success = True
            except Exception as e:
                self.log_step(f"⚠️ AI Strategy failed ({str(e)}). Switching to Heuristic Mode.")
        
        self._heuristic_cleaning() 
        self._drop_duplicates()
        self._fix_data_types()  # <--- BUG WAS HERE
        
        # --- PHASE 2: FEATURE ENGINEERING ---
        self._extract_date_features()
        self._extract_text_features()
        self._encode_categoricals()
        
        # --- PHASE 3: FINAL SWEEP ---
        self._heuristic_cleaning(silent=True)

        # --- PHASE 4: PREPROCESSING ---
        #self._scale_numerical_features()
        
        final_shape = self.df.shape
        self.log_step(f"✅ Pipeline Complete. Final Shape: {final_shape}")
        
        return self.df, self.log

    # --- WORKER FUNCTIONS ---

    def _apply_ai_cleaning_strategy(self):
        stats = self.df.describe(include='all').to_string()
        missing = self.df.isnull().sum()
        missing_report = missing[missing > 0].to_string()
        
        if len(missing_report) == 0: return

        prompt_data = f"STATS:\n{stats}\n\nMISSING VALUES:\n{missing_report}"
        strategy_json = get_engineering_strategy(prompt_data)
        
        try:
            plan = json.loads(strategy_json)
            for col, instructions in plan.items():
                if col not in self.df.columns: continue
                
                action = instructions.get("action")
                if action == "drop":
                    self.df = self.df.drop(columns=[col])
                    self.log_step(f"🗑️ Dropped '{col}' (AI Reason: {instructions.get('reason')})")
                    
                elif action == "impute":
                    method = instructions.get("method", "median")
                    if method == "median" and pd.api.types.is_numeric_dtype(self.df[col]):
                        val = self.df[col].median()
                        self.df[col] = self.df[col].fillna(val)
                        self.log_step(f"🧩 Imputed '{col}' with Median ({val:.2f})")
                    elif method == "mode":
                        val = self.df[col].mode()[0]
                        self.df[col] = self.df[col].fillna(val)
                        self.log_step(f"🧩 Imputed '{col}' with Mode ({val})")
        except:
            pass 

    def _heuristic_cleaning(self, silent=False):
        num_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(num_cols) > 0:
            imputer = SimpleImputer(strategy='median')
            if self.df[num_cols].isnull().any().any():
                self.df[num_cols] = imputer.fit_transform(self.df[num_cols])
                if not silent:
                    self.log_step(f"🧩 (Heuristic) Imputed numeric columns.")

        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns
        for col in cat_cols:
            if self.df[col].isnull().sum() > 0:
                self.df[col] = self.df[col].fillna("Unknown")
                if not silent:
                    self.log_step(f"🧩 (Heuristic) Filled missing values in '{col}'.")

    def _drop_duplicates(self):
        initial = len(self.df)
        self.df = self.df.drop_duplicates()
        dropped = initial - len(self.df)
        if dropped > 0:
            self.log_step(f"🗑️ Dropped {dropped} duplicate rows.")

    def _fix_data_types(self):
        """
        Detects if a numeric column is actually an ID (e.g. 'Transaction_ID').
        STRICT FIX: Only matches '_id', 'id_', or exact 'id'. Ignores 'width'.
        """
        for col in self.df.columns:
            if not pd.api.types.is_numeric_dtype(self.df[col]):
                continue
                
            col_lower = col.lower()
            
            # 1. Check for "ID" pattern
            is_id_pattern = (
                col_lower == 'id' or 
                col_lower.endswith('_id') or 
                col_lower.startswith('id_') or 
                'code' in col_lower
            )
            
            # 2. Check for High Cardinality (IDs usually are unique)
            # But don't convert if it's a float (e.g. 1.5 is likely not an ID)
            is_integer_like = (self.df[col] % 1 == 0).all()
            
            if is_id_pattern and is_integer_like and self.df[col].nunique() > 10:
                self.df[col] = self.df[col].astype(str)
                self.log_step(f"🔢 Converted ID column '{col}' to string.")

    def _extract_date_features(self):
        for col in self.df.columns:
            if pd.api.types.is_datetime64_any_dtype(self.df[col]) or 'date' in col.lower():
                try:
                    self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                    self.df[f'{col}_year'] = self.df[col].dt.year
                    self.df[f'{col}_month'] = self.df[col].dt.month
                    self.df[f'{col}_day'] = self.df[col].dt.day_name()
                    self.df = self.df.drop(columns=[col])
                    self.log_step(f"📅 Extracted features from '{col}'.")
                except:
                    pass

    def _extract_text_features(self):
        object_cols = self.df.select_dtypes(include=['object']).columns
        for col in object_cols:
            if self.df[col].nunique() > 10:
                self.df[f'{col}_len'] = self.df[col].astype(str).str.len()
                self.log_step(f"📏 Created text length feature for '{col}'.")

    def _encode_categoricals(self):
        cat_cols = self.df.select_dtypes(include=['object']).columns
        le = LabelEncoder()
        for col in cat_cols:
            unique_count = self.df[col].nunique()
            if unique_count < 50:
                new_col = f"{col}_encoded"
                self.df[new_col] = le.fit_transform(self.df[col].astype(str))
                self.df = self.df.drop(columns=[col])
                self.log_step(f"🔤 Label Encoded '{col}'.")

    def _scale_numerical_features(self):
        self.df = self.df.dropna(axis=1, how='all')
        num_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(num_cols) > 0:
            scaler = StandardScaler()
            try:
                self.df[num_cols] = scaler.fit_transform(self.df[num_cols])
                self.log_step(f"⚖️ Scaled {len(num_cols)} numerical features.")
            except:
                pass

# --- EXPORT FUNCTION ---
def run_auto_prep(df: pd.DataFrame):
    engine = AutoDataEngineer(df)
    processed_df, log = engine.run_pipeline()
    return processed_df, log