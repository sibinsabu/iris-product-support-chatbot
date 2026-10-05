import os, base64, mimetypes, uuid, requests, json, crawler
from flask import Flask, render_template, request, jsonify, send_file
from typing import Any, cast
from dotenv import load_dotenv  # pyrefly: ignore[missing-import]
from openai import OpenAI  # pyrefly: ignore[missing-import]

load_dotenv()
app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024
os.makedirs("uploads", exist_ok=True)

AOAI_ENDPOINT=os.getenv("AZURE_OPENAI_ENDPOINT","").rstrip("/")
AOAI_KEY=os.getenv("AZURE_OPENAI_API_KEY","")
TEXT_MODEL=os.getenv("TEXT_MODEL_DEPLOYMENT","")
VISION_MODEL=os.getenv("VISION_MODEL_DEPLOYMENT") or TEXT_MODEL
IMAGE_MODEL=os.getenv("IMAGE_MODEL_DEPLOYMENT","")
SPEECH_ENDPOINT=os.getenv("SPEECH_ENDPOINT","").rstrip("/")
SPEECH_KEY=os.getenv("SPEECH_API_KEY","")
SPEECH_REGION=os.getenv("SPEECH_REGION","eastus")
CONTENT_ENDPOINT=os.getenv("CONTENT_ENDPOINT","").rstrip("/")
CONTENT_KEY=os.getenv("CONTENT_API_KEY","")
CONTENT_API_VERSION=os.getenv("CONTENT_API_VERSION","2025-11-01")

def client():
    if not AOAI_ENDPOINT or not AOAI_KEY:
        raise RuntimeError("Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in .env")
    endpoint = AOAI_ENDPOINT.removesuffix("/openai/v1").rstrip("/")
    return OpenAI(api_key=AOAI_KEY, base_url=f"{endpoint}/openai/v1/")

def image_client():
    if not CONTENT_ENDPOINT or not CONTENT_KEY:
        raise RuntimeError("Set CONTENT_ENDPOINT and CONTENT_API_KEY in .env")
    endpoint = CONTENT_ENDPOINT.removesuffix("/openai/v1").removesuffix("/openai").rstrip("/")
    return OpenAI(
        api_key=CONTENT_KEY,
        base_url=f"{endpoint}/openai/v1/",
        default_query={"api-version": "preview"},
    )

SUPPORT_SYSTEM_PROMPT = """You are "Iris", the premier AI diagnostic and repair advisor for our certified electronics and gadget lab.
CRITICAL IDENTITY & GREETING RULE:
- Never say "Welcome to TechFix" or mention "TechFix". Your name and our service name is IRIS.
- When greeted (e.g. "hi", "hello", "hey", or when starting a conversation), always greet as Iris using:
  "Hello! Iris here, how may I assist you today?"
We are a premier repair store and certified service lab fixing:
1. Mobiles (iPhone, Samsung Galaxy, Google Pixel, OnePlus - cracked OLED/LCD screens, shattered back glass, degraded battery replacement, charging port repair, water damage recovery, camera module repair).
2. Laptops (MacBook Pro/Air, Dell, HP, Lenovo, ThinkPad, Asus - cracked displays, keyboard and trackpad repair, battery replacement, deep fan cleaning & thermal repasting, SSD/RAM upgrades, motherboard repairs).
3. Earphones & Audio Gear (Apple AirPods, Galaxy Buds, Sony WH-1000XM, Bose QuietComfort, Beats - battery replacement, ear cushion replacement, mesh wax cleaning, audio balance distortion fix, charging cases).
4. Other Gadgets (Apple Watch, Galaxy Watch, iPad, tablets, Nintendo Switch joy-con drift, gaming consoles).

CURRENCY RULE:
All repair quotes, service fees, and parts MUST be quoted in Indian Rupees (₹ / INR). Never use USD or $ symbols.

Your core capabilities:
- Diagnose hardware glitches, physical damage, and software errors from customer descriptions and defect photos.
- Provide initial troubleshooting steps (soft reset, lint cleaning, frequency reset) when a DIY fix is safe.
- If physical repair or replacement parts are needed, give clear pricing in Indian Rupees (₹) and estimated turnaround time (e.g. "30-45 mins walk-in or express mail-in").
- Whenever a repair service, diagnostic fee, or replacement part is relevant, append an interactive booking/checkout card block at the bottom of your response in this exact JSON format so the customer can book repair or checkout immediately:
:::product
{
  "id": "iphone-back-glass-repair",
  "name": "iPhone Back Glass Laser Removal & Replacement",
  "price": 2499,
  "currency": "INR",
  "category": "Mobile Repair Service",
  "compatibility": "iPhone 12 / 13 / 14 / 15 series",
  "turnaround": "45 Mins Walk-in or Express",
  "warranty": "90-Day Guarantee",
  "inStock": true,
  "desc": "Precision laser extraction of shattered back glass and OEM-grade tempered glass panel installation."
}
:::

Common repair catalog items in our store (all prices in Indian Rupees ₹):
- "iPhone Back Glass Laser Removal & Replacement" (₹2,499, id: "iphone-back-glass-repair", category: "Mobile Repair")
- "iPhone OLED Screen & Digitizer Assembly" (₹4,999, id: "iphone-screen-repair", category: "Mobile Screen")
- "Mobile OEM Battery Replacement (100% Health)" (₹1,899, id: "mobile-battery-repair", category: "Mobile Battery")
- "MacBook / Laptop Screen & Display Assembly" (₹8,999, id: "laptop-screen-repair", category: "Laptop Screen")
- "MacBook Pro / Air High-Capacity Battery" (₹4,999, id: "macbook-battery-repair", category: "Laptop Service")
- "Laptop Deep Thermal Cleaning & Fan Service" (₹999, id: "laptop-thermal-service", category: "Laptop Maintenance")
- "AirPods / Earbuds Battery & Audio Restoration" (₹1,299, id: "airpods-battery-fix", category: "Audio Service")
- "Apex / Sony Pro Cooling-Gel Ear Cushions (Pair)" (₹899, id: "ear-cushions-pair", category: "Audio Accessories")
- "USB-C / Lightning Port Cleaning & Pin Repair" (₹699, id: "port-repair-service", category: "Hardware Repair")
- "Full Diagnostic Bench Inspection & Water Damage Clean" (₹299, id: "diagnostic-bench-fee", category: "Diagnostic Service")

Format replies in clean, friendly Markdown with clear step-by-step guidance. Maintain a welcoming, professional repair technician tone and emphasize our 90-day Iris warranty on all repairs."""

