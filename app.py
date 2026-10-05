import os, base64, mimetypes, uuid, requests, json, crawler
from urllib.parse import quote
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Any, cast
from dotenv import load_dotenv  # pyrefly: ignore[missing-import]
from openai import OpenAI  # pyrefly: ignore[missing-import]

# Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import credentials, auth as fb_admin_auth
except ImportError:
    firebase_admin = None
    fb_admin_auth = None

load_dotenv()
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("SECRET_KEY", "iris-chatgpt-auth-secret-key-2026-v1")
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.jinja_env.auto_reload = True
os.makedirs("uploads", exist_ok=True)

# Initialize Firebase Admin app safely
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "iris-repair-copilot")
FIREBASE_SERVICE_ACCOUNT = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
if firebase_admin and not firebase_admin._apps:
    try:
        if FIREBASE_SERVICE_ACCOUNT and os.path.exists(FIREBASE_SERVICE_ACCOUNT):
            cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT)
            firebase_admin.initialize_app(cred)
        else:
            firebase_admin.initialize_app(options={"projectId": FIREBASE_PROJECT_ID})
    except Exception:
        pass
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

# In-Memory User Registry for ChatGPT-Style Authentication
USERS_STORE: dict[str, dict[str, Any]] = {
    "rahul@gmail.com": {
        "id": "usr_rahul",
        "name": "Rahul Sharma",
        "email": "rahul@gmail.com",
        "password_hash": generate_password_hash("password123"),
        "role": "customer",
        "plan": "Iris Pro Member",
        "avatar_initials": "RS",
        "avatar_color": "#7c3aed",
        "created_at": "March 2026",
        "recent_orders": ["FIX-8A201C"]
    },
    "user@iris.com": {
        "id": "usr_demo",
        "name": "Iris Explorer",
        "email": "user@iris.com",
        "password_hash": generate_password_hash("iris2026"),
        "role": "customer",
        "plan": "Standard User",
        "avatar_initials": "IE",
        "avatar_color": "#2563eb",
        "created_at": "Today",
        "recent_orders": []
    },
    "arvind@iris.com": {
        "id": "usr_tech_arvind",
        "name": "Arvind M.",
        "email": "arvind@iris.com",
        "password_hash": generate_password_hash("admin123"),
        "role": "technician",
        "plan": "Senior Certified Tech",
        "avatar_initials": "AM",
        "avatar_color": "#10b981",
        "created_at": "January 2026",
        "recent_orders": ["FIX-8A201C", "FIX-94E21A"]
    }
}

def sanitize_user(user: dict[str, Any]) -> dict[str, Any]:
    """Return public user dict safe for client consumption."""
    return {k: v for k, v in user.items() if k != "password_hash"}

@app.get("/")
def home():
    user = session.get("user")
    return render_template("home.html", user=user)

@app.get("/chat")
def chat():
    user = session.get("user")
    return render_template("home.html", user=user)

@app.get("/login")
def login_view():
    if session.get("user"):
        return redirect(request.args.get("next") or url_for("home"))
    return render_template("login.html", mode="login")

@app.get("/signup")
def signup_view():
    if session.get("user"):
        return redirect(request.args.get("next") or url_for("home"))
    return render_template("login.html", mode="signup")

@app.get("/logout")
def logout_view():
    session.pop("user", None)
    return redirect(url_for("home"))

@app.get("/api/auth/status")
def api_auth_status():
    user = session.get("user")
    return jsonify(authenticated=bool(user), user=user)

