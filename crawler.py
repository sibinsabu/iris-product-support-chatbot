"""
Gadget & Electronics Repair Industry Crawler & Dataset Intelligence Engine
Integrates:
1. iFixit Live REST API (Official Repair Guides, Teardowns, Tools, Difficulty)
2. OEM Hardware Diagnostic & Fault Code Datasets (Apple, Dell ePSA, HP, Lenovo, Samsung)
3. Consumer Electronics Safety Recalls & Service Advisory Database
4. TechFix Parts & Service Catalog (Pricing in Indian Rupees ₹ INR)
5. Live Web / URL Crawler Engine with BeautifulSoup & AI Diagnostic Extraction
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional

# ==============================================================================
# 1. OEM HARDWARE DIAGNOSTIC & FAULT CODE DATASET
# ==============================================================================
DIAGNOSTIC_CODES_DATASET = [
    # Apple Diagnostic Codes (MacBook, iMac, iPhone)
    {
        "code": "PPT004",
        "oem": "Apple",
        "category": "Laptops & Mobiles",
        "devices": ["MacBook Pro", "MacBook Air", "iPhone"],
        "title": "Battery Condition Degraded / Cycle Limit Exceeded",
        "severity": "High",
        "symptom": "Battery health degraded below 80%, unexpected shutdowns, system throttling, or 'Service Recommended' alert in macOS / iOS.",
        "root_cause": "Lithium-ion cells chemical degradation, internal resistance spike, or cycle count exceeding 1000 cycles.",
        "action": "Perform full OEM battery replacement. Re-calibrate battery management controller and verify SMC charging logic.",
        "estimated_price_inr": 4999,
        "service_id": "macbook-battery-repair"
    },
    {
        "code": "PPT006",
        "oem": "Apple",
        "category": "Laptops & Mobiles",
        "devices": ["MacBook Pro", "MacBook Air"],
        "title": "Battery Swelling Hazard / Critical Failure",
        "severity": "Critical",
        "symptom": "Trackpad difficult to click, bottom aluminum case bulging, battery fails to accept charge or discharges instantly.",
        "root_cause": "Lithium pouch outgassing due to cell rupture, thermal runaway risk, or overvoltage stress.",
        "action": "Immediate disassembly in ESD safe lab. Extract swollen battery pouch using solvent dissolver. Replace with new OEM cell pack.",
        "estimated_price_inr": 4999,
        "service_id": "macbook-battery-repair"
    },
    {
        "code": "VFD001",
        "oem": "Apple",
        "category": "Laptops & Mobiles",
        "devices": ["MacBook Pro", "MacBook Air", "iPhone", "iPad"],
        "title": "Display Panel / eDP Flex Cable Fault (Flexgate)",
        "severity": "High",
        "symptom": "Screen flickers, stage light effect at bottom of display, vertical colored lines, or completely black screen when opened past 45 degrees.",
        "root_cause": "Micro-fracture in flexible display ribbon cable (Flexgate) or damaged panel digitizer.",
        "action": "Precision micro-soldering ribbon jumper extension or full OEM display assembly replacement.",
        "estimated_price_inr": 8999,
        "service_id": "laptop-screen-repair"
    },
    {
        "code": "VDC001",
        "oem": "Apple",
        "category": "Laptops",
        "devices": ["MacBook Pro", "MacBook Air"],
        "title": "FaceTime HD Camera / Sensor Disconnected",
        "severity": "Moderate",
        "symptom": "Camera indicator LED stays off, FaceTime and Photo Booth show 'No Camera Available'.",
        "root_cause": "Display lid angle sensor or T2/M-series camera bus ribbon disconnection.",
        "action": "Reseat camera flex connector under top EMI shield; replace camera module if bus lines fail continuity.",
        "estimated_price_inr": 2499,
        "service_id": "diagnostic-bench-fee"
    },
    {
        "code": "ALS001",
        "oem": "Apple",
        "category": "Laptops & Mobiles",
        "devices": ["MacBook Pro", "iPhone 13 / 14 / 15"],
        "title": "Ambient Light Sensor / True Tone Sensor Glitch",
        "severity": "Low",
        "symptom": "Automatic brightness does not adjust, True Tone toggle disabled or missing in settings.",
        "root_cause": "Front ear-speaker flex or top display sensor array damaged during screen replacement without eeprom transfer.",
        "action": "Program and serialize True Tone data from original IC chip to replacement module using EEPROM programmer.",
        "estimated_price_inr": 1499,
        "service_id": "diagnostic-bench-fee"
    },
    {
        "code": "PFM006",
        "oem": "Apple",
        "category": "Laptops",
        "devices": ["MacBook Pro", "MacBook Air", "Mac Mini"],
        "title": "SMC / Power Management Logic Controller Issue",
        "severity": "High",
        "symptom": "Fans run at maximum RPM immediately upon boot, CPU kernel_task uses 600% CPU, slow charging.",
        "root_cause": "System Management Controller sensor line failure or corroded thermal diode pull-up resistor.",
        "action": "Ultrasonic board clean for moisture corrosion; repair PPBUS_G3H or PP3V3_G3H rail short; reset SMC/NVRAM.",
        "estimated_price_inr": 2999,
        "service_id": "laptop-thermal-service"
    },

    # Dell ePSA Error Codes (Laptops, XPS, Inspiron, Latitude)
    {
        "code": "2000-0142",
        "oem": "Dell",
        "category": "Laptops",
        "devices": ["Dell XPS 13/15", "Dell Inspiron", "Dell Latitude"],
        "title": "Drive Self-Test Failed / Uncorrectable Read Error",
        "severity": "Critical",
        "symptom": "Laptop fails to boot into Windows, 'No bootable device found' or Dell ePSA diagnostic halts at hard drive test with error code 2000-0142.",
        "root_cause": "NAND flash controller failure or bad sector reallocation exhausted on NVMe SSD / SATA drive.",
        "action": "Urgent data recovery backup; replace failed drive with high-speed PCIe Gen4 NVMe M.2 SSD; reinstall fresh OS.",
        "estimated_price_inr": 3499,
        "service_id": "laptop-thermal-service"
    },
    {
        "code": "2000-0131",
        "oem": "Dell",
        "category": "Laptops",
        "devices": ["Dell XPS", "Dell Inspiron", "Dell Vostro"],
        "title": "Battery Approaching End of Usable Life",
        "severity": "Moderate",
        "symptom": "Flashing orange battery LED indicator, BIOS prompt: 'The battery is operating normally, but it has reached end of usable life'.",
        "root_cause": "Lithium pouch capacity dropped below 60% of design capacity; internal impedance too high.",
        "action": "Install OEM Dell 56Wh / 86Wh high-capacity replacement battery pack with 90-day TechFix warranty.",
        "estimated_price_inr": 3899,
        "service_id": "macbook-battery-repair"
    },
    {
        "code": "2000-0333",
        "oem": "Dell",
        "category": "Laptops",
        "devices": ["Dell XPS", "Dell Latitude", "Dell Alienware"],
        "title": "LCD Graphics Panel Line / Video Signal Failure",
        "severity": "High",
        "symptom": "Beeping code 8 or 2-7 LED amber/white blink, distorted colors, screen blank while external monitor displays fine.",
        "root_cause": "Damaged eDP display cable pinched inside 360-degree hinge, or fractured LCD panel.",
        "action": "Inspect and replace eDP ribbon harness; bench test replacement FHD/4K IPS panel.",
        "estimated_price_inr": 6499,
        "service_id": "laptop-screen-repair"
    },
    {
        "code": "2000-0511",
        "oem": "Dell",
        "category": "Laptops",
        "devices": ["Dell XPS 15", "Dell Inspiron Gaming", "Dell G15"],
        "title": "CPU / GPU Cooling Fan Did Not Respond Correctly",
        "severity": "High",
        "symptom": "Error 2000-0511 on startup, fan rattling or silent, system overheats and shuts down within 5 minutes.",
        "root_cause": "Fan bearing seized with lint dust, broken impeller fin, or blown PWM fan header fuse.",
        "action": "Ultrasonic clean heatsink fins; lubricate or replace dual hydraulic bearing fan; apply Arctic MX-6 thermal repaste.",
        "estimated_price_inr": 1299,
        "service_id": "laptop-thermal-service"
    },

    # Lenovo ThinkPad Diagnostic Beeps & Codes
    {
        "code": "5 Short Beeps",
        "oem": "Lenovo",
        "category": "Laptops",
        "devices": ["ThinkPad X1 Carbon", "ThinkPad T14", "ThinkPad E15"],
        "title": "System Motherboard / Security TPM Unit Failure",
        "severity": "Critical",
        "symptom": "Loud 5-beep sequence during power-on self-test; screen remains dark; power light pulses.",
        "root_cause": "Cryptographic security coprocessor or power sequencing MOSFET shorted on 3.3V standby rail.",
        "action": "Micro-bench multimeter power rail diagnostic, re-flash UEFI BIOS SPI chip, or motherboard repair.",
        "estimated_price_inr": 2999,
        "service_id": "diagnostic-bench-fee"
    },
    {
        "code": "1-3-3-1 Beeps",
        "oem": "Lenovo",
        "category": "Laptops",
        "devices": ["ThinkPad T-Series", "ThinkPad L-Series", "IdeaPad"],
        "title": "Memory (RAM) Module Detection / Parity Failure",
        "severity": "High",
        "symptom": "1 beep, pause, 3 beeps, pause, 3 beeps, 1 beep. Machine will not POST.",
        "root_cause": "Oxidized SO-DIMM golden contacts, unseated memory stick, or defective DDR4/DDR5 module.",
        "action": "Ultrasonic clean memory slots with 99% isopropyl alcohol; reseat or install verified DDR4/DDR5 module.",
        "estimated_price_inr": 1699,
        "service_id": "diagnostic-bench-fee"
    },

    # HP Diagnostic Blink Codes
    {
        "code": "3.2 Blinks",
        "oem": "HP",
        "category": "Laptops",
        "devices": ["HP Pavilion", "HP Envy", "HP Spectre x360", "HP EliteBook"],
        "title": "Memory Module Error / Initialization Glitch",
        "severity": "High",
        "symptom": "Caps Lock key blinks 3 slow flashes followed by 2 fast flashes, screen remains black.",
        "root_cause": "BIOS fails to initialize memory bank or soldered RAM chip has cold solder joint.",
        "action": "Reseat RAM modules in alternative bank; run BGA reflow or replace failed memory strip.",
        "estimated_price_inr": 1499,
        "service_id": "diagnostic-bench-fee"
    },
    {
        "code": "90b Fan Error",
        "oem": "HP",
        "category": "Laptops",
        "devices": ["HP Omen", "HP Pavilion", "HP Envy 15"],
        "title": "Cooling System Fan (90B) Stalled / Thermal Protection",
        "severity": "High",
        "symptom": "Screen displays: 'The system has detected that a cooling fan is not operating correctly (90B)' before shutdown.",
        "root_cause": "Foreign debris or accumulated hair obstructing blower rotor; dried thermal paste causing thermal runaway.",
        "action": "Full teardown and chamber vacuuming, heatsink wash, replace blower motor, apply thermal repaste.",
        "estimated_price_inr": 999,
        "service_id": "laptop-thermal-service"
    },

    # Samsung Secret Diagnostic Codes & Faults (Smartphones & Tablets)
    {
        "code": "*#0*#",
        "oem": "Samsung",
        "category": "Smartphones",
        "devices": ["Galaxy S21/S22/S23/S24", "Galaxy Note", "Galaxy A-Series"],
        "title": "Samsung Hardware Diagnostic Test Matrix",
        "severity": "Info",
        "symptom": "Customer testing touchscreen accuracy, dead OLED pixels, vibration motor, or ear-speaker volume.",
        "root_cause": "Service test menu to isolate hardware faults from Android software glitches.",
        "action": "Dial *#0*# in Phone app to run sub-pixel red/green/blue checks, touch grid digitizer verification, sensor check.",
        "estimated_price_inr": 299,
        "service_id": "diagnostic-bench-fee"
    },
    {
        "code": "*#0228#",
        "oem": "Samsung",
        "category": "Smartphones",
        "devices": ["Galaxy S Series", "Galaxy Z Fold/Flip", "Galaxy A Series"],
        "title": "Battery Fuel Gauge & ADC Voltage Calibration",
        "severity": "Info",
        "symptom": "Phone jumps from 30% to 5% instantly, erratic battery percentage reporting, phone dies under load.",
        "root_cause": "Battery fuel-gauge IC desynchronized from physical cell voltage curve.",
        "action": "Dial *#0228#, execute 'Quick Start' fuel gauge reset. If issue persists, install new OEM battery cell.",
        "estimated_price_inr": 1899,
        "service_id": "mobile-battery-repair"
    },

    # Audio & Earbuds Fault Diagnostics
    {
        "code": "AUDIO-UNBALANCE-01",
        "oem": "Apple & Sony",
        "category": "Earphones & Audio",
        "devices": ["AirPods 2/3", "AirPods Pro 1/2", "Sony WF-1000XM4/XM5"],
        "title": "One Earbud Quiet / Muffled Audio / No Bass",
        "severity": "Moderate",
        "symptom": "Left or right earbud is 70% quieter than the other, sounds hollow or lacks bass response.",
        "root_cause": "Acoustic mesh clogged with microscopic cerumen (earwax) or blown dynamic micro-driver diaphragm.",
        "action": "Chemical solvent acoustic mesh breakdown and ultrasonic vacuum extraction. Replace driver if coil open.",
        "estimated_price_inr": 1299,
        "service_id": "airpods-battery-fix"
    },
    {
        "code": "ANC-CRACKLE-02",
        "oem": "Apple & Bose",
        "category": "Earphones & Audio",
        "devices": ["AirPods Pro", "Bose QC Earbuds", "Sony WH-1000XM4"],
        "title": "Crackling, Static, or Popping Sounds During Movement",
        "severity": "High",
        "symptom": "Sharp clicking or wind static noises when walking, chewing, or in noisy environments with ANC enabled.",
        "root_cause": "Debris lodged in outward-facing noise cancellation microphone port, causing acoustic feedback loop.",
        "action": "Microscope inspection and acoustic port de-clogging. If transducer membrane torn, install replacement bud.",
        "estimated_price_inr": 1299,
        "service_id": "airpods-battery-fix"
    }
]

# ==============================================================================
# 2. CONSUMER SAFETY GADGET RECALLS & SERVICE PROGRAMS DATASET
# ==============================================================================
RECALLS_DATASET = [
    {
        "id": "RECALL-APL-MBP15",
        "brand": "Apple",
        "category": "Laptops",
        "device": "15-inch MacBook Pro (Retina, 15-inch, Mid 2015)",
        "title": "15-inch MacBook Pro Battery Recall Program",
        "agency": "CPSC / Apple Official Recall",
        "risk_level": "Severe (Fire & Thermal Runaway)",
        "defect_summary": "Affected units contain a defective lithium-ion battery cell that may overheat and pose a severe fire safety risk.",
        "affected_period": "Sold primarily between September 2015 and February 2017.",
        "remedy": "Stop using device immediately. Free battery replacement program or TechFix certified cell swap.",
        "verification_method": "Check serial number in Apple Menu > About This Mac > Serial Number."
    },
    {
        "id": "RECALL-APL-IPH11",
        "brand": "Apple",
        "category": "Smartphones",
        "device": "iPhone 11",
        "title": "iPhone 11 Display Module Replacement Program for Touch Issues",
        "agency": "Apple Quality Service Bulletin",
        "risk_level": "Moderate (Hardware Unresponsive)",
        "defect_summary": "A small percentage of iPhone 11 displays may stop responding to touch due to an issue with the display driver IC module.",
        "affected_period": "Manufactured between November 2019 and May 2020.",
        "remedy": "Display digitizer module replacement with OEM high-refresh panel.",
        "verification_method": "Enter IMEI/Serial number on Apple Service or inspect via TechFix diagnostic bench."
    },
    {
        "id": "RECALL-APL-APP1",
        "brand": "Apple",
        "category": "Earphones & Audio",
        "device": "AirPods Pro (1st Generation)",
        "title": "AirPods Pro Service Program for Sound Issues",
        "agency": "Apple Quality Program",
        "risk_level": "Moderate (Audio Distortion)",
        "defect_summary": "Affected units experience crackling or static sounds that increase in loud environments or while exercising; Active Noise Cancellation loses bass or increases background sounds.",
        "affected_period": "Manufactured before October 2020.",
        "remedy": "Acoustic mesh clearing or replacement of affected left/right earbud units.",
        "verification_method": "Audio frequency sweep test at TechFix Lab."
    },
    {
        "id": "RECALL-SAM-NOTE7",
        "brand": "Samsung",
        "category": "Smartphones",
        "device": "Samsung Galaxy Note 7",
        "title": "Samsung Galaxy Note 7 Battery Thermal Safety Recall",
        "agency": "CPSC Recall #16-266",
        "risk_level": "Critical (Fire & Explosion Hazard)",
        "defect_summary": "Internal battery separator damage causing cathode-to-anode short circuit, leading to severe thermal expansion and fire.",
        "affected_period": "All models sold in 2016.",
        "remedy": "Mandatory full device return or permanent lithium battery removal.",
        "verification_method": "Model number SM-N930."
    },
    {
        "id": "RECALL-DELL-XPS-SW",
        "brand": "Dell",
        "category": "Laptops",
        "device": "Dell XPS 15 (9550 / 9560) & XPS 13",
        "title": "Dell XPS Swollen Battery & Trackpad Bulge Service Advisory",
        "agency": "Dell Service Advisory",
        "risk_level": "High (Pouch Swelling)",
        "defect_summary": "High cycle degradation in thin lithium-polymer pouch causes expansion, pushing against the glass precision trackpad and bottom chassis.",
        "affected_period": "Dell XPS 9550/9560 series under extended heavy thermal load.",
        "remedy": "Disconnect AC power immediately, remove battery safely, install new OEM 86Wh battery.",
        "verification_method": "Physical inspection of trackpad click travel and bottom lid gap."
    },
    {
        "id": "RECALL-HP-BAT-2019",
        "brand": "HP",
        "category": "Laptops",
        "device": "HP ProBook, HP Envy, HP Pavilion, HP ZBook",
        "title": "HP Worldwide Voluntary Battery Safety Recall",
        "agency": "CPSC Recall #18-085 / HP Support",
        "risk_level": "Severe (Fire / Burn Hazard)",
        "defect_summary": "Certain lithium-ion internal battery packs supplied with HP commercial notebooks pose a risk of overheating, fire, and burns.",
        "affected_period": "Shipped between December 2015 and April 2018.",
        "remedy": "Activate HP Battery Safety Mode via BIOS update, replace battery pack with genuine unit.",
        "verification_method": "Run HP Battery Check utility or inspect CT battery barcode."
    }
]

# ==============================================================================
# 3. TECHFIX REPAIR CATALOG & PARTS PRICING DATASET (INR ₹)
# ==============================================================================
TECHFIX_PARTS_CATALOG = [
    {
        "id": "iphone-back-glass-repair",
        "name": "iPhone Back Glass Laser Removal & Replacement",
        "category": "Mobile Repair",
        "device_category": "Smartphones",
        "models": "iPhone 12, 13, 14, 15, 16 Series (Standard, Pro, Pro Max)",
        "price_inr": 2499,
        "turnaround": "45 Mins Walk-in or Express Mail-In",
        "warranty": "90-Day TechFix Guarantee",
        "in_stock": True,
        "difficulty": "Moderate",
        "tools_required": ["Specialized Fiber Laser Machine", "Suction Clamp", "ESD Tweezers", "UV Optical Adhesive", "Clamping Mold"],
        "desc": "Precision fiber-laser ablation of shattered rear back glass followed by OEM-grade tempered back glass installation."
    },
    {
        "id": "iphone-screen-repair",
        "name": "iPhone OLED Screen & Digitizer Assembly",
        "category": "Mobile Screen",
        "device_category": "Smartphones",
        "models": "iPhone X, 11, 12, 13, 14, 15 Series",
        "price_inr": 4999,
        "turnaround": "30 Mins Walk-in",
        "warranty": "90-Day TechFix Guarantee",
        "in_stock": True,
        "difficulty": "Easy to Moderate",
        "tools_required": ["Pentalobe P2 Screwdriver", "iOpener Heat Pad", "Precision Suction Handle", "Spudger", "Tri-point Y000"],
        "desc": "OEM-spec Super Retina XDR OLED panel with True Tone serialized programming and water-resistant perimeter adhesive gasket."
    },
    {
        "id": "mobile-battery-repair",
        "name": "Mobile OEM Battery Replacement (100% Health)",
        "category": "Mobile Battery",
        "device_category": "Smartphones",
        "models": "iPhone, Samsung Galaxy, Google Pixel, OnePlus",
        "price_inr": 1899,
        "turnaround": "30 Mins",
        "warranty": "90-Day Guarantee",
        "in_stock": True,
        "difficulty": "Moderate",
        "tools_required": ["Battery Adhesive Pull Tabs", "Plastic Spudger", "99% Isopropyl Alcohol", "Digital Battery Calibrator"],
        "desc": "Grade-A zero-cycle high-density lithium polymer battery cell restoring original peak battery runtime and health."
    },
    {
        "id": "laptop-screen-repair",
        "name": "MacBook / Laptop Screen & Display Assembly",
        "category": "Laptop Screen",
        "device_category": "Laptops",
        "models": "MacBook Pro/Air M1/M2/M3, Dell XPS, Lenovo ThinkPad, HP Spectre",
        "price_inr": 8999,
        "turnaround": "2-3 Hours",
        "warranty": "90-Day Guarantee",
        "in_stock": True,
        "difficulty": "Difficult",
        "tools_required": ["Torx T3/T5/T8 Screwdrivers", "Plastic Opening Picks", "Heat Gun", "Display Cable Guide"],
        "desc": "Complete clamshell assembly replacement with pre-calibrated backlight, True Tone sensor array, and high-res IPS/OLED panel."
    },
    {
        "id": "macbook-battery-repair",
        "name": "MacBook Pro / Air High-Capacity Battery Pack",
        "category": "Laptop Service",
        "device_category": "Laptops",
        "models": "MacBook Pro 13/14/15/16-inch, MacBook Air M1/M2/Intel",
        "price_inr": 4999,
        "turnaround": "60 Mins",
        "warranty": "90-Day Guarantee",
        "in_stock": True,
        "difficulty": "Moderate to Difficult",
        "tools_required": ["P5 Pentalobe", "T5 Torx", "Battery Dissolver Fluid", "Nylon Thread Extraction String"],
        "desc": "OEM-tier multi-cell battery pack bonded with factory thermal isolation tape, tested for zero cycle count."
    },
    {
        "id": "laptop-thermal-service",
        "name": "Laptop Deep Thermal Cleaning & Fan Service",
        "category": "Laptop Maintenance",
        "device_category": "Laptops",
        "models": "Dell, HP, Lenovo, Asus ROG, Acer, MacBook",
        "price_inr": 999,
        "turnaround": "45 Mins",
        "warranty": "90-Day Guarantee",
        "in_stock": True,
        "difficulty": "Easy to Moderate",
        "tools_required": ["Precision Phillips #00", "Anti-Static Brush", "Thermal Grizzly Kryonaut Repaste", "High-Pressure Blower"],
        "desc": "Complete heatsink and dual-fan de-linting, heatsink contact polishing, and high-performance thermal paste application."
    },
    {
        "id": "airpods-battery-fix",
        "name": "AirPods / Earbuds Battery & Audio Restoration",
        "category": "Audio Service",
        "device_category": "Earphones & Audio",
        "models": "AirPods 1/2/3, AirPods Pro 1/2, Galaxy Buds, Sony WF-1000XM4/XM5",
        "price_inr": 1299,
        "turnaround": "45 Mins",
        "warranty": "90-Day Guarantee",
        "in_stock": True,
        "difficulty": "Difficult (Microsoldering)",
        "tools_required": ["Hot Air Rework Station (160°C)", "Microscopic Tweezers", "Micro-soldering Iron", "B-7000 Precision Sealant"],
        "desc": "Micro-soldering new CP1254 / button-cell battery, ultrasonic acoustic wax mesh cleaning, and sound balance calibration."
    },
    {
        "id": "ear-cushions-pair",
        "name": "Apex / Sony Pro Cooling-Gel Ear Cushions (Pair)",
        "category": "Audio Accessories",
        "device_category": "Earphones & Audio",
        "models": "Sony WH-1000XM3/XM4/XM5, Bose QuietComfort 35/45, AirPods Max, Beats Studio",
        "price_inr": 899,
        "turnaround": "15 Mins Walk-in",
        "warranty": "90-Day Guarantee",
        "in_stock": True,
        "difficulty": "Easy",
        "tools_required": ["Flat Plastic Pry Tool"],
        "desc": "Ergonomic cooling-gel infused high-density memory foam ear cushions with breathable protein leather."
    },
    {
        "id": "port-repair-service",
        "name": "USB-C / Lightning Port Cleaning & Pin Repair",
        "category": "Hardware Repair",
        "device_category": "Smartphones & Laptops",
        "models": "All Smart Devices, iPhone, iPad, MacBooks, Android",
        "price_inr": 699,
        "turnaround": "30 Mins",
        "warranty": "90-Day Guarantee",
        "in_stock": True,
        "difficulty": "Easy to Moderate",
        "tools_required": ["Microscope", "Conductive Pin Probe", "DeoxIT Contact Cleaner", "Mini ESD Vacuum"],
        "desc": "High-magnification microscopic lint and oxidation extraction, bent pin realignment, or port modular replacement."
    },
    {
        "id": "diagnostic-bench-fee",
        "name": "Full Diagnostic Bench Inspection & Water Damage Clean",
        "category": "Diagnostic Service",
        "device_category": "All Devices",
        "models": "All Mobiles, Laptops, Earbuds, Smartwatches",
        "price_inr": 299,
        "turnaround": "60 Mins",
        "warranty": "90-Day Guarantee",
        "in_stock": True,
        "difficulty": "Moderate",
        "tools_required": ["Ultrasonic Bath", "99.9% Pure Isopropanol", "Fluke Digital Multimeter", "Thermal Imaging Camera"],
        "desc": "Comprehensive power rail voltage drop diagnostic, short-circuit locator, ultrasonic bath corrosion cleaning."
    }
]

# ==============================================================================
# 4. IFIXIT LIVE API INTEGRATION
# ==============================================================================
def search_ifixit_guides(query: str, limit: int = 6) -> List[Dict[str, Any]]:
    """
    Query official iFixit REST API 2.0 for live gadget repair guides, teardowns, and difficulty.
    """
    clean_query = query.strip()
    if not clean_query:
        return []

    url = f"https://www.ifixit.com/api/2.0/search/{requests.utils.quote(clean_query)}?filter=guide&limit={limit}"
    headers = {
        "User-Agent": "TechFixRepairCrawler/1.0 (Electronics Repair Diagnostic Platform; +support@techfix.local)"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            raw_results = data.get("results", [])
            formatted = []
            for item in raw_results[:limit]:
                # Extract best image
                img_obj = item.get("image") or {}
                image_url = (
                    img_obj.get("standard")
                    or img_obj.get("medium")
                    or img_obj.get("thumbnail")
                    or "https://assets.ifixit.com/static/images/ifixit/guide/guide_placeholder.png"
                )
                formatted.append({
                    "source": "iFixit Official Database",
                    "guideid": item.get("guideid"),
                    "title": item.get("title") or item.get("display_title") or "Repair Guide",
                    "category": item.get("category", "Electronics Repair"),
                    "subject": item.get("subject", ""),
                    "summary": item.get("summary") or item.get("text") or "Official iFixit community repair guide and teardown steps.",
                    "url": item.get("url") or f"https://www.ifixit.com/Guide/{item.get('guideid')}",
                    "difficulty": item.get("difficulty", "Moderate"),
                    "time_required": item.get("time_required_max") or "30-60 mins",
                    "image": image_url
                })
            return formatted
    except Exception as e:
        print(f"[iFixit API Warning] {e}")

    # Fallback search within cached common iFixit guides if network is down
    return get_cached_ifixit_fallback(clean_query, limit)


def get_cached_ifixit_fallback(query: str, limit: int = 4) -> List[Dict[str, Any]]:
    """
    High-fidelity offline fallback cache of popular iFixit repair guides.
    """
    sample_guides = [
        {
            "source": "iFixit Official Database",
            "guideid": 160340,
            "title": "iPhone 13 / 14 / 15 Screen Replacement",
            "category": "Phone",
            "subject": "Screen",
            "summary": "Step-by-step instructions to replace a cracked OLED display assembly, transfer sensors, and re-apply water-resistant seal.",
            "url": "https://www.ifixit.com/Guide/iPhone+13+Screen+Replacement/145899",
            "difficulty": "Moderate",
            "time_required": "45 - 60 minutes",
            "image": "https://guide-images.cdn.ifixit.com/igi/2FYrBQaFhhADVVAq.standard"
        },
        {
            "source": "iFixit Official Database",
            "guideid": 145901,
            "title": "iPhone Battery Replacement (OEM Cell)",
            "category": "Phone",
            "subject": "Battery",
            "summary": "Safe removal of stretched battery pull tabs, extraction of aged lithium pouch, and installation of fresh battery.",
            "url": "https://www.ifixit.com/Guide/iPhone+Battery+Replacement",
            "difficulty": "Moderate",
            "time_required": "30 - 45 minutes",
            "image": "https://guide-images.cdn.ifixit.com/igi/Wf5rELsuTPFYibSK.standard"
        },
        {
            "source": "iFixit Official Database",
            "guideid": 140292,
            "title": "MacBook Pro Retina Display & Hinge Assembly Replacement",
            "category": "MacBook",
            "subject": "Display",
            "summary": "Disassembly of bottom chassis, disconnect battery data cable, unroute antenna wires, and unbolt T8 torx display hinges.",
            "url": "https://www.ifixit.com/Device/MacBook_Pro",
            "difficulty": "Difficult",
            "time_required": "1 - 2 hours",
            "image": "https://guide-images.cdn.ifixit.com/igi/2FYrBQaFhhADVVAq.standard"
        },
        {
            "source": "iFixit Official Database",
            "guideid": 128490,
            "title": "AirPods / AirPods Pro Battery Teardown & Inspection",
            "category": "Audio",
            "subject": "Earbuds",
            "summary": "Delicate heat-based opening of earbud hermetic shell, desoldering button-cell battery leads, and transducer testing.",
            "url": "https://www.ifixit.com/Device/AirPods",
            "difficulty": "Very Difficult",
            "time_required": "60 minutes",
            "image": "https://guide-images.cdn.ifixit.com/igi/Wf5rELsuTPFYibSK.standard"
        }
    ]
    tokens = set(re.findall(r"\w+", query.lower()))
    matches = []
    for g in sample_guides:
        text = f"{g['title']} {g['category']} {g['subject']} {g['summary']}".lower()
        if any(tok in text for tok in tokens):
            matches.append(g)
    return matches[:limit] or sample_guides[:limit]


# ==============================================================================
# 5. LIVE WEB / URL CRAWLER ENGINE (BeautifulSoup + AI Synthesizer)
# ==============================================================================
def crawl_web_url(url: str, ai_client=None, text_model: str = "") -> Dict[str, Any]:
    """
    Crawls an external gadget repair webpage, forum thread, or documentation page,
    extracts key content using BeautifulSoup, and utilizes the Azure OpenAI text model
    to synthesize actionable diagnostic and repair insights.
    """
    clean_url = url.strip()
    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36 TechFixCrawler/1.0"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        resp = requests.get(clean_url, headers=headers, timeout=10)
        status_code = resp.status_code
        content_type = resp.headers.get("Content-Type", "")

        if status_code >= 400:
            return {
                "success": False,
                "url": clean_url,
                "error": f"Target server returned HTTP {status_code}"
            }

        # Parse with BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")

        # Strip scripts, styles, iframes, SVGs
        for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav", "iframe"]):
            tag.decompose()

        # Extract title & headings
        page_title = soup.title.string.strip() if soup.title and soup.title.string else clean_url
        headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])[:8]]

        # Extract main text
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 25]
        body_text = "\n".join(paragraphs[:20])

        if not body_text:
            body_text = soup.get_text(separator=" ", strip=True)[:3000]
        else:
            body_text = body_text[:3000]

        result = {
            "success": True,
            "url": clean_url,
            "status_code": status_code,
            "title": page_title,
            "headings": headings,
            "raw_snippet": body_text[:600] + "..." if len(body_text) > 600 else body_text,
            "content_length": len(body_text),
            "ai_synthesis": None
        }

        # If Azure OpenAI client is available, synthesize actionable repair knowledge
        if ai_client and text_model and len(body_text) > 40:
            try:
                extraction_prompt = f"""You are "Iris", AI Master Diagnostic Technician for TechFix. We have crawled the following electronics repair documentation / forum thread / guide:
