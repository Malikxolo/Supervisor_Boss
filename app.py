import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

# --- Load environment variables ---
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- Init Groq client ---
client = Groq(api_key=GROQ_API_KEY)

# --- Supervisor Prompt ---
SUPERVISOR_PROMPT = """\
# Role: Supervisor  
You are the Supervisor Agent. Analyze user queries and decide whether it's:
1. A shopping/pricing query → calculate prices, totals in INR, and provide structured Data Package.
2. A policy/FAQ question → summarize intent and relevant response info for Boss.

⚠️ Rules:
- Always return prices in INR (₹), convert if needed.
- Perform all math yourself (totals, discounts).
- Detect emotional cues and context.
- Keep output short and clean.

🎯 Enhancements:
1. Opening Conversations: contextual greetings.
2. Product Introduction: natural lead-ins.
3. Objection Handling: empathetic, alternatives/value framing.
4. Emotional Recognition: adjust tone.
5. Conversation Bridges: suggest products naturally.

## Output Format
<MARKDOWN>
### Data Package
**User Intent:** <detected_intent>
**Key Entities:** <main_entities_from_query>
**Tool Results:** <prices, totals, or info>
**Contextual Hooks:** <extra_info_or_context>
</MARKDOWN>
"""

# --- Boss Prompt ---
BOSS_PROMPT = """\
# Role: Boss  
You read the Supervisor’s Data Package and give the final user reply.

⚠️ Rules:
- Reply in one short friendly line only.
- Show total/price in ₹ INR if shopping.
- Mirror user tone and add friendly closers (🙂, 👍).
- For policy/FAQ questions, give clear reassurance or instructions.
- Use natural openings, product intros, objection handling, emotional cues, conversation bridges.

Examples:
- Shopping total: Total ₹270.07 → Reply: Your total is **₹270.07** 🙂
- Missing info: Reply: Could you confirm the onion quantity?
- Policy: Bananas bruised → Reply: Absolutely! We have a freshness guarantee 🙂...
"""

# --- Streamlit UI ---
st.set_page_config(page_title="Boss-Supervisor Chatbot")
st.title("Boss–Supervisor Prototype")

user_query = st.text_input("Ask something (e.g., 'I want 2kg rice' or 'Are bananas fresh?')")

if st.button("Send") and user_query:
    with st.spinner("Supervisor thinking..."):
        sup_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SUPERVISOR_PROMPT},
                {"role": "user", "content": user_query}
            ]
        )
        data_package = sup_response.choices[0].message.content

    with st.spinner("Boss responding..."):
        boss_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": BOSS_PROMPT},
                {"role": "user", "content": data_package}
            ]
        )
        final_reply = boss_response.choices[0].message.content.strip().replace('"', '')

    st.subheader("Boss Reply")
    st.success(final_reply)
