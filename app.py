import base64, io, os, uuid
import streamlit as st
from groq import Groq
from openai import OpenAI
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="Satyam AI", page_icon="✨", layout="centered")

def key(name):
    try:
        return st.secrets[name]
    except Exception:
        return os.getenv(name, "")

GROQ_KEY, GEM_KEY = key("GROQ_API_KEY"), key("GEMINI_API_KEY")
if GEM_KEY:
    genai.configure(api_key=GEM_KEY)

SYSTEM = ("Tum Satyam ho, ek dost jaisa smart AI assistant. Hinglish me, chhote aur saaf jawab do. "
          "Photo ya sawaal ho toh step-by-step madad karo. Galat jaankari mat do.")
# naam: (provider, model, photo samajhta hai?)
MODELS = {
    "Satyam AI": ("groq", "llama-3.3-70b-versatile", False),
    "ChatGPT (GPT-4o)": ("openai", "gpt-4o", True),
    "Gemini": ("gemini", "gemini-2.5-flash", True),
    "Meta AI (Llama)": ("groq", "meta-llama/llama-4-scout-17b-16e-instruct", True),
    "Grok": ("xai", "grok-3", False),
}

st.markdown("""
<style>
.stApp{background:radial-gradient(circle at 50% 0%,#0c1a3a 0%,#060b18 60%);color:#e8eefc}
[data-testid=stSidebar]{background:#0a1226}
.orb{width:96px;height:96px;margin:24px auto 12px;border-radius:50%;
 background:radial-gradient(circle at 35% 35%,#fff 0%,#a5f3fc 20%,#38bdf8 45%,#818cf8 70%,#c084fc 100%);
 animation:glow 2s ease-in-out infinite alternate}
@keyframes glow{0%{box-shadow:0 0 25px 5px rgba(56,189,248,.4)}100%{box-shadow:0 0 50px 15px rgba(147,51,234,.5)}}
.hi{text-align:center;font-size:1.7rem;font-weight:700;
 background:linear-gradient(90deg,#38bdf8,#a78bfa);-webkit-background-clip:text;color:transparent}
.sub{text-align:center;color:#94a3b8;font-size:.8rem;margin-bottom:12px}
</style>""", unsafe_allow_html=True)

S = st.session_state
S.setdefault("chats", {}); S.setdefault("cur", None); S.setdefault("quick", None); S.setdefault("up", 0)

def new_chat():
    cid = uuid.uuid4().hex[:8]
    S.chats[cid] = {"title": "नयी चैट", "msgs": []}
    S.cur = cid

if S.cur is None:
    new_chat()
chat = S.chats[S.cur]

with st.sidebar:
    st.markdown("### ✨ Satyam AI")
    if st.button("➕ नयी चैट", use_container_width=True):
        new_chat(); st.rerun()
    st.caption("पुरानी चैट्स")
    for cid, c in reversed(list(S.chats.items())):
        if c["msgs"] and st.button(c["title"][:28], key=cid, use_container_width=True):
            S.cur = cid; st.rerun()

model = MODELS[st.selectbox("AI Engine", list(MODELS), label_visibility="collapsed")]

if not chat["msgs"]:
    st.markdown('<div class="orb"></div><div class="hi">नमस्ते! मैं Satyam हूँ</div>'
                '<div class="sub">ऑल-इन-वन AI असिस्टेंट</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    chips = ["गणित का सवाल हल करो", "अपना परिचय दो", "एक मज़ेदार जोक सुनाओ"]
    for col, text in zip(cols, chips):
        if col.button(text, use_container_width=True):
            S.quick = text; st.rerun()

for m in chat["msgs"]:
    with st.chat_message(m["role"]):
        if m.get("img"):
            st.image(m["img"], width=220)
        st.markdown(m["content"])

def client_for(p):
    k = {"groq": "GROQ_API_KEY", "openai": "OPENAI_API_KEY", "xai": "XAI_API_KEY"}[p]
    if not key(k):
        raise RuntimeError(f"{k} Secrets me daalo")
    if p == "groq":
        return Groq(api_key=key(k))
    return OpenAI(api_key=key(k), base_url="https://api.x.ai/v1" if p == "xai" else None)

def reply(msgs, img_bytes):
    p, name, vision = model
    if img_bytes and not vision:  # is model ko photo nahi dikhti -> Gemini
        p, name = "gemini", "gemini-2.5-flash"
    if p != "groq":  # model ka naam Secrets se badal sakte ho, jaise OPENAI_MODEL / XAI_MODEL / GEMINI_MODEL
        name = key(p.upper() + "_MODEL") or name
    msgs = msgs[-20:]
    if p == "gemini":
        if not GEM_KEY:
            raise RuntimeError("GEMINI_API_KEY Secrets me daalo")
        g = genai.GenerativeModel(name, system_instruction=SYSTEM)
        hist = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [m["content"]]}
                for m in msgs]
        if img_bytes:
            hist[-1]["parts"].append(Image.open(io.BytesIO(img_bytes)))
        return g.generate_content(hist, request_options={"timeout": 90}).text
    api = [{"role": "system", "content": SYSTEM}] + \
          [{"role": m["role"], "content": m["content"]} for m in msgs]
    if img_bytes:
        b64 = base64.b64encode(img_bytes).decode()
        api[-1]["content"] = [{"type": "text", "text": msgs[-1]["content"]},
                              {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]
    r = client_for(p).chat.completions.create(model=name, messages=api)
    return r.choices[0].message.content

with st.popover("➕ फोटो / 🎤 आवाज़"):
    img = st.file_uploader("फोटो भेजो", type=["png", "jpg", "jpeg"], key=f"img{S.up}")
    voice = st.audio_input("🎤 बोलो")
prompt = st.chat_input("मुझसे कभी भी पूछें...")

if voice and S.get("last_voice") != voice.file_id:
    S.last_voice = voice.file_id
    try:
        prompt = client_for("groq").audio.transcriptions.create(
            file=("voice.wav", voice.getvalue()), model="whisper-large-v3-turbo", language="hi").text
    except Exception as e:
        st.error(f"आवाज़ समझ नहीं आई: {e}")
prompt = prompt or S.quick
S.quick = None

if prompt:
    img_bytes = img.getvalue() if img else None
    chat["msgs"].append({"role": "user", "content": prompt, "img": img_bytes})
    if chat["title"] == "नयी चैट":
        chat["title"] = prompt[:28]
    with st.chat_message("user"):
        if img_bytes:
            st.image(img_bytes, width=220)
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("सोच रहा हूँ..."):
            try:
                ans = reply(chat["msgs"], img_bytes)
            except Exception as e:
                ans = f"⚠️ दिक्कत आई: {e}\n\nAPI keys और internet check करो।"
        st.markdown(ans)
    chat["msgs"].append({"role": "assistant", "content": ans})
    S.up += 1
    st.rerun()
