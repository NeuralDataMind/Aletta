import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.impute import SimpleImputer

# Import the AI function we created
try:
    from app.core.ai import get_engineering_strategy
except ImportError:
    # Failsafe if ai.py isn't updated yet
    get_engineering_strategy = None

class AutoDataEngineer:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.log = []
        self.original_shape = df.shape
        self.transformation_metadata = {}

    def log_step(self, message):
        """Records actions for the AI to summarize later."""
        self.log.append(message)

    def run_pipeline(self):
        """
        Master function that runs the entire Data Engineering sequence.
        Flow: AI Cleaning Strategy -> Feature Engineering -> Scaling
        """
        self.log_step(f"🚀 Starting Auto-Engineering on {self.original_shape[0]} rows, {self.original_shape[1]} columns.")
        
        # --- PHASE 1: CLEANING (AI-Guided) ---
        # We try to use the AI to decide how to clean. If it fails, we use heuristics.
        ai_success = False
        if get_engineering_strategy:
            try:
                self._apply_ai_cleaning_strategy()
                ai_success = True
            except Exception as e:
                self.log_step(f"⚠️ AI Strategy failed ({str(e)}). Switching to Heuristic Mode.")
        
        if not ai_success:
            self._heuristic_cleaning()

        self._drop_duplicates()
        self._fix_data_types()
        
        # --- PHASE 2: FEATURE ENGINEERING (Algorithmic) ---
        self._extract_date_features()
        self._extract_text_features()
        self._encode_categoricals()
        
        # --- PHASE 3: PREPROCESSING (Standardization) ---
        self._scale_numerical_features()
        
        final_shape = self.df.shape
        self.log_step(f"✅ Pipeline Complete. Final Shape: {final_shape}")
        
        return self.df, self.log

    # --- PHASE 1: STRATEGIC CLEANING ---

    def _apply_ai_cleaning_strategy(self):
        """
        Asks Groq: 'Here are the stats. Which columns should I drop or impute?'
        """
        # 1. Generate Metadata (The "Eyes")
        stats = self.df.describe(include='all').to_string()
        missing = self.df.isnull().sum()
        missing = missing[missing > 0].to_string() # Only show cols with missing data
        
        if len(missing) == 0:
            self.log_step("Dataset has no missing values. Skipping AI Cleaning.")
            return

        prompt_data = f"STATS:\n{stats}\n\nMISSING VALUES:\n{missing}"
        
        # 2. Ask the Brain
        strategy_json = get_engineering_strategy(prompt_data)
        plan = json.loads(strategy_json) # Parse JSON response
        
        # 3. Execute the Plan
        for col, instructions in plan.items():
            if col not in self.df.columns: continue
            
            action = instructions.get("action")
            
            if action == "drop":
                self.df.drop(columns=[col], inplace=True)
                reason = instructions.get("reason", "AI suggestion")
                self.log_step(f"🗑️ Dropped '{col}' (AI Reason: {reason})")
                
            elif action == "impute":
                method = instructions.get("method", "median")
                if method == "median" and pd.api.types.is_numeric_dtype(self.df[col]):
                    val = self.df[col].median()
                    self.df[col].fillna(val, inplace=True)
                    self.log_step(f"🧩 Imputed '{col}' with Median ({val:.2f})")
                elif method == "mode":
                    val = self.df[col].mode()[0]
                    self.df[col].fillna(val, inplace=True)
                    self.log_step(f"🧩 Imputed '{col}' with Mode ({val})")
                else:
                    # Fallback for "value" or unknown method
                    self.df[col].fillna("Unknown", inplace=True)
                    self.log_step(f"🧩 Imputed '{col}' with 'Unknown'")

    def _heuristic_cleaning(self):
        """Fallback: Standard logic if AI is unavailable."""
        # Numeric: Impute with Median
        num_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(num_cols) > 0:
            imputer = SimpleImputer(strategy='median')
            self.df[num_cols] = imputer.fit_transform(self.df[num_cols])
            self.log_step(f"🧩 (Heuristic) Imputed missing values in {len(num_cols)} numeric columns using Median.")

        # Categorical: Impute with "Unknown"
        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns
        for col in cat_cols:
            if self.df[col].isnull().sum() > 0:
                self.df[col] = self.df[col].fillna("Unknown")
                self.log_step(f"🧩 (Heuristic) Filled missing values in '{col}' with 'Unknown'.")

    def _drop_duplicates(self):
        initial = len(self.df)
        self.df = self.df.drop_duplicates()
        dropped = initial - len(self.df)
        if dropped > 0:
            self.log_step(f"🗑️ Dropped {dropped} duplicate rows.")

    def _fix_data_types(self):
        # Convert ID-like columns to strings
        for col in self.df.columns:
            if ('id' in col.lower() or 'code' in col.lower()) and pd.api.types.is_numeric_dtype(self.df[col]):
                # Only if high cardinality (lots of unique values), otherwise it might be a real count
                if self.df[col].nunique() > 10: 
                    self.df[col] = self.df[col].astype(str)
                    self.log_step(f"🔢 Converted ID column '{col}' to string.")

    # --- PHASE 2: FEATURE ENGINEERING ---

    def _extract_date_features(self):
        for col in self.df.columns:
            # Check for datetime type or 'date' in name
            if pd.api.types.is_datetime64_any_dtype(self.df[col]) or 'date' in col.lower():
                try:
                    self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                    # Create new features
                    self.df[f'{col}_year'] = self.df[col].dt.year
                    self.df[f'{col}_month'] = self.df[col].dt.month
                    self.df[f'{col}_day'] = self.df[col].dt.day_name()
                    
                    # Drop original date (ML models can't read raw dates)
                    self.df = self.df.drop(columns=[col])
                    self.log_step(f"📅 Extracted Year, Month, Day from '{col}' and dropped original.")
                except:
                    pass

    def _extract_text_features(self):
        # Create 'length' feature for text columns
        object_cols = self.df.select_dtypes(include=['object']).columns
        for col in object_cols:
            # Only if it's not a tiny category (e.g. "Male/Female")
            if self.df[col].nunique() > 10:
                self.df[f'{col}_len'] = self.df[col].astype(str).str.len()
                self.log_step(f"📏 Created text length feature for '{col}'.")

    def _encode_categoricals(self):
        cat_cols = self.df.select_dtypes(include=['object']).columns
        le = LabelEncoder()
        
        for col in cat_cols:
            unique_count = self.df[col].nunique()
            # If low cardinality (< 50), it's likely a Category -> Encode it
            if unique_count < 50:
                new_col = f"{col}_encoded"
                self.df[new_col] = le.fit_transform(self.df[col].astype(str))
                self.df.drop(columns=[col], inplace=True)
                self.log_step(f"🔤 Label Encoded '{col}' -> '{new_col}'")
            else:
                # If high cardinality (> 50), it's likely a Name/ID -> Drop for ML
                # (Unless we already extracted features from it)
                if f'{col}_len' not in self.df.columns:
                     self.log_step(f"⚠️ High cardinality in '{col}' ({unique_count}). Kept raw (might need embedding).")

    # --- PHASE 3: PREPROCESSING ---

    def _scale_numerical_features(self):
        num_cols = self.df.select_dtypes(include=[np.number]).columns
        # Exclude encoded columns/ID columns if desired, but StandardScaling everything is generally safe
        if len(num_cols) > 0:
            scaler = StandardScaler()
            self.df[num_cols] = scaler.fit_transform(self.df[num_cols])
            self.log_step(f"⚖️ Scaled {len(num_cols)} numerical features using StandardScaler.")

# --- EXPORT FUNCTION ---
def run_auto_prep(df: pd.DataFrame):
    """
    Entry point for the API.
    """
    engine = AutoDataEngineer(df)
    processed_df, log = engine.run_pipeline()
    return processed_df, log