@app.post("/api/auth/login")
def api_auth_login():
    try:
        data = request.json or {}
        email = (data.get("email") or "").strip().lower()
        password = (data.get("password") or "").strip()

        if not email:
            return jsonify(error="Please enter your email address."), 400
        if not password:
            return jsonify(error="Please enter your password."), 400

        user = USERS_STORE.get(email)
        if not user:
            return jsonify(error="No account found with this email. Click 'Sign up' to create one or use Demo accounts."), 401

        if not check_password_hash(user["password_hash"], password):
            return jsonify(error="Incorrect password. Please verify and try again."), 401

        clean_user = sanitize_user(user)
        session["user"] = clean_user
        return jsonify(success=True, user=clean_user, message=f"Welcome back, {clean_user['name']}!")
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.post("/api/auth/signup")
def api_auth_signup():
    try:
        data = request.json or {}
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = (data.get("password") or "").strip()

        if not email or "@" not in email:
            return jsonify(error="Please enter a valid email address."), 400
        if not password or len(password) < 6:
            return jsonify(error="Password must be at least 6 characters long."), 400
        if not name:
            name = email.split("@")[0].replace(".", " ").title()

        if email in USERS_STORE:
            return jsonify(error="An account with this email already exists. Please log in instead."), 409

        parts = name.split()
        initials = (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")).upper()
        if not initials:
            initials = email[0].upper()

        new_user = {
            "id": f"usr_{uuid.uuid4().hex[:8]}",
            "name": name,
            "email": email,
            "password_hash": generate_password_hash(password),
            "role": "customer",
            "plan": "Iris Pro Member",
            "avatar_initials": initials,
            "avatar_color": "#7c3aed",
            "created_at": "Today",
            "recent_orders": []
        }
        USERS_STORE[email] = new_user
        clean_user = sanitize_user(new_user)
        session["user"] = clean_user
        return jsonify(success=True, user=clean_user, message=f"Welcome to Iris, {name}!")
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.post("/api/auth/social")
def api_auth_social():
    try:
        data = request.json or {}
        provider = (data.get("provider") or "google").strip().lower()
        providers_map = {
            "google": {
                "name": "Alex Chen",
                "email": "alex.chen.work@gmail.com",
                "initials": "AC",
                "color": "#ea4335"
            },
            "microsoft": {
                "name": "Jordan Taylor",
                "email": "jordan.taylor@outlook.com",
                "initials": "JT",
                "color": "#00a4ef"
            },
            "apple": {
                "name": "Sam Rivera",
                "email": "sam.rivera@icloud.com",
                "initials": "SR",
                "color": "#0f172a"
            }
        }
        prof = providers_map.get(provider, providers_map["google"])
        email = prof["email"]

        if email not in USERS_STORE:
            USERS_STORE[email] = {
                "id": f"usr_{provider}_{uuid.uuid4().hex[:6]}",
                "name": prof["name"],
                "email": email,
                "password_hash": generate_password_hash("social-token-iris-2026"),
                "role": "customer",
                "plan": "Iris Pro Member",
                "avatar_initials": prof["initials"],
                "avatar_color": prof["color"],
                "created_at": "Today",
                "recent_orders": ["FIX-8A201C"]
            }

        user = USERS_STORE[email]
        clean_user = sanitize_user(user)
        session["user"] = clean_user
        return jsonify(success=True, user=clean_user, message=f"Connected via {provider.capitalize()}!")
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.post("/api/auth/logout")
def api_auth_logout():
    session.pop("user", None)
    return jsonify(success=True, message="Successfully logged out")

@app.get("/api/auth/firebase-config")
def api_firebase_config():
    """Exposes Firebase client configuration for Web Auth SDK."""
    return jsonify({
        "apiKey": os.getenv("FIREBASE_API_KEY", "AIzaSyDemo-iris-gadget-repair-auth-key"),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", "iris-repair-copilot.firebaseapp.com"),
        "projectId": os.getenv("FIREBASE_PROJECT_ID", "iris-repair-copilot"),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", "iris-repair-copilot.appspot.com"),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", "839102948102"),
        "appId": os.getenv("FIREBASE_APP_ID", "1:839102948102:web:9f8a02c81928019284")
    })

