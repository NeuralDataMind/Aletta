import pandas as pd
import numpy as np
import json
import re
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer

try:
    from app.core.ai import get_engineering_strategy
except ImportError:
    get_engineering_strategy = None

class AutoDataEngineer:
    def __init__(self, df: pd.DataFrame, target_col: str):
        self.df = df.copy() 
        self.target_col = target_col
        self.log = []
        self.original_shape = df.shape

    def log_step(self, message):
        self.log.append(message)

    def run_pipeline(self):
        self.log_step(f"🚀 Starting High-Performance Engineering on {self.original_shape[0]} rows, {self.original_shape[1]} columns.")
        
        # --- PHASE 1: TARGET ISOLATION ---
        # Temporarily detach the target so we don't accidentally mutate it
        target_series = None
        if self.target_col and self.target_col in self.df.columns:
            target_series = self.df[self.target_col].copy()
            self.df = self.df.drop(columns=[self.target_col])
            self.log_step(f"🛡️ Target variable '{self.target_col}' isolated from feature transformations.")

        # --- PHASE 2: STRUCTURAL CLEANING ---
        self._drop_duplicates()
        self._drop_id_columns()
        
        # --- PHASE 3: FEATURE EXTRACTION & NORMALIZATION ---
        self._extract_date_features()
        self._fix_skewness() # Normalize exponential data distributions
        
        # --- PHASE 4: ENCODING & IMPUTATION ---
        self._encode_categoricals()
        self._heuristic_imputation()
        
        # --- PHASE 5: THE PURGE ---
        self._purge_unencoded_text()

        # --- PHASE 6: REATTACH TARGET & CLEAN OUTLIERS ---
        if target_series is not None:
            self.df[self.target_col] = target_series
            # Drop rows where the target itself is missing (Poisoned data)
            before_drop = len(self.df)
            self.df = self.df.dropna(subset=[self.target_col])
            if len(self.df) < before_drop:
                self.log_step(f"🗑️ Dropped {before_drop - len(self.df)} rows due to missing target variables.")
                
        # Only remove extreme outliers after target is reattached to keep rows aligned
        self._remove_extreme_outliers()
        
        final_shape = self.df.shape
        self.log_step(f"✅ Pipeline Complete. Final Shape: {final_shape}")
        
        return self.df, self.log

    # --- WORKER FUNCTIONS ---

    def _fix_skewness(self):
        """Applies log transformation to heavily skewed numeric features."""
        num_cols = self.df.select_dtypes(include=[np.number]).columns
        for col in num_cols:
            if self.df[col].nunique() > 20: # Don't skew-correct categorical integers
                skew_val = self.df[col].skew()
                if skew_val > 1.5:
                    # Only apply log1p if all values are >= 0
                    if (self.df[col] >= 0).all():
                        self.df[col] = np.log1p(self.df[col])
                        self.log_step(f"📉 Normalized right-skewed feature '{col}' (Skew: {skew_val:.2f})")

    def _remove_extreme_outliers(self):
        """Drops rows with mathematically impossible values using 3x IQR (Extreme Outliers)."""
        before = len(self.df)
        num_cols = self.df.select_dtypes(include=[np.number]).columns
        
        for col in num_cols:
            if col == self.target_col: continue # Don't filter based on target
            if self.df[col].nunique() > 20:
                Q1 = self.df[col].quantile(0.25)
                Q3 = self.df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 3 * IQR
                upper_bound = Q3 + 3 * IQR
                
                # Keep rows within bounds, or where it's NaN (to be imputed later)
                self.df = self.df[((self.df[col] >= lower_bound) & (self.df[col] <= upper_bound)) | self.df[col].isna()]
        
        dropped = before - len(self.df)
        if dropped > 0:
            self.log_step(f"🚨 Eradicated {dropped} extreme outlier rows using 3x IQR method.")

    def _heuristic_imputation(self):
        num_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(num_cols) > 0 and self.df[num_cols].isnull().any().any():
            imputer = SimpleImputer(strategy='median')
            self.df[num_cols] = imputer.fit_transform(self.df[num_cols])
            self.log_step("🧩 Statistically imputed missing numeric values with median.")

        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns
        for col in cat_cols:
            if self.df[col].isnull().sum() > 0:
                mode_val = self.df[col].mode()[0] if not self.df[col].mode().empty else "Unknown"
                self.df[col] = self.df[col].fillna(mode_val)
                self.log_step(f"🧩 Imputed missing categories in '{col}' with mode.")

    def _drop_duplicates(self):
        initial = len(self.df)
        self.df = self.df.drop_duplicates()
        dropped = initial - len(self.df)
        if dropped > 0:
            self.log_step(f"🗑️ Dropped {dropped} duplicate rows.")

    def _drop_id_columns(self):
        cols_to_drop = []
        for col in self.df.columns:
            col_lower = col.lower()
            is_id_pattern = col_lower == 'id' or col_lower.endswith('_id') or col_lower.startswith('id_')
            is_high_cardinality = self.df[col].nunique() > (len(self.df) * 0.8)
            
            if is_id_pattern or is_high_cardinality:
                cols_to_drop.append(col)
                
        if cols_to_drop:
            self.df = self.df.drop(columns=cols_to_drop)
            self.log_step(f"🗑️ Dropped high-cardinality/ID columns: {cols_to_drop}")

    def _extract_date_features(self):
        for col in list(self.df.columns):
            if pd.api.types.is_datetime64_any_dtype(self.df[col]) or 'date' in col.lower():
                try:
                    dt_series = pd.to_datetime(self.df[col], errors='coerce')
                    if dt_series.isnull().all(): continue 
                    
                    self.df[f'{col}_year'] = dt_series.dt.year.fillna(0)
                    self.df[f'{col}_month'] = dt_series.dt.month.fillna(0)
                    self.df[f'{col}_day_encoded'] = LabelEncoder().fit_transform(dt_series.dt.day_name().fillna("Unknown"))
                    
                    self.df = self.df.drop(columns=[col])
                    self.log_step(f"📅 Extracted temporal features from '{col}' and dropped original.")
                except:
                    pass

    def _encode_categoricals(self):
        cat_cols = self.df.select_dtypes(include=['object']).columns
        le = LabelEncoder()
        
        for col in cat_cols:
            unique_count = self.df[col].nunique()
            if unique_count <= 100:
                new_col = f"{col}_encoded"
                self.df[new_col] = le.fit_transform(self.df[col].astype(str))
                self.df = self.df.drop(columns=[col])
                self.log_step(f"🔤 Label Encoded '{col}'.")
            elif 100 < unique_count <= 1000:
                new_col = f"{col}_freq"
                freq_map = self.df[col].value_counts().to_dict()
                self.df[new_col] = self.df[col].map(freq_map)
                self.df = self.df.drop(columns=[col])
                self.log_step(f"📊 Frequency Encoded '{col}'.")

    def _purge_unencoded_text(self):
        text_cols = self.df.select_dtypes(include=['object', 'category']).columns
        if len(text_cols) > 0:
            self.df = self.df.drop(columns=text_cols)
            self.log_step(f"⚠️ PURGE: Dropped unencoded text columns to protect ML engine: {list(text_cols)}")

# --- EXPORT FUNCTION ---
def run_auto_prep(df: pd.DataFrame, target_col: str = None):
    engine = AutoDataEngineer(df, target_col)
    processed_df, log = engine.run_pipeline()
    return processed_df, log