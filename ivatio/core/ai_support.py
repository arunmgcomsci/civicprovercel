"""
CivicPro AI Support Executive Engine
Intelligent, context-aware customer support assistant tailored specifically
for the CivicPro daily-wage worker and employer ecosystem.
"""

import os
import re
import json
import urllib.request
import urllib.parse
from django.conf import settings


SYSTEM_PROMPT = """You are Maya, the friendly, professional, and knowledgeable AI Support Executive for CivicPro.
CivicPro is a transparent, zero-commission daily-wage worker hiring platform that connects employers directly with skilled local workers (electricians, plumbers, carpenters, painters, masons, welders, helpers, drivers, gardeners, cleaners).
Your goal is to assist workers, employers, and visitors with hiring, profile setup, daily rates, emergency SOS services, and platform guidelines.
Always speak warmly, concisely, and provide clear step-by-step instructions. Where appropriate, refer to specific platform features.
"""


def detect_intent(message_lower):
    """
    Identifies the primary user intent from their query.
    """
    if re.search(r'\b(emergency|sos|ambulance|police|fire|accident|danger|hazard|panic|hospital)\b', message_lower):
        return 'emergency'

    if re.search(r'\b(human|agent|executive|person|manager|admin|call me|talk to someone|complaint|dispute|fraud|cheat|scam)\b', message_lower):
        return 'escalation'

    if re.search(r'\b(hire|find worker|search|looking for|electrician|plumber|carpenter|painter|mason|welder|driver|cleaner|helper|labor|labour|maid)\b', message_lower):
        return 'hire_search'

    if re.search(r'\b(register|sign up|join|become worker|create profile|account setup|be a worker|as worker)\b', message_lower):
        return 'worker_register'

    if re.search(r'\b(rate|wage|salary|charge|pay|payment|price|money|fee|commission|cash|upi|how much)\b', message_lower):
        return 'payment_rates'

    if re.search(r'\b(available|busy|toggle|status|working hours|offline|online)\b', message_lower):
        return 'worker_availability'

    if re.search(r'\b(verify|verified|badge|trust|id proof|document|kyc)\b', message_lower):
        return 'verification'

    if re.search(r'\b(review|rating|feedback|star|complain about worker|rate worker)\b', message_lower):
        return 'reviews'

    if re.search(r'\b(login|password|forgot|cant login|sign in|logout)\b', message_lower):
        return 'auth_trouble'

    if re.search(r'\b(location|map|gps|pin|not showing|distance|area|city|km)\b', message_lower):
        return 'location_map'

    if re.search(r'\b(hello|hi|hey|good morning|good evening|good afternoon|namaste|vanakkam|hai)\b', message_lower):
        return 'greeting'

    if re.search(r'\b(thank|thanks|great|helpful|awesome|good job|ok|okay)\b', message_lower):
        return 'gratitude'

    return 'general'


def get_user_context(user):
    """
    Extracts relevant profile context for a logged-in user.
    """
    if not user or not user.is_authenticated:
        return {
            'authenticated': False,
            'role': 'GUEST',
            'name': 'Visitor',
            'details': 'Unauthenticated guest browsing the site'
        }

    try:
        profile = user.profile
        name = user.get_full_name() or user.username
        role = profile.role
        skill = profile.get_skill_category_display() if profile.skill_category else None
        rate = profile.daily_rate
        is_avail = profile.is_available
        verified = profile.is_verified
        location = profile.location_name or "Location not set"

        return {
            'authenticated': True,
            'user_id': user.id,
            'role': role,
            'name': name,
            'skill': skill,
            'rate': rate,
            'is_available': is_avail,
            'is_verified': verified,
            'location': location,
            'details': f"Logged in as {role} ({name}), location: {location}"
        }
    except Exception:
        return {
            'authenticated': True,
            'role': 'USER',
            'name': user.username,
            'details': f"Logged in as {user.username}"
        }


