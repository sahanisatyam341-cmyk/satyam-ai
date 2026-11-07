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

GEM_KEY = key("GEMINI_API_KEY")
if GEM_KEY:
    genai.configure(api_key=GEM_KEY)

SYSTEM = ("Tum Satyam ho, ek dost jaisa smart AI assistant. Hinglish me, chhote aur saaf jawab do. "
          "Photo ya sawaal ho toh step-by-step madad karo. Galat jaankari mat do.")
# naam: (provider, model, Secrets me naam badalne ki key, photo samajhta hai?)
MODELS = {
    "Satyam AI": ("groq", "openai/gpt-oss-120b", "SATYAM_MODEL", False),
    "ChatGPT (GPT-4o)": ("openai", "gpt-4o", "OPENAI_MODEL", True),
    "Gemini": ("gemini", "gemini-flash-latest", "GEMINI_MODEL", True),
    "Qwen 3.6": ("groq", "qwen/qwen3.6-27b", "QWEN_MODEL", False),
    "Grok": ("xai", "grok-3", "XAI_MODEL", False),
}
ORB = ('<div class="orb"></div><div class="hi">%s</div><div class="sub">ऑल-इन-वन AI असिस्टेंट</div>')

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
for k, v in {"chats": {}, "cur": None, "quick": None, "up": 0, "user": None, "sb": None, "guest": False}.items():
    S.setdefault(k, v)

# ---------- Login (Supabase) ----------
SB_URL, SB_KEY = key("SUPABASE_URL"), key("SUPABASE_KEY")

def load_chats():
    rows = S.sb.table("chats").select("id,title,msgs").order("created_at").execute().data
    S.chats = {r["id"]: {"title": r["title"], "msgs": r["msgs"] or []} for r in rows}

def save_chat(cid):
    if not S.sb:
        return
    c = S.chats[cid]
    msgs = [{"role": m["role"], "content": m["content"]} for m in c["msgs"]]
    try:
        S.sb.table("chats").upsert({"id": cid, "user_id": S.user.id, "title": c["title"], "msgs": msgs}).execute()
    except Exception as e:
        st.warning(f"Chat save nahi hui: {e}")

def login_screen():
    st.markdown(ORB % "Satyam AI me aao", unsafe_allow_html=True)
    tabs = st.tabs(["Login", "Sign up"])
    for tab, mode in zip(tabs, ("in", "up")):
        with tab:
            email = st.text_input("Email", key="e" + mode)
            pw = st.text_input("Password (6+ akshar)", type="password", key="p" + mode)
            if st.button("Login" if mode == "in" else "Account banao", key="b" + mode, use_container_width=True):
                try:
                    from supabase import create_client
                    sb = create_client(SB_URL, SB_KEY)
                    cred = {"email": email, "password": pw}
                    res = sb.auth.sign_in_with_password(cred) if mode == "in" else sb.auth.sign_up(cred)
                    if not res.session:
                        st.info("Email confirm karo (inbox dekho), phir Login karo.")
                        st.stop()
                    sb.postgrest.auth(res.session.access_token)
                    S.sb, S.user = sb, res.user
                    load_chats()
                    st.rerun()
                except Exception as e:
                    st.error(f"Login nahi hua: {e}")
    if st.button("Guest ki tarah chalao", use_container_width=True):
        S.guest = True
        st.rerun()
    st.stop()

if SB_URL and SB_KEY and not S.user and not S.guest:
    login_screen()

# ---------- Chats ----------
def new_chat():
    cid = str(uuid.uuid4())
    S.chats[cid] = {"title": "नयी चैट", "msgs": []}
    S.cur = cid

if S.cur not in S.chats:
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
    if S.user:
        st.divider()
        st.caption(S.user.email)
        if st.button("Logout", use_container_width=True):
            S.update(user=None, sb=None, chats={}, cur=None, guest=False)
            st.rerun()

model = MODELS[st.selectbox("AI Engine", list(MODELS), label_visibility="collapsed")]

if not chat["msgs"]:
    st.markdown(ORB % "नमस्ते! मैं Satyam हूँ", unsafe_allow_html=True)
    for col, text in zip(st.columns(3), ["गणित का सवाल हल करो", "अपना परिचय दो", "एक मज़ेदार जोक सुनाओ"]):
        if col.button(text, use_container_width=True):
            S.quick = text; st.rerun()

for m in chat["msgs"]:
    with st.chat_message(m["role"]):
        if m.get("img"):
            st.image(m["img"], width=220)
        st.markdown(m["content"])

def full(m):
    return m["content"] + ("\n\n" + m["ctx"] if m.get("ctx") else "")

def client_for(p):
    k = {"groq": "GROQ_API_KEY", "openai": "OPENAI_API_KEY", "xai": "XAI_API_KEY"}[p]
    if not key(k):
        raise RuntimeError(f"{k} Secrets me daalo")
    if p == "groq":
        return Groq(api_key=key(k))
    return OpenAI(api_key=key(k), base_url="https://api.x.ai/v1" if p == "xai" else None)

def reply(msgs, img_bytes):
    p, name, env, vision = model
    if img_bytes and not vision:  # is model ko photo nahi dikhti -> Gemini
        p, name, env = "gemini", "gemini-flash-latest", "GEMINI_MODEL"
    name = key(env) or name
    msgs = msgs[-20:]
    if p == "gemini":
        if not GEM_KEY:
            raise RuntimeError("GEMINI_API_KEY Secrets me daalo")
        g = genai.GenerativeModel(name, system_instruction=SYSTEM)
        hist = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [full(m)]} for m in msgs]
        if img_bytes:
            hist[-1]["parts"].append(Image.open(io.BytesIO(img_bytes)))
        return g.generate_content(hist, request_options={"timeout": 90}).text
    api = [{"role": "system", "content": SYSTEM}] + [{"role": m["role"], "content": full(m)} for m in msgs]
    if img_bytes:
        b64 = base64.b64encode(img_bytes).decode()
        api[-1]["content"] = [{"type": "text", "text": full(msgs[-1])},
                              {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]
    r = client_for(p).chat.completions.create(model=name, messages=api)
    return r.choices[0].message.content

IMG = ("png", "jpg", "jpeg")
with st.popover("➕ फाइल / 🎤 आवाज़"):
    up = st.file_uploader("फोटो या फाइल भेजो", type=list(IMG) + ["txt", "md", "py", "csv", "json"], key=f"f{S.up}")
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
    img_bytes, ctx = None, None
    if up:
        if up.name.lower().endswith(IMG):
            img_bytes = up.getvalue()
        else:
            ctx = f"[File: {up.name}]\n" + up.getvalue().decode("utf-8", "ignore")[:12000]
            prompt += f"\n\n📎 {up.name}"
    chat["msgs"].append({"role": "user", "content": prompt, "img": img_bytes, "ctx": ctx})
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
                ans = f"⚠️ दिक्कत आई: {e}\n\nAPI keys check करो, या दूसरा model चुनो।"
        st.markdown(ans)
    chat["msgs"].append({"role": "assistant", "content": ans})
    save_chat(S.cur)
    S.up += 1
    st.rerun()