def text_response(prompt, system=None, history=None):
    instructions = system or SUPPORT_SYSTEM_PROMPT
    if history and isinstance(history, list):
        formatted_input: list[dict[str, Any]] = []
        for item in history:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            if role not in ("user", "assistant"):
                continue
            content = item.get("content") or item.get("text") or ""
            if isinstance(content, list):
                text_parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("text")]
                content = " ".join(text_parts)
            content_str = str(content).strip()
            if content_str:
                formatted_input.append({
                    "role": role,
                    "content": content_str
                })
        
        # Ensure current prompt is included at the end
        if prompt:
            clean_prompt = prompt.strip()
            if not formatted_input or formatted_input[-1].get("role") != "user" or formatted_input[-1].get("content") != clean_prompt:
                formatted_input.append({"role": "user", "content": clean_prompt})
        
        if formatted_input:
            # Keep up to 20 messages for rich multi-turn context
            recent_context = formatted_input[-20:]
            r = client().responses.create(
                model=TEXT_MODEL,
                instructions=instructions,
                input=cast(Any, recent_context)
            )
            return r.output_text

    r = client().responses.create(model=TEXT_MODEL, instructions=instructions, input=prompt)
    return r.output_text

@app.get("/")
def home(): return render_template("home.html")

@app.get("/chat")
def chat(): return render_template("home.html")

@app.post("/api/chat")
def api_chat():
    try:
        body = request.json or {}
        p = body.get("message", "").strip()
        history = body.get("history") or []
        if not p: return jsonify(error="Enter a message."), 400
        clean_p = p.lower().strip("!.,? ")
        # Only greet if this is the start of a conversation with no history
        if not history and clean_p in ("hi", "hello", "hey", "hi iris", "hello iris", "hey iris", "greetings", "hi there", "hello there"):
            return jsonify(reply="Hello! Iris here, how may I assist you today? Whether you need hardware diagnostics, repair pricing in ₹ INR, or troubleshooting for your mobile, laptop, earphones, or gadget, I'm here to help!")
        return jsonify(reply=text_response(p, history=history))
    except Exception as e: return jsonify(error=str(e)), 500

