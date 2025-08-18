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
- Detect situation/emotion: Weather, Party Planning, Emotional Stress, Budget, News, etc. 
- Keep output short and clean.
- If the user asks for **price comparisons across platforms**, fetch/estimate each platform price separately.
- For direct price comparisons (e.g., "Is ₹45 more than ₹40?"), calculate the difference.

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
**Situation:** <Weather / Party / Emotional / Budget / News / etc.>
**Tool Results:** <prices, totals, or info>
**Contextual Hooks:** <extra_info_or_context>
</MARKDOWN>
"""

# --- Boss Prompt ---
BOSS_PROMPT = """\
# Role: Boss  
You read the Supervisor’s Data Package and give the final user reply.

⚠️ Rules:
- Reply in **short, friendly lines**.  
- Always show total/price in **₹ INR**.  
- Mirror user tone and add a friendly closer (🙂, 👍).  
- Use natural openings, product intros, objection handling, emotional cues, conversation bridges.
- For multiple items, present in **numbered list style** with:
    - Name - Price (Quantity)
    - Short description
- Include subtotals, discounts, and final totals clearly.
- Add context-based friendly phrases:
    - Family-sized quantities → "Perfect portion for a family meal!"  
    - Discounts → "Great savings!"  
    - Snacks/fruits → "Perfect for a quick healthy bite!"  
- End product lists or totals with a crisp call-to-action: "Ready to add to your cart?"
- Incorporate friendly suggestions naturally:  
    - Weather → suggest chai, pakode, indoor hacks  
    - Party → snack/cheese platter, instant starter pack  
    - Emotional → comfort food, ice cream, movies  
    - Budget → pocket-friendly options  
    - News → add mini-fun suggestion (chai/biscuit, quick snack) 

Examples:
- Shopping total: Total ₹270.07 → Reply: Your total is **₹270.07** 🙂
- Missing info: Reply: Could you confirm the onion quantity?
- Policy: Bananas bruised → Reply: Absolutely! We have a freshness guarantee 🙂...
- Input: 3 vegetables with discount → Reply: Great savings! Should I add these to your cart?
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






