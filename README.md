# Satyam AI ✨

Hinglish AI chatbot (Streamlit). Orb home screen, 5 models ka dropdown, chat history, photo upload aur mic.

| Dropdown | Kaun chalata hai | Key |
|---|---|---|
| Satyam AI | Groq (Llama 3.3) | GROQ_API_KEY |
| Meta AI (Llama) | Groq (Llama 4) | GROQ_API_KEY |
| Gemini | Google | GEMINI_API_KEY |
| ChatGPT (GPT-4o) | OpenAI | OPENAI_API_KEY |
| Grok | xAI | XAI_API_KEY |

Mic (bolke likhna) Groq ki key se chalta hai.

## Run
1. `pip install -r requirements.txt`
2. Keys `.streamlit/secrets.toml` me ya Streamlit Cloud -> Manage app -> Settings -> Secrets me daalo:
   ```
   GROQ_API_KEY = "..."
   GEMINI_API_KEY = "..."
   OPENAI_API_KEY = "..."
   XAI_API_KEY = "..."
   ```
   Model ka naam badalna ho toh `OPENAI_MODEL`, `XAI_MODEL`, `GEMINI_MODEL` bhi daal sakte ho.
3. `streamlit run app.py`
