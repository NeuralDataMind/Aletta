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