@app.post("/api/auth/firebase-session")
def api_firebase_session():
    """Receives Firebase ID Token and User Profile, creates/syncs authenticated session."""
    try:
        data = request.json or {}
        id_token = data.get("id_token", "")
        user_info = data.get("user") or {}

        email = (user_info.get("email") or "").strip().lower()
        name = (user_info.get("displayName") or user_info.get("name") or "").strip()
        uid = user_info.get("uid") or f"fb_{uuid.uuid4().hex[:8]}"
        photo_url = user_info.get("photoURL") or ""
        provider_id = user_info.get("providerId") or "firebase"

        # Verify Firebase ID token if live admin SDK is active
        if id_token and fb_admin_auth:
            try:
                verified_claims = fb_admin_auth.verify_id_token(id_token, check_revoked=False)
                if verified_claims:
                    uid = verified_claims.get("uid") or uid
                    email = (verified_claims.get("email") or email).lower()
                    name = verified_claims.get("name") or name
            except Exception:
                pass

        if not email:
            email = f"user_{uid[:8]}@firebase.iris"
        if not name:
            name = email.split("@")[0].replace(".", " ").title()

        parts = name.split()
        initials = (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")).upper()
        if not initials:
            initials = email[0].upper()

        if email in USERS_STORE:
            user = USERS_STORE[email]
            user["firebase_uid"] = uid
            if photo_url: user["photo_url"] = photo_url
            user["auth_provider"] = "firebase"
        else:
            user = {
                "id": f"usr_fb_{uid[:8]}",
                "firebase_uid": uid,
                "name": name,
                "email": email,
                "password_hash": generate_password_hash("firebase-auth-verified"),
                "role": "customer",
                "plan": "Iris Pro Member",
                "avatar_initials": initials,
                "avatar_color": "#f59e0b" if "google" in provider_id else "#7c3aed",
                "photo_url": photo_url,
                "auth_provider": "firebase",
                "created_at": "Today",
                "recent_orders": ["FIX-8A201C"]
            }
            USERS_STORE[email] = user

        clean_user = sanitize_user(user)
        session["user"] = clean_user
        return jsonify(success=True, user=clean_user, message=f"Firebase login successful: {clean_user['name']}")
    except Exception as e:
        return jsonify(error=str(e)), 500


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

# In-Memory Production Store for Live Repair Tracking & Callback Requests
ORDERS_STORE: dict[str, Any] = {
    "FIX-8A201C": {
        "order_id": "FIX-8A201C",
        "customer_name": "Rahul Sharma",
        "phone": "+91 98765 43210",
        "device": "Apple iPhone 14 Pro Max (Deep Purple, 256GB)",
        "imei": "358920-04-192840-2",
        "created_at": "Today, 09:15 AM",
        "current_step": 3,
        "status_title": "Precision Laser Glass Removal in Progress",
        "status_desc": "Technician Arvind M. is performing laser rear back glass removal and installing genuine OEM tempered glass panel.",
        "turnaround_estimate": "Estimated completion today by 10:45 AM (30 mins remaining)",
        "technician": "Arvind M. (Master Certified Apple & Samsung Tech)",
        "warranty": "90-Day Iris Warranty Guarantee",
        "total": 2949.00,
        "items": [
            {"name": "iPhone Back Glass Laser Removal & Replacement", "price": 2499, "category": "Mobile Repair"},
            {"name": "Full Diagnostic Bench Inspection & Water Damage Clean", "price": 299, "category": "Diagnostic Service"}
        ],
        "steps": [
            {"number": 1, "title": "Device Intake & Inspection", "desc": "Logged into Iris repair portal, serial & defect photographed", "time": "09:15 AM", "status": "completed"},
            {"number": 2, "title": "Cleanroom Bench Diagnostic", "desc": "Digitizer touch, True Tone sensor, and camera verified", "time": "09:25 AM", "status": "completed"},
            {"number": 3, "title": "Laser Extraction & Glass Replacement", "desc": "Fiber-laser ablation and OEM glass clamping in progress", "time": "09:40 AM", "status": "active"},
            {"number": 4, "title": "Pressure & Waterproof Gasket QC", "desc": "IP68 water-resistance seal and sensor bench test", "time": "Pending", "status": "pending"},
            {"number": 5, "title": "Ready for Store Pickup / Delivery", "desc": "Customer notification and 90-day warranty card issuance", "time": "Pending", "status": "pending"}
        ]
    },
    "FIX-DEMO01": {
        "order_id": "FIX-DEMO01",
        "customer_name": "Ananya Roy",
        "phone": "+91 98450 11223",
        "device": "MacBook Pro 16\" (M2 Pro, Space Gray)",
        "imei": "C02G901ZMD6M",
        "created_at": "Yesterday, 04:30 PM",
        "current_step": 4,
        "status_title": "Thermal Stress & QC Testing",
        "status_desc": "Battery cell installed successfully. Running multi-core stress test and thermal fan calibration.",
        "turnaround_estimate": "Ready for pickup today at 11:30 AM",
        "technician": "Priya S. (Senior Apple Certified Mac Engineer)",
        "warranty": "90-Day Iris Guarantee",
        "total": 5898.00,
        "items": [
            {"name": "MacBook Pro High-Capacity Battery Pack", "price": 4999, "category": "Laptop Service"},
            {"name": "Deep Thermal Cleaning & Heatsink Repaste", "price": 999, "category": "Laptop Maintenance"}
        ],
        "steps": [
            {"number": 1, "title": "Device Intake & Inspection", "desc": "Diagnostic scan verified 68% battery health and throttled fans", "time": "Yesterday, 04:30 PM", "status": "completed"},
            {"number": 2, "title": "Safety Teardown", "desc": "Logic board isolated and swollen battery solvent-released", "time": "Yesterday, 05:15 PM", "status": "completed"},
            {"number": 3, "title": "OEM Battery Pack & Fan Service", "desc": "New Grade-A cells installed and liquid metal thermal paste applied", "time": "Today, 09:00 AM", "status": "completed"},
            {"number": 4, "title": "Thermal Stress & QC Testing", "desc": "Full battery charge-discharge cycle and sensor benchmarking", "time": "Today, 09:45 AM", "status": "active"},
            {"number": 5, "title": "Ready for Store Pickup", "desc": "Packaging with Iris certified repair certificate", "time": "Pending", "status": "pending"}
        ]
    },
    "FIX-94E21A": {
        "order_id": "FIX-94E21A",
        "customer_name": "Vikram Patel",
        "phone": "+91 97123 99881",
        "device": "Apple AirPods Pro (2nd Generation)",
        "imei": "H2LG4001PQ9X",
        "created_at": "Today, 08:30 AM",
        "current_step": 5,
        "status_title": "Ready for Customer Pickup / Dispatch",
        "status_desc": "Both earbuds balanced, acoustic mesh ultrasonically cleaned, new micro-battery operating at 100%.",
        "turnaround_estimate": "Ready Now for Store Pickup or Courier Dispatch",
        "technician": "Arvind M. (Master Certified Tech)",
        "warranty": "90-Day Iris Guarantee",
        "total": 1532.00,
        "items": [
            {"name": "AirPods Audio & Battery Restoration", "price": 1299, "category": "Audio Service"}
        ],
        "steps": [
            {"number": 1, "title": "Intake & Audio Spectrum Test", "desc": "Left earbud confirmed 65% quieter with clogged mesh", "time": "08:30 AM", "status": "completed"},
            {"number": 2, "title": "Ultrasonic Cleaning", "desc": "Solvent cerumen removal and mesh drying", "time": "08:45 AM", "status": "completed"},
            {"number": 3, "title": "Battery Cell Micro-Soldering", "desc": "Button cell replaced and sealed with UV adhesive", "time": "09:05 AM", "status": "completed"},
            {"number": 4, "title": "Frequency Spectrum QC Check", "desc": "Left and right stereo decibel parity confirmed", "time": "09:20 AM", "status": "completed"},
            {"number": 5, "title": "Ready for Pickup", "desc": "Disinfected and packaged in Iris seal pouch", "time": "09:30 AM", "status": "active"}
        ]
    }
}

CALLBACKS_STORE = []

@app.post("/api/checkout")
def api_checkout():
    try:
        data = request.json or {}
        items = data.get("items", [])
        total = data.get("total", 0)
        order_id = f"FIX-{uuid.uuid4().hex[:6].upper()}"
        
        # Save to live tracking store
        first_item_name = items[0].get("name", "Gadget Repair Service") if items else "Gadget Repair"
        device_guess = items[0].get("compatibility", "Electronic Device") if items else "Smartphone / Laptop"
        order_data: dict[str, Any] = {
            "order_id": order_id,
            "customer_name": data.get("customer_name") or "Valued Customer",
            "phone": data.get("phone") or "+91 Verified",
            "device": f"{device_guess} - {first_item_name}",
            "imei": f"IMEI-35{uuid.uuid4().int % 1000000:06d}-88",
            "created_at": "Just now",
            "current_step": 1,
            "status_title": "Repair Booking Confirmed & Station Allocated",
            "status_desc": "Your repair ticket is active. OEM inventory parts are tagged and cleanroom bench is ready.",
            "turnaround_estimate": "Same-Day Completion (45 Mins upon check-in)",
            "technician": "Arvind M. (Master Certified Apple & Samsung Tech)",
            "warranty": "90-Day Iris Guarantee",
            "total": float(total) if total else 2499.00,
            "items": items or [{"name": first_item_name, "price": float(total) if total else 2499.00, "category": "Repair Service"}],
            "steps": [
                {"number": 1, "title": "Booking Received & Verified", "desc": "Order logged and OEM parts reserved", "time": "Just now", "status": "active"},
                {"number": 2, "title": "Cleanroom Bench Inspection", "desc": "Hardware sensor check & safety teardown", "time": "Pending", "status": "pending"},
                {"number": 3, "title": "Precision Component Replacement", "desc": "Laser repair and OEM module installation", "time": "Pending", "status": "pending"},
                {"number": 4, "title": "Waterproof & Pressure QC", "desc": "Bench testing and seal verification", "time": "Pending", "status": "pending"},
                {"number": 5, "title": "Ready for Pickup / Dispatch", "desc": "Disinfected and packaged with warranty card", "time": "Pending", "status": "pending"}
            ]
        }
        ORDERS_STORE[order_id] = order_data
        
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

@app.route("/api/track", methods=["GET", "POST"])
def api_track():
    try:
        data = request.json if request.is_json else request.args
        order_id = (data.get("order_id") or data.get("id") or "").strip().upper()
        if not order_id:
            return jsonify(
                demo_orders=list(ORDERS_STORE.keys()),
                error="Please enter an Order / Ticket ID (e.g. FIX-8A201C)"
            ), 400

        order = ORDERS_STORE.get(order_id)
        if not order:
            # Dynamically synthesize a live in-progress ticket for any custom ID entered
            order = {
                "order_id": order_id,
                "customer_name": "Valued Customer",
                "phone": "+91 Verified",
                "device": "Registered Flagship Gadget",
                "imei": f"IMEI-35{abs(hash(order_id)) % 1000000:06d}-01",
                "created_at": "Today, Intake Logged",
                "current_step": 2,
                "status_title": "Diagnostic Bench Inspection in Progress",
                "status_desc": "Certified technician is conducting teardown inspection and verifying component integrity.",
                "turnaround_estimate": "Estimated completion within 45 mins",
                "technician": "Priya S. (Senior Hardware Specialist)",
                "warranty": "90-Day Iris Guarantee",
                "total": 2499.00,
                "items": [{"name": "Standard Hardware Diagnostic & Repair Service", "price": 2499, "category": "Hardware Repair"}],
                "steps": [
                    {"number": 1, "title": "Device Intake & Inspection", "desc": "Logged into Iris repair system", "time": "Completed", "status": "completed"},
                    {"number": 2, "title": "Cleanroom Bench Inspection", "desc": "Diagnostic scan and component verification", "time": "In Progress", "status": "active"},
                    {"number": 3, "title": "Component Replacement", "desc": "Installation of OEM grade parts", "time": "Pending", "status": "pending"},
                    {"number": 4, "title": "Quality Bench Test", "desc": "Full functional testing and waterproofing check", "time": "Pending", "status": "pending"},
                    {"number": 5, "title": "Ready for Pickup", "desc": "Ready for customer handover", "time": "Pending", "status": "pending"}
                ]
            }
        return jsonify(success=True, order=order)
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.post("/api/technician-callback")
def api_technician_callback():
    try:
        data = request.json or {}
        phone = data.get("phone", "").strip()
        name = data.get("name", "Customer").strip()
        device = data.get("device", "Electronic Device").strip()
        issue = data.get("issue", "Hardware Fault / Diagnostic Request").strip()
        time_slot = data.get("time_slot", "Within 15 minutes").strip()
        if not phone:
            return jsonify(error="Please provide a valid contact number."), 400
        
        callback_id = f"CALL-{uuid.uuid4().hex[:6].upper()}"
        CALLBACKS_STORE.append({
            "callback_id": callback_id,
            "name": name,
            "phone": phone,
            "device": device,
            "issue": issue,
            "time_slot": time_slot,
            "timestamp": "Just now",
            "assigned_technician": "Arvind M. (Master Repair Tech)"
        })
        
        wa_text = f"Hi Iris Lab, I need senior technician consultation for my {device}. Issue: {issue}. Reference: {callback_id}"
        wa_url = f"https://wa.me/919876543210?text={quote(wa_text)}"
        
        return jsonify(
            success=True,
            callback_id=callback_id,
            assigned_technician="Arvind M. (Master Repair Tech)",
            eta=time_slot,
            message=f"Callback confirmed! Master Tech Arvind M. will call you {time_slot}.",
            whatsapp_url=wa_url
        )
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.get("/api/calculator")
def api_calculator():
    try:
        options = {
            "categories": [
                {
                    "id": "smartphones",
                    "name": "Smartphones",
                    "icon": "phone",
                    "models": [
                        "iPhone 15 / 15 Pro / Pro Max",
                        "iPhone 14 / 14 Pro / Pro Max",
                        "iPhone 13 / 13 Pro",
                        "iPhone 12 / 11 / XR",
                        "Samsung Galaxy S24 / S23 Ultra",
                        "Samsung Galaxy Z Fold / Z Flip",
                        "Google Pixel 8 / 7 Pro",
                        "OnePlus 12 / 11 / 10 Pro"
                    ],
                    "issues": [
                        {"id": "screen", "name": "Cracked OLED Screen & Touch Digitizer", "price": 4999, "turnaround": "30 Mins", "warranty": "90 Days"},
                        {"id": "back-glass", "name": "Shattered Back Glass (Laser Extraction)", "price": 2499, "turnaround": "45 Mins", "warranty": "90 Days"},
                        {"id": "battery", "name": "OEM Battery Replacement (100% Health)", "price": 1899, "turnaround": "25 Mins", "warranty": "90 Days"},
                        {"id": "charging-port", "name": "USB-C / Lightning Port Repair & Cleaning", "price": 699, "turnaround": "20 Mins", "warranty": "90 Days"},
                        {"id": "camera", "name": "Rear Camera Module / Broken Lens Glass", "price": 2199, "turnaround": "40 Mins", "warranty": "90 Days"},
                        {"id": "water-damage", "name": "Liquid Damage Ultrasonic Clean & Micro-Solder", "price": 1499, "turnaround": "2 Hours", "warranty": "90 Days"}
                    ]
                },
                {
                    "id": "laptops",
                    "name": "Laptops & MacBooks",
                    "icon": "laptop",
                    "models": [
                        "Apple MacBook Pro (M1/M2/M3 / Intel)",
                        "Apple MacBook Air (M1/M2/M3)",
                        "Dell XPS 13 / 15 / Inspiron",
                        "Lenovo ThinkPad X1 / Legion",
                        "HP Spectre / Envy / Pavilion",
                        "ASUS ROG / ZenBook"
                    ],
                    "issues": [
                        {"id": "laptop-screen", "name": "Retina / IPS Display Panel Assembly", "price": 8999, "turnaround": "2 Hours", "warranty": "90 Days"},
                        {"id": "laptop-battery", "name": "High-Capacity OEM Battery Pack", "price": 4999, "turnaround": "45 Mins", "warranty": "90 Days"},
                        {"id": "thermal", "name": "Deep Thermal Cleaning & Heatsink Repaste", "price": 999, "turnaround": "45 Mins", "warranty": "90 Days"},
                        {"id": "keyboard", "name": "Keyboard Assembly & Sticky Trackpad Fix", "price": 3299, "turnaround": "90 Mins", "warranty": "90 Days"},
                        {"id": "hinge", "name": "Broken Display Hinge & Chassis Alignment", "price": 1899, "turnaround": "60 Mins", "warranty": "90 Days"},
                        {"id": "ssd-ram", "name": "NVMe SSD & High-Speed RAM Upgrade", "price": 2499, "turnaround": "30 Mins", "warranty": "90 Days"}
                    ]
                },
                {
                    "id": "audio",
                    "name": "Earphones & Audio",
                    "icon": "headphones",
                    "models": [
                        "Apple AirPods Pro 1 / 2",
                        "Apple AirPods 2 / 3",
                        "Apple AirPods Max",
                        "Sony WF-1000XM4 / XM5",
                        "Sony WH-1000XM4 / XM5",
                        "Bose QuietComfort Earbuds / 45"
                    ],
                    "issues": [
                        {"id": "earbud-battery", "name": "Earbud Micro-Battery Replacement (Dead Bud)", "price": 1299, "turnaround": "40 Mins", "warranty": "90 Days"},
                        {"id": "cushions", "name": "Cooling-Gel Ear Cushions (Pair)", "price": 899, "turnaround": "Instant", "warranty": "90 Days"},
                        {"id": "mesh-clean", "name": "Acoustic Mesh Solvent & Ultrasonic Vacuum", "price": 499, "turnaround": "20 Mins", "warranty": "90 Days"},
                        {"id": "case-port", "name": "Charging Case Battery & Lightning / USB-C Port", "price": 1499, "turnaround": "45 Mins", "warranty": "90 Days"}
                    ]
                },
                {
                    "id": "wearables",
                    "name": "Smartwatches",
                    "icon": "watch",
                    "models": [
                        "Apple Watch Ultra 1 / 2",
                        "Apple Watch Series 9 / 8 / 7 / SE",
                        "Samsung Galaxy Watch 6 / 5 Pro"
                    ],
                    "issues": [
                        {"id": "watch-glass", "name": "Sapphire / OLED Glass Touch Digitizer", "price": 3999, "turnaround": "60 Mins", "warranty": "90 Days"},
                        {"id": "watch-battery", "name": "Internal Lithium Polymer Battery Cell", "price": 1999, "turnaround": "45 Mins", "warranty": "90 Days"},
                        {"id": "sensor-flex", "name": "Heart Rate & Bio-Sensor Glass Restoration", "price": 1699, "turnaround": "60 Mins", "warranty": "90 Days"}
                    ]
                }
            ]
        }
        return jsonify(options)
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
    debug = os.getenv("FLASK_DEBUG", "true").lower() in ("true", "1", "yes")
    app.run(debug=debug, host="0.0.0.0", port=port)