@app.post("/api/checkout")
def api_checkout():
    try:
        data = request.json or {}
        items = data.get("items", [])
        total = data.get("total", 0)
        order_id = f"FIX-{uuid.uuid4().hex[:6].upper()}"
        return jsonify(
            success=True,
            order_id=order_id,
            status="Repair Booked & Confirmed",
            delivery_estimate="Same-Day 45-Min Repair or Express Mail-In",
            total=total,
            items_count=len(items)
        )
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.post("/api/warranty-check")
def api_warranty():
    try:
        serial = (request.json or {}).get("serial", "APX-89204-PRO").strip().upper()
        return jsonify(
            serial=serial or "IMEI-358920-04-192840",
            product="Smartphone / Gadget Repair Plan",
            status="Active Coverage",
            plan="Iris Pro Protection (90-Day Warranty)",
            expires="December 2027",
            accidental_damage=True,
            battery_health="Diagnostic Passed"
        )
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.get("/text-analysis")
def text_analysis(): return render_template("text_analysis.html")

@app.post("/api/text-analysis")
def api_text_analysis():
    try:
        text=(request.json or {}).get("text","").strip()
        if not text: return jsonify(error="Enter text."),400
        prompt=f"""Analyze the following text and return exactly these sections:
1. Sentiment
2. Keywords
3. Entities (organization, person, location, date, product where applicable)
4. Summary

TEXT:
{text}"""
        return jsonify(result=text_response(prompt))
    except Exception as e: return jsonify(error=str(e)),500

@app.get("/vision")
def vision(): return render_template("vision.html")

@app.post("/api/vision")
def api_vision():
    try:
        f = request.files.get("image")
        prompt = request.form.get("prompt", "Describe this image in detail.").strip()
        history_raw = request.form.get("history")
        if not f: return jsonify(error="Upload an image."), 400
        data = base64.b64encode(f.read()).decode()
        mime = f.mimetype or "image/jpeg"
        vision_instructions = """You are Iris, Master Gadget Diagnostic Technician. Inspect customer photos of broken or damaged electronics (smartphones with cracked front glass or shattered back glass, broken laptop screens or hinges, damaged earphone cushions or dead earbuds, bent charging ports).
1. Identify the device make and model (e.g. iPhone with matte glass and triple-camera layout, MacBook Pro, Galaxy, AirPods, etc.).
2. Detail the exact physical damage (e.g., severe impact fracture on rear glass near camera module, spiderweb glass cracks, frame scuffs).
3. State whether the screen digitizer, camera lens, or housing is intact or compromised.
4. Recommend the exact repair service needed (e.g., Laser Back Glass Removal & OEM Glass Replacement).
5. State the turnaround time (e.g., 45 minutes) and provide the estimated repair price in Indian Rupees (₹ / INR, e.g. ₹2,499).
6. When applicable, append our standard :::product { "id": "...", "name": "...", "price": ..., "currency": "INR", ... } ::: block so the customer can book repair or checkout directly!"""
        
        vision_input: list[Any] = []
        if history_raw:
            try:
                past = json.loads(history_raw) if isinstance(history_raw, str) else history_raw
                if isinstance(past, list):
                    for msg in past[-10:]:
                        if isinstance(msg, dict):
                            r_role = msg.get("role")
                            r_content = msg.get("content") or msg.get("text") or ""
                            if r_role in ("user", "assistant") and str(r_content).strip():
                                vision_input.append({
                                    "role": r_role,
                                    "content": str(r_content).strip()
                                })
            except Exception:
                pass

        vision_input.append({"role": "user", "content": [
            {"type": "input_text", "text": prompt},
            {"type": "input_image", "image_url": f"data:{mime};base64,{data}"}
        ]})

        r = client().responses.create(  # pyrefly: ignore[no-matching-overload]
            model=VISION_MODEL,
            instructions=vision_instructions,
            input=cast(Any, vision_input)
        )
        return jsonify(result=r.output_text)
    except Exception as e: return jsonify(error=str(e)), 500

@app.get("/image-generation")
def image_generation(): return render_template("image_generation.html")

@app.post("/api/image-generation")
def api_image_generation():
    try:
        prompt=(request.json or {}).get("prompt","").strip()
        if not prompt: return jsonify(error="Enter a prompt."),400
        if not IMAGE_MODEL:
            raise RuntimeError("Set IMAGE_MODEL_DEPLOYMENT to your FLUX-1.1-pro deployment name.")
        r=image_client().images.generate(model=IMAGE_MODEL,prompt=prompt,n=1,size="1024x1024")
        if not r.data:
            raise RuntimeError("No image data returned from image generation API.")
        item=r.data[0]  # pyrefly: ignore[unsupported-operation]
        if getattr(item,"b64_json",None):
            raw=base64.b64decode(item.b64_json)
            name=f"{uuid.uuid4().hex}.png"; path=os.path.join("uploads",name)
            open(path,"wb").write(raw)
            return jsonify(url=f"/uploads/{name}")
        return jsonify(url=getattr(item,"url",None))
    except Exception as e: return jsonify(error=str(e)),500

