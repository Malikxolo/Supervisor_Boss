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
You are the **Supervisor Agent**. Analyze user query, detect items, fetch/estimate price, and return structured data.

⚠️ Rules:  
- Always return prices in INR (₹), convert if needed.
- Perform all math yourself (totals, discounts).
- If user asks for budget/sasta/cheap, include only affordable items.
- Detect user language/tone: English or Roman Hindi (Hinglish).
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
- Mirror the user's language/tone: use Hinglish if user wrote in Roman Hindi.  
- Add emojis where appropriate.  

Examples:
- Shopping total: Total ₹270.07 → Reply: Your total is **₹270.07** 🙂
- Missing info: Reply: Could you confirm the onion quantity?
- Policy: Bananas bruised → Reply: Absolutely! We have a freshness guarantee 🙂...
- Input: 3 vegetables with discount → Reply: Great savings! Should I add these to your cart?
"""

# --- Streamlit UI ---
st.set_page_config(page_title="Boss-Supervisor Chatbot", layout="wide")
st.title("Boss–Supervisor Chatbot (WhatsApp-style)")

# Initialize conversation in session_state
if "conversation" not in st.session_state:
    st.session_state.conversation = []

if "bot_messages" not in st.session_state:
    st.session_state.bot_messages = []

# --- Chat display container (constrained width) ---
chat_container = st.container()
container_style = "max-width:700px; margin:auto;"

# --- Input at bottom like WhatsApp ---
with st.container():
    user_input = st.text_input("Type a message...", key="user_input")
    send_button = st.button("Send")

if send_button and user_input:
    st.session_state.conversation.append({"role": "user", "content": user_input})

    with st.spinner("Supervisor thinking..."):
        sup_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": SUPERVISOR_PROMPT}] + st.session_state.conversation
        )
        data_package = sup_response.choices[0].message.content

    with st.spinner("Bot is replying..."):
        boss_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": BOSS_PROMPT},
                      {"role": "user", "content": data_package}]
        )
        final_reply = boss_response.choices[0].message.content.strip().replace('"', '')
        st.session_state.bot_messages.append({"user": user_input, "bot": final_reply})
        st.session_state.conversation.append({"role": "assistant", "content": final_reply})

# --- Display chat with white bubbles ---
# --- Display chat with white bubbles and black text ---
with chat_container:
    for chat in st.session_state.bot_messages:
        # Bot message (left)
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown(
                f"<div style='max-width:700px; margin:auto; background-color:#ffffff; color:#000000; padding:10px; border-radius:10px; margin:5px 0; border:1px solid #ddd;'>{chat['bot']}</div>",
                unsafe_allow_html=True
            )
        with col2:
            st.write("")

        # User message (right)
        col3, col4 = st.columns([4, 1])
        with col3:
            st.write("")
        with col4:
            st.markdown(
                f"<div style='max-width:700px; margin:auto; background-color:#ffffff; color:#000000; padding:10px; border-radius:10px; margin:5px 0; border:1px solid #ddd;'>{chat['user']}</div>",
                unsafe_allow_html=True
            )

