import pandas as pd
import numpy as np
import json
import re
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer

# Safely import the AI function
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
        
        # --- PHASE 1: AI COGNITIVE STRATEGY ---
        if get_engineering_strategy:
            try:
                self._apply_ai_cleaning_strategy()
            except Exception as e:
                self.log_step(f"⚠️ AI Strategy failed ({str(e)}). Executing strict statistical heuristics.")

        # --- PHASE 2: STRUCTURAL CLEANING ---
        self._drop_duplicates()
        self._drop_id_columns() # Drop IDs before they confuse the encoders
        
        # --- PHASE 3: FEATURE EXTRACTION ---
        self._extract_date_features()
        # Removed _extract_text_features() call that was causing the crash
        
        # --- PHASE 4: ENCODING & IMPUTATION ---
        self._encode_categoricals() # Handles both low and mid-cardinality text
        self._heuristic_imputation() # Fill all remaining missing values
        
        # --- PHASE 5: THE PURGE (Safety Check) ---
        self._purge_unencoded_text()
        
        final_shape = self.df.shape
        self.log_step(f"✅ Pipeline Complete. Final Shape: {final_shape}")
        
        return self.df, self.log

    # --- WORKER FUNCTIONS ---

    def _extract_json(self, text: str) -> str:
        """Strips markdown formatting from LLM outputs to guarantee valid JSON."""
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return match.group(1)
        # If no markdown blocks, find the first { and last }
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            return text[start:end+1]
        return text

    def _apply_ai_cleaning_strategy(self):
        stats = self.df.describe(include='all').to_string()
        missing = self.df.isnull().sum()
        missing_report = missing[missing > 0].to_string()
        
        if len(missing_report) == 0: 
            return

        prompt_data = f"STATS:\n{stats}\n\nMISSING VALUES:\n{missing_report}"
        raw_strategy = get_engineering_strategy(prompt_data)
        
        clean_json = self._extract_json(raw_strategy)
        plan = json.loads(clean_json)
        
        for col, instructions in plan.items():
            if col not in self.df.columns: continue
            
            action = instructions.get("action")
            if action == "drop":
                self.df = self.df.drop(columns=[col])
                self.log_step(f"🗑️ Dropped '{col}' (AI Reason: {instructions.get('reason', 'None provided')})")
                
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

    def _heuristic_imputation(self):
        """Fills any missing values the AI missed."""
        # Numeric imputation
        num_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(num_cols) > 0 and self.df[num_cols].isnull().any().any():
            imputer = SimpleImputer(strategy='median')
            self.df[num_cols] = imputer.fit_transform(self.df[num_cols])
            self.log_step("🧩 Statistically imputed remaining numeric columns with median.")

        # Categorical imputation
        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns
        for col in cat_cols:
            if self.df[col].isnull().sum() > 0:
                mode_val = self.df[col].mode()[0] if not self.df[col].mode().empty else "Unknown"
                self.df[col] = self.df[col].fillna(mode_val)
                self.log_step(f"🧩 Imputed missing values in '{col}' with mode.")

    def _drop_duplicates(self):
        initial = len(self.df)
        self.df = self.df.drop_duplicates()
        dropped = initial - len(self.df)
        if dropped > 0:
            self.log_step(f"🗑️ Dropped {dropped} duplicate rows.")

    def _drop_id_columns(self):
        """Drops columns that act as unique identifiers to prevent overfitting."""
        cols_to_drop = []
        for col in self.df.columns:
            col_lower = col.lower()
            is_id_pattern = col_lower == 'id' or col_lower.endswith('_id') or col_lower.startswith('id_')
            is_high_cardinality = self.df[col].nunique() > (len(self.df) * 0.8) # 80% unique
            
            if is_id_pattern or is_high_cardinality:
                cols_to_drop.append(col)
                
        if cols_to_drop:
            self.df = self.df.drop(columns=cols_to_drop)
            self.log_step(f"🗑️ Dropped high-cardinality/ID columns: {cols_to_drop}")

    def _extract_date_features(self):
        for col in list(self.df.columns): # Use list to avoid modifying during iteration
            if pd.api.types.is_datetime64_any_dtype(self.df[col]) or 'date' in col.lower():
                try:
                    dt_series = pd.to_datetime(self.df[col], errors='coerce')
                    if dt_series.isnull().all(): continue # Not a real date column
                    
                    self.df[f'{col}_year'] = dt_series.dt.year.fillna(0)
                    self.df[f'{col}_month'] = dt_series.dt.month.fillna(0)
                    self.df[f'{col}_day_encoded'] = LabelEncoder().fit_transform(dt_series.dt.day_name().fillna("Unknown"))
                    
                    self.df = self.df.drop(columns=[col])
                    self.log_step(f"📅 Extracted temporal features from '{col}' and dropped original.")
                except:
                    pass

    def _encode_categoricals(self):
        """Encodes strings using Label Encoding (low cardinality) or Frequency Encoding (mid cardinality)."""
        cat_cols = self.df.select_dtypes(include=['object']).columns
        le = LabelEncoder()
        
        for col in cat_cols:
            unique_count = self.df[col].nunique()
            
            # Low Cardinality: Label Encoding
            if unique_count <= 100:
                new_col = f"{col}_encoded"
                self.df[new_col] = le.fit_transform(self.df[col].astype(str))
                self.df = self.df.drop(columns=[col])
                self.log_step(f"🔤 Label Encoded '{col}'.")
                
            # Mid Cardinality (e.g., Zip Codes, Cities): Frequency Encoding
            elif 100 < unique_count <= 1000:
                new_col = f"{col}_freq"
                freq_map = self.df[col].value_counts().to_dict()
                self.df[new_col] = self.df[col].map(freq_map)
                self.df = self.df.drop(columns=[col])
                self.log_step(f"📊 Frequency Encoded '{col}'.")

    def _purge_unencoded_text(self):
        """The ultimate safety net. Destroys any remaining string columns so ML doesn't crash."""
        text_cols = self.df.select_dtypes(include=['object', 'category']).columns
        if len(text_cols) > 0:
            self.df = self.df.drop(columns=text_cols)
            self.log_step(f"⚠️ PURGE: Dropped unencoded text columns to protect ML engine: {list(text_cols)}")

# --- EXPORT FUNCTION ---
def run_auto_prep(df: pd.DataFrame):
    engine = AutoDataEngineer(df)
    processed_df, log = engine.run_pipeline()
    return processed_df, log