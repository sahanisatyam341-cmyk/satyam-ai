# Satyam AI ✨

Hinglish AI chatbot (Streamlit): orb home screen, 5 models, login, chat history, photo/file upload, mic.

| Dropdown | Kaun chalata hai | Key |
|---|---|---|
| Satyam AI | Groq (gpt-oss-120b) | GROQ_API_KEY |
| Qwen 3.6 | Groq | GROQ_API_KEY |
| Gemini | Google | GEMINI_API_KEY |
| ChatGPT (GPT-4o) | OpenAI | OPENAI_API_KEY |
| Grok | xAI | XAI_API_KEY |

Mic Groq ki key se chalta hai. Model ka naam badalna ho toh Secrets me `SATYAM_MODEL`, `QWEN_MODEL`, `GEMINI_MODEL`, `OPENAI_MODEL`, `XAI_MODEL` daalo.

## Login (Supabase)
1. supabase.com par free project banao.
2. SQL Editor me `setup.sql` chalao.
3. Authentication -> Sign In / Providers -> Email me **Confirm email** band kar do (warna signup ke baad email confirm karna padega).
4. Project Settings -> API se URL aur **anon public** key lo.
5. Secrets me daalo: `SUPABASE_URL`, `SUPABASE_KEY`.
Keys na ho toh app bina login (guest) chalti hai.

## Secrets
```
GROQ_API_KEY = "..."
GEMINI_API_KEY = "..."
OPENAI_API_KEY = "..."
XAI_API_KEY = "..."
SUPABASE_URL = "..."
SUPABASE_KEY = "..."
```