def generate_rule_based_response(intent, message, user_ctx):
    """
    Generates rich, intelligent, and context-tailored responses.
    """
    name = user_ctx.get('name', 'Friend')
    role = user_ctx.get('role', 'GUEST')
    authenticated = user_ctx.get('authenticated', False)

    if intent == 'emergency':
        reply = (
            f"🚨 **Emergency & Safety Services on CivicPro**\n\n"
            f"If you or someone on your work site is in immediate danger, use our **Emergency SOS System** right away:\n\n"
            f"• **Instant SOS Access:** Visit the [Emergency Services Page](/emergency/) to trigger alerts for Medical/Ambulance (108), Police (112), or Fire Force (101).\n"
            f"• **Live Broadcast:** Triggering an alert immediately alerts your connected employer or worker with your exact location and medical details.\n"
            f"• **National Emergency Numbers:**\n"
            f"  - 🚑 **Ambulance:** Dial **108** or **102**\n"
            f"  - 👮 **Police:** Dial **112** or **100**\n"
            f"  - 🚒 **Fire Force:** Dial **101**\n\n"
            f"Please stay calm and ensure your physical safety first."
        )
        chips = ["🚨 Open Emergency SOS", "📞 Emergency Numbers", "📋 Safety Guidelines", "💬 Speak with Admin"]
        return reply, chips, False, "Emergency Assistance"

    if intent == 'escalation':
        reply = (
            f"🤝 **Connecting You with a Human Administrator**\n\n"
            f"I understand you would like direct human support, {name}. I have marked this conversation as **Escalated** for our CivicPro Administrative Team.\n\n"
            f"• **Ticket Status:** Escalated to Human Admin (Open)\n"
            f"• **Support Team Email:** support@civicpro.in\n"
            f"• **Working Hours:** Mon - Sat, 9:00 AM – 7:00 PM IST\n\n"
            f"Our team regularly reviews escalated conversations directly in the admin console. Please feel free to type any specific details about your issue or concern below so we can address it promptly."
        )
        chips = ["📝 Add Ticket Details", "🔍 Find Workers", "🛠️ Worker Profile Help", "📞 Platform Contact"]
        return reply, chips, True, "Escalated to Human Admin"

    if intent == 'hire_search':
        if not authenticated:
            reply = (
                f"👷 **Finding & Hiring Skilled Workers**\n\n"
                f"CivicPro connects you directly with skilled daily-wage professionals in your neighborhood without any middlemen!\n\n"
                f"**How to search and hire:**\n"
                f"1. **Log In / Register:** To protect worker contacts, you need an account. [Log in here](/login/) or [Register as an Employer](/register/employer/).\n"
                f"2. **Open Worker Search:** Navigate to [Find Workers](/search/).\n"
                f"3. **Filter by Skill & Distance:** Choose from Electricians, Plumbers, Carpenters, Painters, Masons, Welders, Drivers, Cleaners, and Helpers.\n"
                f"4. **View Profiles & Hire:** Check daily rates, experience, verified badges, and reviews. Click **Hire Worker** to send your job date and requirements."
            )
            chips = ["🔑 Log In to Search", "📝 Register as Employer", "💰 How Payments Work", "⭐ Worker Reviews"]
        else:
            reply = (
                f"👷 **Finding & Hiring Skilled Workers**\n\n"
                f"Hello {name}! You can browse active professionals right now on our live interactive map:\n\n"
                f"• **Search Workers Now:** Go to the [Worker Search Directory](/search/).\n"
                f"• **Filter by Radius:** Adjust your search radius (up to 50 km) to find workers closest to your location.\n"
                f"• **Categories Available:** ⚡ Electrician, 🔧 Plumber, 🪚 Carpenter, 🖌️ Painter, 🧱 Mason, 🔥 Welder, 🚗 Driver, 🧹 Cleaner, 👷 Helper.\n"
                f"• **Sending Requests:** Click on any worker profile to review their daily rate and click **Send Hire Request**."
            )
            chips = ["🔍 Open Worker Search", "📋 My Hire Dashboard", "💰 Daily Wage Guidelines", "⭐ How Reviews Work"]
        return reply, chips, False, "Hiring Workers"

    if intent == 'worker_register':
        reply = (
            f"🛠️ **Joining CivicPro as a Skilled Worker**\n\n"
            f"Welcome! CivicPro is designed to empower skilled daily-wage workers with direct job opportunities and fair wages:\n\n"
            f"1. **Register:** Create your account at [Register as Worker](/register/worker/).\n"
            f"2. **Set Up Profile:** Visit [Worker Profile Setup](/worker/profile/setup/) to choose your trade (Electrician, Plumber, Mason, etc.), experience years, and your own **daily rate (₹)**.\n"
            f"3. **Set Your Location:** Enter your city or area so nearby employers can locate you on the map.\n"
            f"4. **Toggle Availability:** On your [Worker Dashboard](/worker/dashboard/), easily switch between **Available** and **Busy** anytime!"
        )
        chips = ["📝 Register as Worker", "⚙️ Profile Setup", "💰 Setting Daily Rates", "✓ Getting Verified"]
        return reply, chips, False, "Worker Onboarding"

    if intent == 'payment_rates':
        reply = (
            f"💰 **Daily Rates & Direct Payment Policy**\n\n"
            f"CivicPro follows a **100% Transparent, Zero-Commission** philosophy:\n\n"
            f"• **Direct Worker Rates:** Every worker sets their own transparent daily wage rate based on their skill and experience.\n"
            f"• **Zero Platform Cut:** CivicPro does NOT take cuts or commissions from worker wages.\n"
            f"• **Direct Payment:** Employers pay workers directly upon completion of the day's work (via Cash, UPI, or Bank Transfer).\n"
            f"• **Status Completion:** When work concludes, the employer marks the request as **Completed** on their dashboard, which enables ratings and reviews."
        )
        chips = ["🔍 Find Workers", "📋 Employer Dashboard", "👷 Worker Dashboard", "❓ Other Questions"]
        return reply, chips, False, "Payments and Rates"

    if intent == 'worker_availability':
        reply = (
            f"🟢 **Managing Worker Availability**\n\n"
            f"Workers have full control over when they want to accept work:\n\n"
            f"• Go to your [Worker Dashboard](/worker/dashboard/).\n"
            f"• Click the **Toggle Availability** switch.\n"
            f"• **Available (Green):** Your profile appears in search results and on the live map for nearby employers.\n"
            f"• **Busy / Off-duty (Gray):** You won't appear in active searches until you switch back on."
        )
        chips = ["📊 Go to Dashboard", "⚙️ Update Profile", "✓ Verification Badge", "💬 Contact Support"]
        return reply, chips, False, "Worker Availability"

    if intent == 'verification':
        reply = (
            f"✓ **Verified Worker Badge on CivicPro**\n\n"
            f"The **Verified Badge** builds immense trust with employers and increases hire requests:\n\n"
            f"• **What it indicates:** The worker's identity, contact information, and skill history have been reviewed by platform administrators.\n"
            f"• **How to apply:** Ensure your profile photo, phone number, experience years, and trade are completely filled out at [Worker Profile Setup](/worker/profile/setup/).\n"
            f"• **Admin Review:** Our verification team reviews active profiles weekly. You can also message our admin team here to request an expedited review."
        )
        chips = ["⚙️ Complete My Profile", "👤 Worker Dashboard", "📝 Request Fast Verification", "🔍 Search Workers"]
        return reply, chips, False, "Worker Verification"

    if intent == 'reviews':
        reply = (
            f"⭐ **Ratings & Reviews System**\n\n"
            f"CivicPro relies on honest community feedback:\n\n"
            f"• **When can you review?** Only after a hire request is marked as **Completed** by the employer.\n"
            f"• **How it helps:** Transparent reviews reward dedicated workers with higher visibility on the search map and help employers hire with confidence.\n"
            f"• **Rating scale:** 1 to 5 stars, along with descriptive feedback on punctuality, workmanship, and behavior."
        )
        chips = ["📋 Employer Dashboard", "🔍 Search Workers", "⭐ Best Rated Workers", "❓ Help Center"]
        return reply, chips, False, "Reviews and Ratings"

    if intent == 'auth_trouble':
        reply = (
            f"🔐 **Account & Login Assistance**\n\n"
            f"• **Sign In:** Access your account anytime at [Login Page](/login/).\n"
            f"• **New Accounts:** Choose either [Worker Registration](/register/worker/) or [Employer Registration](/register/employer/).\n"
            f"• **Password Reset:** If you are unable to remember your credentials, you can contact our administrator team directly or ask an admin to reset it from the control panel."
        )
        chips = ["🔑 Go to Login", "📝 Register New Account", "💬 Request Admin Help", "🏠 Return Home"]
        return reply, chips, False, "Account and Login"

    if intent == 'location_map':
        reply = (
            f"📍 **Location & Interactive Map Navigation**\n\n"
            f"CivicPro uses OpenStreetMap & Leaflet with intelligent distance calculations:\n\n"
            f"• **Map Access:** Open the [Worker Search Page](/search/) to explore the live map with interactive pins.\n"
            f"• **Device GPS:** When prompted by your browser, tap **Allow Location** so CivicPro can automatically calculate distances to nearby workers.\n"
            f"• **City / Area Search:** If GPS is unavailable, you can type your locality or city (e.g., *Kochi, Palakkad, Thrissur, Bangalore*) to locate workers."
        )
        chips = ["🗺️ Open Search Map", "⚙️ Update My Location", "🔍 Filter by Skill", "🚨 Emergency Services"]
        return reply, chips, False, "Map and Location"

    if intent == 'gratitude':
        reply = (
            f"😊 You're very welcome, {name}! I'm always here to help you get the best experience on CivicPro.\n\n"
            f"Is there anything else regarding hiring, worker profiles, or platform features I can assist you with today?"
        )
        chips = ["🔍 Find Workers", "🚨 Emergency SOS", "📋 Help Center", "✓ Worker Verification"]
        return reply, chips, False, "Gratitude"

    # Default / Greeting
    if intent == 'greeting':
        greeting_text = f"Hello {name}! 👋 I am **Maya**, your CivicPro AI Support Executive."
        if role == 'WORKER':
            role_hint = f"I see you're registered as a **Worker** ({user_ctx.get('skill') or 'Skilled Trade'}). How can I assist with your dashboard, daily wage settings, or job requests today?"
        elif role == 'EMPLOYER':
            role_hint = "I see you're an **Employer**. Are you looking to hire skilled workers, check your active bookings, or learn about daily wages?"
        else:
            role_hint = "Whether you are looking to hire skilled daily-wage workers or register your own trade, I'm here to guide you step-by-step!"

        reply = f"{greeting_text}\n\n{role_hint}\n\nFeel free to ask any question, or select a quick topic below:"
        chips = [
            "👷 How to Find & Hire Workers",
            "🛠️ Worker Profile Setup & Rates",
            "💰 How Daily Wages Work",
            "🚨 Emergency SOS Guide"
        ]
        return reply, chips, False, "Greetings"

    # General fallback
    reply = (
        f"Thank you for reaching out, {name}! I'm **Maya**, CivicPro's AI Support Executive.\n\n"
        f"I can help you with:\n"
        f"• **Hiring:** Finding certified electricians, plumbers, carpenters, masons, and more on our interactive map.\n"
        f"• **Worker Profiles:** Setting daily wages, updating skills, and toggling availability.\n"
        f"• **Direct Payments:** How our transparent zero-commission daily-wage payments operate.\n"
        f"• **Emergency Services:** On-site SOS assistance for medical, police, and fire alerts.\n\n"
        f"Could you please tell me a bit more about what you need assistance with?"
    )
    chips = [
        "🔍 Find Workers Near Me",
        "🛠️ Worker Onboarding Help",
        "💰 Payment Guidelines",
        "💬 Speak with Human Admin"
    ]
    return reply, chips, False, "General Inquiry"


