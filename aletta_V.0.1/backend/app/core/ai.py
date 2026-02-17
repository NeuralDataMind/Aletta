import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key = os.environ.get("GROQ_API_KEY"),
)

def get_groq_analysis(
        system_prompt: str,
        user_data: str
):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_data},
            ],
            model = "llama-3.3-70b-versatile",
            temperature=0.5,
            max_tokens=1500,
        )
    except Exception as e:
        return f"AI Analysis Failed: {str(e)}"
    
    return chat_completion.choices[0].message.content

# app/core/ai.py (Add this new function)

def get_engineering_strategy(column_stats: str):
    """
    Asks the AI to decide how to clean specific columns.
    Returns a JSON-parsable string.
    """
    system_prompt = """
    You are a Senior Data Engineer. 
    Analyze the column statistics provided.
    Decide on the best cleaning strategy for each column.
    
    RULES:
    1. If a column is NUMERIC (int/float), use "impute" with "mean", "median", or "mode". NEVER use "Unknown" or strings for numbers.
    2. If a column is TEXT (object), you can use "impute" with "value" (e.g., "Unknown").
    3. If a column has too many missing values (>50%), use "drop".
    
    OUTPUT FORMAT (Strict JSON):
    {
        "ColumnName": {"action": "impute", "method": "median"},
        "City": {"action": "encode", "method": "label"}
    }
    """
    
    # We use a lower temperature for deterministic logic
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": column_stats},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1, # Precise logic
            response_format={"type": "json_object"} # Force JSON
        )
        return completion.choices[0].message.content
    except Exception as e:
        return "{}"