URL: {clean_url}
TITLE: {page_title}
CONTENT:
{body_text[:2500]}

Extract and synthesize these exact 5 structured items:
1. Target Device & Symptom: (Identify device make/model and failure symptom)
2. Verified Hardware Diagnosis: (Root cause, faulty IC, ribbon, or component)
3. Step-by-Step Repair Action Plan: (Numbered concise instructions)
4. Recommended Tools & Safety Warnings: (Crucial ESD, heat, or battery warnings)
5. TechFix Lab Repair Recommendation & Pricing: (Quote estimated repair cost in Indian Rupees ₹ INR)."""

                ai_resp = ai_client.responses.create(
                    model=text_model,
                    instructions="You are Iris, AI Diagnostic Engineer for TechFix. Quote all repair prices in Indian Rupees (₹ / INR). Provide clean, professional Markdown.",
                    input=extraction_prompt
                )
                result["ai_synthesis"] = ai_resp.output_text
            except Exception as ai_err:
                result["ai_synthesis_error"] = str(ai_err)

        return result

    except Exception as e:
        return {
            "success": False,
            "url": clean_url,
            "error": str(e)
        }


# ==============================================================================
# 6. FEDERATED SEARCH & DATASET QUERY ENGINE
# ==============================================================================
def search_diagnostic_codes(query: str) -> List[Dict[str, Any]]:
    """
    Search OEM Diagnostic & Hardware Error Codes dataset by code, OEM, symptom, or device.
    """
    q = query.lower().strip()
    if not q:
        return DIAGNOSTIC_CODES_DATASET[:6]

    tokens = [t for t in re.findall(r"[\w\*\#\-]+", q) if len(t) > 1]
    results = []

    for item in DIAGNOSTIC_CODES_DATASET:
        searchable = " ".join([
            item["code"],
            item["oem"],
            item["category"],
            " ".join(item["devices"]),
            item["title"],
            item["symptom"],
            item["root_cause"],
            item["action"]
        ]).lower()

        # Check exact code match first
        if item["code"].lower() in q or q in item["code"].lower():
            results.append((item, 100))
            continue

        score = sum(1 for tok in tokens if tok in searchable)
        if score > 0:
            results.append((item, score))

    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in results]


def search_recalls(query: str) -> List[Dict[str, Any]]:
    """
    Search official gadget safety recalls & quality service programs.
    """
    q = query.lower().strip()
    if not q:
        return RECALLS_DATASET[:4]

    tokens = [t for t in re.findall(r"\w+", q) if len(t) > 1]
    results = []

    for item in RECALLS_DATASET:
        searchable = " ".join([
            item["id"],
            item["brand"],
            item["category"],
            item["device"],
            item["title"],
            item["agency"],
            item["defect_summary"],
            item["remedy"]
        ]).lower()

        score = sum(1 for tok in tokens if tok in searchable)
        if score > 0 or not tokens:
            results.append((item, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in results]


def search_parts_catalog(query: str) -> List[Dict[str, Any]]:
    """
    Search TechFix replacement parts & service catalog with pricing in INR (₹).
    """
    q = query.lower().strip()
    if not q:
        return TECHFIX_PARTS_CATALOG[:6]

    tokens = [t for t in re.findall(r"\w+", q) if len(t) > 1]
    results = []

    for item in TECHFIX_PARTS_CATALOG:
        searchable = " ".join([
            item["name"],
            item["category"],
            item["device_category"],
            item["models"],
            item["desc"],
            " ".join(item.get("tools_required", []))
        ]).lower()

        score = sum(1 for tok in tokens if tok in searchable)
        if score > 0:
            results.append((item, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in results]


def federated_crawl(
    query: str = "",
    mode: str = "all",
    url: Optional[str] = None,
    category_filter: str = "all",
    ai_client=None,
    text_model: str = ""
) -> Dict[str, Any]:
    """
    Unified federated crawl across:
    - iFixit Live API
    - OEM Hardware Diagnostic Codes
    - Gadget Safety Recalls & Bulletins
    - TechFix Parts & Pricing Catalog (INR ₹)
    - Optional Live Web Scraper
    - Synthesizes findings with AI.
    """
    output = {
        "query": query,
        "mode": mode,
        "category_filter": category_filter,
        "datasets_connected": [
            {"id": "ifixit", "name": "iFixit Open Repair API (v2.0)", "status": "online", "type": "Live REST API"},
            {"id": "diagnostic_codes", "name": "OEM Hardware Diagnostic Codes (Apple, Dell, HP, Lenovo, Samsung)", "status": "loaded", "type": "Structured Diagnostic Matrix"},
            {"id": "recalls", "name": "Safety Recalls & Bulletins (CPSC, EU Safety, Apple, Dell)", "status": "loaded", "type": "Consumer Safety Database"},
            {"id": "catalog", "name": "TechFix Parts & Pricing Index (₹ INR)", "status": "active", "type": "Commercial Catalog"}
        ],
        "ifixit_guides": [],
        "diagnostic_codes": [],
        "recalls": [],
        "parts_catalog": [],
        "web_crawl_result": None,
        "ai_synthesis": None,
        "stats": {
            "total_records_found": 0,
            "ifixit_count": 0,
            "diagnostic_count": 0,
            "recall_count": 0,
            "catalog_count": 0
        }
    }

    # 1. Live Web Crawl if URL provided or mode is 'web_url'
    if url or mode == "web_url":
        target_url = url or query
        if target_url and target_url.startswith(("http://", "https://", "www.")):
            output["web_crawl_result"] = crawl_web_url(target_url, ai_client, text_model)
            if mode == "web_url":
                return output

    search_query = query.strip()
    if not search_query and url:
        search_query = output.get("web_crawl_result", {}).get("title", "")

    # If query is still empty, provide general top items
    active_q = search_query or "smartphone laptop repair"

    # 2. iFixit Live API
    if mode in ("all", "ifixit"):
        guides = search_ifixit_guides(active_q, limit=6)
        output["ifixit_guides"] = guides
        output["stats"]["ifixit_count"] = len(guides)

    # 3. Diagnostic Codes
    if mode in ("all", "diagnostic_codes"):
        diag_matches = search_diagnostic_codes(active_q)
        if category_filter != "all":
            diag_matches = [
                d for d in diag_matches
                if category_filter.lower() in d["category"].lower()
                or category_filter.lower() in " ".join(d["devices"]).lower()
            ]
        output["diagnostic_codes"] = diag_matches[:8]
        output["stats"]["diagnostic_count"] = len(output["diagnostic_codes"])

    # 4. Safety Recalls
    if mode in ("all", "recalls"):
        recall_matches = search_recalls(active_q)
        if category_filter != "all":
            recall_matches = [
                r for r in recall_matches
                if category_filter.lower() in r["category"].lower()
                or category_filter.lower() in r["device"].lower()
            ]
        output["recalls"] = recall_matches[:6]
        output["stats"]["recall_count"] = len(output["recalls"])

    # 5. TechFix Parts Catalog
    if mode in ("all", "catalog"):
        catalog_matches = search_parts_catalog(active_q)
        if category_filter != "all":
            catalog_matches = [
                c for c in catalog_matches
                if category_filter.lower() in c["device_category"].lower()
                or category_filter.lower() in c["category"].lower()
            ]
        output["parts_catalog"] = catalog_matches[:8]
        output["stats"]["catalog_count"] = len(output["parts_catalog"])

    output["stats"]["total_records_found"] = (
        output["stats"]["ifixit_count"] +
        output["stats"]["diagnostic_count"] +
        output["stats"]["recall_count"] +
        output["stats"]["catalog_count"]
    )

    # 6. AI Master Synthesis across all collected dataset entries
    if ai_client and text_model and (output["stats"]["total_records_found"] > 0 or output["web_crawl_result"]):
        try:
            # Build high-density context summary
            context_snippets = []

            if output["web_crawl_result"] and output["web_crawl_result"].get("raw_snippet"):
                context_snippets.append(f"WEBPAGE SNIPPET: {output['web_crawl_result']['raw_snippet'][:600]}")

            if output["diagnostic_codes"]:
                top_code = output["diagnostic_codes"][0]
                context_snippets.append(
                    f"DIAGNOSTIC CODE MATCH: {top_code['oem']} {top_code['code']} - {top_code['title']}. "
                    f"Symptom: {top_code['symptom']}. Fix: {top_code['action']}."
                )

            if output["recalls"]:
                top_recall = output["recalls"][0]
                context_snippets.append(
                    f"SAFETY RECALL ALERT: {top_recall['device']} - {top_recall['title']} ({top_recall['risk_level']})."
                )

            if output["ifixit_guides"]:
                top_guide = output["ifixit_guides"][0]
                context_snippets.append(
                    f"IFIXIT REPAIR GUIDE: {top_guide['title']} (Difficulty: {top_guide['difficulty']}, Time: {top_guide['time_required']})."
                )

            if output["parts_catalog"]:
                top_part = output["parts_catalog"][0]
                context_snippets.append(
                    f"TECHFIX REPAIR PART: {top_part['name']} - ₹{top_part['price_inr']} (Turnaround: {top_part['turnaround']})."
                )

            synthesis_prompt = f"""The technician searched for: "{active_q}".
Here are the cross-referenced findings from our electronics repair datasets:
{chr(10).join(context_snippets)}

Provide a concise, expert 3-paragraph diagnostic summary:
1. Root Cause & Fault Classification: (Clearly explain why this failure occurs).
2. Recommended Repair Protocol & Feasibility: (Step-by-step resolution, required precision tools, difficulty rating).
3. Estimated Repair Costs & Warranty: (Quote parts & service pricing in Indian Rupees ₹ INR and reference TechFix 90-day warranty)."""

            synth_res = ai_client.responses.create(
                model=text_model,
                instructions="You are Iris, Master Diagnostic Advisor for TechFix. Quote all prices in Indian Rupees (₹ / INR). Format in clean Markdown.",
                input=synthesis_prompt
            )
            output["ai_synthesis"] = synth_res.output_text
        except Exception as e:
            output["ai_synthesis_error"] = str(e)

    return output