@app.get("/speech")
def speech(): return render_template("speech.html")

@app.post("/api/speech")
def api_speech():
    try:
        f=request.files.get("audio")
        if not f: return jsonify(error="Upload an audio file."),400
        if not SPEECH_KEY: raise RuntimeError("Set SPEECH_API_KEY.")
        # Azure Speech REST endpoint for short audio transcription.
        # The exact language can be changed in the UI.
        language=request.form.get("language","en-US")
        url=f"{SPEECH_ENDPOINT}/speechtotext/v3.2/transcriptions:transcribe?api-version=2024-11-15"
        headers={"Ocp-Apim-Subscription-Key":SPEECH_KEY}
        files={"audio":(f.filename,f.stream,f.mimetype or "audio/wav")}
        data={"definition":'{"locales":["'+language+'"],"profanityFilterMode":"Masked"}'}
        r=requests.post(url,headers=headers,files=files,data=data,timeout=120)
        if not r.ok:
            # Fall back to the common Speech SDK route through a helpful error.
            return jsonify(error=f"Speech service returned {r.status_code}: {r.text}"),r.status_code
        return jsonify(result=r.json())
    except Exception as e: return jsonify(error=str(e)),500

@app.get("/content-understanding")
def content_understanding(): return render_template("content.html")

@app.post("/api/content-understanding")
def api_content():
    try:
        f=request.files.get("file")
        analyzer=request.form.get("analyzer","prebuilt-documentSearch")
        if not f: return jsonify(error="Upload a file."),400
        if not CONTENT_ENDPOINT or not CONTENT_KEY:
            raise RuntimeError("Set CONTENT_ENDPOINT and CONTENT_API_KEY.")
        url=f"{CONTENT_ENDPOINT}/contentunderstanding/analyzers/{analyzer}:analyze?api-version={CONTENT_API_VERSION}"
        headers={"Ocp-Apim-Subscription-Key":CONTENT_KEY}
        # Content Understanding supports file bytes in multipart for current REST patterns.
        r=requests.post(url,headers=headers,files={"file":(f.filename,f.stream,f.mimetype)},timeout=180)
        if not r.ok:
            return jsonify(error=f"Content Understanding returned {r.status_code}: {r.text}"),r.status_code
        return jsonify(result=r.json())
    except Exception as e: return jsonify(error=str(e)),500

@app.get("/agent")
def agent(): return render_template("agent.html")

@app.post("/api/agent")
def api_agent():
    try:
        p=(request.json or {}).get("message","").strip()
        if not p:return jsonify(error="Enter a message."),400
        # Uses the same deployed model with agent-like instructions if no persisted agent ID is supplied.
        system="""You are a Microsoft Foundry teaching agent. Explain technical topics clearly,
step by step, with a definition, example, and practical use case."""
        return jsonify(reply=text_response(p,system))
    except Exception as e:return jsonify(error=str(e)),500

@app.get("/uploads/<name>")
def uploads(name): return send_file(os.path.join("uploads", os.path.basename(name)))

@app.route("/crawl", methods=["GET", "POST"])
def crawl_view():
    if request.method == "POST":
        return api_crawl()
    return render_template("crawl.html")

@app.post("/api/crawl")
def api_crawl():
    try:
        data = request.json if request.is_json else request.form.to_dict()
        data = data or {}
        query = data.get("query", "").strip()
        mode = data.get("mode", "all")
        url = data.get("url", "").strip()
        category = data.get("category", "all")

        ai_cli = None
        try:
            if AOAI_ENDPOINT and AOAI_KEY:
                ai_cli = client()
        except Exception:
            pass

        results = crawler.federated_crawl(
            query=query,
            mode=mode,
            url=url,
            category_filter=category,
            ai_client=ai_cli,
            text_model=TEXT_MODEL
        )
        return jsonify(results)
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.get("/api/crawl/guide/<int:guide_id>")
def api_crawl_guide(guide_id):
    try:
        url = f"https://www.ifixit.com/api/2.0/guides/{guide_id}"
        resp = requests.get(url, headers={"User-Agent": "IrisRepairCrawler/1.0"}, timeout=6)
        if resp.status_code == 200:
            return jsonify(resp.json())
        return jsonify(error="Guide not found on iFixit"), resp.status_code
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.get("/health")
def health():
    return jsonify(text_model=bool(TEXT_MODEL), vision_model=bool(VISION_MODEL),
                   image_model=bool(IMAGE_MODEL), speech=bool(SPEECH_KEY),
                   content_understanding=bool(CONTENT_KEY),
                   crawler=True)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
    app.run(debug=debug, host="0.0.0.0", port=port)
