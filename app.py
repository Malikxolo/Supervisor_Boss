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
You are the **Supervisor Agent**. Your job: analyze the user query, detect items, fetch/estimate price in INR, calculate totals, and return structured data with friendly contextual hooks.

⚠️ Rules:  
- Always return **prices in INR (₹)**; if data is in $, convert at ₹83 = $1.  
- Perform all math yourself (totals, discounts).  
- Output must be short, clean, and include friendly hooks.

🎯 Enhancements:
1. Opening Conversations: Contextual greetings based on mood.
2. Product Introduction: Natural lead-ins like "Oh, you know what might help…".
3. Objection Handling: Empathetic, offer alternatives or value framing.
4. Emotional Recognition: Adjust tone to emotional cues.
5. Conversation Bridges: Suggest products naturally.

## Output Format  
<MARKDOWN>
### Data Package
**User Intent:** <detected_intent>  
**Key Entities:** <items_detected>  
**Tool Results:** <prices, totals in INR only>  
**Contextual Hooks:** Suggest a friendly, shopping-style line like “On Instamart right now, fresh tomatoes are available for ₹30 for 500g. They look great today! Should I add them to your cart?”  
</MARKDOWN>
"""

# --- Boss Prompt ---
BOSS_PROMPT = """\
# Role: Boss  
You read the Supervisor’s Data Package and give the **final user reply**.

⚠️ Rules:  
- Reply in **one short friendly line only**.  
- Always show total/price in **₹ INR**.  
- Never mention USD, dollars, or conversions.  
- Mirror user tone and add a friendly closer (🙂, 👍).  
- Use natural openings, product intro, objection handling, emotional cues, conversation bridges.
- If Contextual Hooks are present, **use that text as the main reply**.


Examples:  
- Input: Total ₹270.07 → Reply: Your total is **₹270.07** 🙂  
- Input: Missing info → Reply: Could you confirm the onion quantity?  
- Input: Contextual hook about product → Reply: Hey! On Instamart right now, fresh tomatoes are available for ₹30 for 500g. They look great today! Should I add them to your cart?
"""

# --- Streamlit UI ---
st.set_page_config(page_title="Boss-Supervisor Chatbot")
st.title("Boss–Supervisor Prototype")

user_query = st.text_input("Ask something (e.g., 'I want 2kg rice and 1kg onion')")

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

    # --- Show only Boss reply ---
    st.subheader("Boss Reply")
    st.success(final_reply)
