import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.impute import SimpleImputer

# Import the AI function
try:
    from app.core.ai import get_engineering_strategy
except ImportError:
    get_engineering_strategy = None

class AutoDataEngineer:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy() # SAFETY: Work on a copy to avoid SettingWithCopy warnings
        self.log = []
        self.original_shape = df.shape

    def log_step(self, message):
        self.log.append(message)

    def run_pipeline(self):
        self.log_step(f"🚀 Starting Auto-Engineering on {self.original_shape[0]} rows, {self.original_shape[1]} columns.")
        
        # --- PHASE 1: CLEANING (AI + Heuristic) ---
        ai_success = False
        if get_engineering_strategy:
            try:
                self._apply_ai_cleaning_strategy()
                ai_success = True
            except Exception as e:
                self.log_step(f"⚠️ AI Strategy failed ({str(e)}). Switching to Heuristic Mode.")
        
        # Always run heuristic cleanup as a safety net for anything the AI missed
        self._heuristic_cleaning() 
        self._drop_duplicates()
        self._fix_data_types()
        
        # --- PHASE 2: FEATURE ENGINEERING ---
        self._extract_date_features()
        self._extract_text_features()
        self._encode_categoricals()
        
        # --- PHASE 3: FINAL SWEEP (Critical Fix) ---
        # Catch NaNs created by Feature Engineering (e.g., Year extracted from NaT Date)
        self._heuristic_cleaning(silent=True)

        # --- PHASE 4: PREPROCESSING ---
        self._scale_numerical_features()
        
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
                        self.df[col] = self.df[col].fillna(val) # FIX: Direct assignment
                        self.log_step(f"🧩 Imputed '{col}' with Median ({val:.2f})")
                    elif method == "mode":
                        val = self.df[col].mode()[0]
                        self.df[col] = self.df[col].fillna(val) # FIX: Direct assignment
                        self.log_step(f"🧩 Imputed '{col}' with Mode ({val})")
        except:
            pass # Fail silently, Heuristic will catch it

    def _heuristic_cleaning(self, silent=False):
        """Fallback that guarantees no NaNs remain."""
        # Numeric: Impute with Median
        num_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(num_cols) > 0:
            imputer = SimpleImputer(strategy='median')
            # Only fit if there are actually NaNs to avoid unnecessary operations
            if self.df[num_cols].isnull().any().any():
                self.df[num_cols] = imputer.fit_transform(self.df[num_cols])
                if not silent:
                    self.log_step(f"🧩 (Heuristic) Imputed missing values in numeric columns.")

        # Categorical: Impute with "Unknown"
        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns
        for col in cat_cols:
            if self.df[col].isnull().sum() > 0:
                self.df[col] = self.df[col].fillna("Unknown")
                if not silent:
                    self.log_step(f"🧩 (Heuristic) Filled missing values in '{col}' with 'Unknown'.")

    def _drop_duplicates(self):
        initial = len(self.df)
        self.df = self.df.drop_duplicates()
        dropped = initial - len(self.df)
        if dropped > 0:
            self.log_step(f"🗑️ Dropped {dropped} duplicate rows.")

    def _fix_data_types(self):
        for col in self.df.columns:
            if ('id' in col.lower() or 'code' in col.lower()) and pd.api.types.is_numeric_dtype(self.df[col]):
                if self.df[col].nunique() > 10: 
                    self.df[col] = self.df[col].astype(str)
                    self.log_step(f"🔢 Converted ID column '{col}' to string.")

    def _extract_date_features(self):
        for col in self.df.columns:
            if pd.api.types.is_datetime64_any_dtype(self.df[col]) or 'date' in col.lower():
                try:
                    self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                    # Creating new features might introduce NaNs if date was NaT
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
                # Convert to string to handle any mixed types safely before encoding
                self.df[new_col] = le.fit_transform(self.df[col].astype(str))
                self.df = self.df.drop(columns=[col])
                self.log_step(f"🔤 Label Encoded '{col}'.")

    def _scale_numerical_features(self):
        # Final check: Drop any columns that are STILL purely NaN (unfixable)
        self.df = self.df.dropna(axis=1, how='all')
        
        num_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(num_cols) > 0:
            scaler = StandardScaler()
            try:
                self.df[num_cols] = scaler.fit_transform(self.df[num_cols])
                self.log_step(f"⚖️ Scaled {len(num_cols)} numerical features.")
            except Exception as e:
                self.log_step(f"⚠️ Scaling failed: {str(e)}. Returned unscaled data.")

# --- EXPORT FUNCTION ---
def run_auto_prep(df: pd.DataFrame):
    engine = AutoDataEngineer(df)
    processed_df, log = engine.run_pipeline()
    return processed_df, log