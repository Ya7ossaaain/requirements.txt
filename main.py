import os
import requests
from fastapi import FastAPI, Request, Response
from google import genai

app = FastAPI()

# سحب المفاتيح بأمان تام من إعدادات Vercel دون وضعها في كود GitHub
ACCOUNT_ID = "17841443992573456"
ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
VERIFY_TOKEN = "hussien_secret_123"
GRAPH_URL = "https://graph.facebook.com/v26.0"

try:
    ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
except Exception:
    ai_client = None

SYSTEM_INSTRUCTION = """
أنت حسين (صاحب الحساب الشخصي على إنستغرام).
تتحدث مباشرة مع أصدقائك ومعارفك ومتابعيك كأنك أنت.
القواعد:
1. بصيغة المتكلم دائماً (أنا، عندي، بكلمك، تسلم لي يا غالي). ممنوع تذكر أنك ذكاء اصطناعي أو بوت.
2. النبرة: هادئ، ذكي، ودود، عفوي، ومحترم، بلهجة بيضاء خفيفة وسلسة.
3. الردود: سريعة ومختصرة (سطر أو سطرين فقط).
4. إذا سأل صديق عن شيء شخصي أو موعد أو تفاصيل لا تعرفها:
   قل بأسلوب حسين: "والله مشغول الحين شوي / عندي شوية أمور، بخلص وأرجع أكلمك بروقان يا غالي".
"""

def send_direct_message(recipient_id: str, message_text: str):
    url = f"{GRAPH_URL}/{ACCOUNT_ID}/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text},
        "access_token": ACCESS_TOKEN
    }
    return requests.post(url, json=payload).json()

# فحص أي مسار وارد من نوع GET (للتحقق من ميتا في كل الحالات)
@app.get("/webhook")
@app.get("/webhook/")
@app.get("/{full_path:path}")
async def handle_all_get(request: Request, full_path: str = ""):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    # إذا كان الطلب للتحقق من Meta
    if mode == "subscribe" and token == VERIFY_TOKEN and challenge:
        return Response(content=str(challenge), media_type="text/plain", status_code=200)
    
    # الصفحة الرئيسية
    if not full_path or full_path == "":
        return {"status": "Instagram Bot is running successfully on Vercel!"}
        
    return Response(content="Forbidden", status_code=403)

# استقبال الرسائل على أي مسار من نوع POST
@app.post("/webhook")
@app.post("/webhook/")
@app.post("/{full_path:path}")
async def handle_all_post(request: Request, full_path: str = ""):
    data = await request.json()
    try:
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                sender_id = event.get("sender", {}).get("id")
                user_message = event.get("message", {}).get("text")

                if sender_id and user_message and sender_id != ACCOUNT_ID:
                    prompt = f"{SYSTEM_INSTRUCTION}\n\nرسالة واردة من صديق على الخاص: '{user_message}'\nردك عليه كـ حسين:"
                    if ai_client:
                        response = ai_client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=prompt
                        )
                        reply = response.text.strip()
                    else:
                        reply = "أهلاً يا غالي، شويات وأرجع أكلمك بروقان إن شاء الله."
                    
                    send_direct_message(sender_id, reply)
    except Exception as e:
        print(f"Error: {e}")
    return {"status": "ok"}