def call_external_llm_if_available(message, user_ctx, history):
    """
    Optional external LLM integration (e.g. Gemini or OpenAI)
    using only standard Python urllib, with zero extra dependencies!
    Returns None if no API key or upon failure, gracefully falling back.
    """
    gemini_key = getattr(settings, 'GEMINI_API_KEY', None) or os.environ.get('GEMINI_API_KEY')
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            prompt = (
                f"{SYSTEM_PROMPT}\n\n"
                f"User Context: {json.dumps(user_ctx)}\n"
                f"User Message: {message}\n"
                f"Please reply concisely and helpfully as Maya."
            )
            data = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=6) as response:
                result = json.loads(response.read().decode('utf-8'))
                text = result['candidates'][0]['content']['parts'][0]['text']
                return text
        except Exception:
            pass

    return None


def get_ai_support_response(message, user=None, history=None):
    """
    Main entry point for generating AI executive support responses.
    """
    clean_msg = message.strip()
    user_ctx = get_user_context(user)
    intent = detect_intent(clean_msg.lower())

    # Try external LLM if configured, otherwise rule-based
    llm_reply = call_external_llm_if_available(clean_msg, user_ctx, history)
    
    rule_reply, chips, escalated, subject = generate_rule_based_response(intent, clean_msg, user_ctx)

    if llm_reply:
        final_reply = llm_reply
    else:
        final_reply = rule_reply

    return {
        'reply': final_reply,
        'chips': chips,
        'escalated': escalated,
        'subject': subject,
        'intent': intent,
    }
