import os
import requests
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from google import genai

app = FastAPI()

# سحب المفاتيح بأمان من إعدادات Vercel
ACCOUNT_ID = "17841443992573456"
ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
VERIFY_TOKEN = "hussien_secret_123"
GRAPH_URL = "https://graph.facebook.com/v26.0"

ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# ==================== تعليمات شخصية حسين ====================
SYSTEM_INSTRUCTION = """
أنت حسين (صاحب الحساب الشخصي على إنستغرام).
تتحدث مباشرة مع أصدقائك ومعارفك ومتابعيك كأنك أنت.

القواعد الأساسية:
1. التحدث بصيغة المتكلم دائماً (أنا، عندي، بكلمك، تسلم لي يا غالي). ممنوع نهائياً أن تذكر أنك ذكاء اصطناعي أو بوت.
2. النبرة: هادئ، ذكي، ودود، عفوي، ومحترم، بلهجة بيضاء خفيفة وسلسة تناسب الشات اليومي.
3. حجم الردود: سريعة ومختصرة (سطر أو سطرين فقط).
4. التحيات: "أهلاً يا غالي"، "يا هلا والله"، "أرحب"، "تمام الحمد لله، كيفك أنت؟"، "تسلم لي يا قلبي".
5. للريلز والميمز: "هههههه حلوة والله" أو "رهيب صراحة".
6. إذا سأل صديق عن شيء خاص، أو طلب موعداً أو موضوعاً لا تعرفه:
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

@app.get("/")
def home():
    return PlainTextResponse("Instagram Bot is running successfully on Vercel!")

# التحقق من الويب هوك بتوافق تام مع شروط فيسبوك
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        if challenge:
            return PlainTextResponse(content=str(challenge), status_code=200)
    
    return PlainTextResponse(content="Verification failed", status_code=403)

# استقبال الرسائل والرد عليها
@app.post("/webhook")
async def receive_message(request: Request):
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
        print(f"Error handling webhook: {e}")
    return PlainTextResponse("EVENT_RECEIVED", status_code=200)
