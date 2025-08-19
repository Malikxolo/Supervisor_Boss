import streamlit as st
import os
import json
from groq import Groq
import requests
from dotenv import load_dotenv
import time
import re

load_dotenv()

# Initialize APIs
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily_api_key = os.getenv("TAVILY_API_KEY")

# Latest Groq models
SUPERVISOR_MODEL = "llama-3.3-70b-versatile"
BOSS_MODEL = "llama-3.3-70b-versatile"

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.greeting_count = 0
    st.session_state.user_memory = {}
    st.session_state.order_history = []
    st.session_state.user_location = None
    st.session_state.location_asked = False
    st.session_state.welcomed = False
    st.session_state.cart_items = []
    st.session_state.cart_total = 0

def tavily_search(query, search_type="basic"):
    """Enhanced Tavily search with robust error handling"""
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": tavily_api_key,
        "query": query,
        "search_depth": search_type,
        "include_answer": True,
        "include_raw_content": False,
        "max_results": 8,
        "include_domains": ["swiggy.com", "instamart.swiggy.com"] if "swiggy" in query.lower() else None
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Search failed with status {response.status_code}"}
    except Exception as e:
        return {"error": f"Search error: {str(e)}"}

def detect_location_in_query(user_query):
    """Detect location information"""
    location_keywords = [
        "mumbai", "delhi", "bangalore", "bengaluru", "chennai", "hyderabad", 
        "pune", "kolkata", "ahmedabad", "jaipur", "lucknow", "kanpur", 
        "nagpur", "indore", "bhopal", "visakhapatnam", "patna", "ludhiana",
        "nagar", "colony", "sector", "area", "road", "street", "gali", 
        "mohalla", "block", "phase", "extension", "vihar", "puram",
        "mein hun", "se hun", "mein rehta", "mein rehti", "location", 
        "address", "jagah", "sheher", "city"
    ]
    
    return any(keyword in user_query.lower() for keyword in location_keywords)

def enhanced_supervisor_agent(user_query):
    """Supervisor agent with comprehensive search and analysis"""
    
    # Check if this is first interaction and no location set
    if not st.session_state.user_location and not st.session_state.location_asked:
        st.session_state.location_asked = True
        return f"""
        ANALYSIS_TYPE: LOCATION_REQUEST
        USER_QUERY: {user_query}
        ACTION_REQUIRED: Ask for user location before proceeding
        LANGUAGE_DETECTED: {"hinglish" if any(word in user_query.lower() for word in ["hai", "ho", "ka", "ke"]) else "english"}
        """
    
    # Check if user is providing location
    if detect_location_in_query(user_query) and not st.session_state.user_location:
        st.session_state.user_location = user_query.strip()
        st.session_state.welcomed = False
        return f"""
        ANALYSIS_TYPE: LOCATION_RECEIVED
        USER_LOCATION: {user_query}
        ACTION_REQUIRED: Welcome user and ask how to help
        LANGUAGE_DETECTED: {"hinglish" if any(word in user_query.lower() for word in ["hai", "ho", "ka", "ke"]) else "english"}
        """
    
    # Check if we need to give welcome message after location
    if st.session_state.user_location and not st.session_state.welcomed:
        st.session_state.welcomed = True
        return f"""
        ANALYSIS_TYPE: WELCOME_MESSAGE
        USER_LOCATION: {st.session_state.user_location}
        ACTION_REQUIRED: Give welcome message and ask how to help
        LANGUAGE_DETECTED: {"hinglish" if any(word in user_query.lower() for word in ["hai", "ho", "ka", "ke"]) else "english"}
        """
    
    # Normal processing
    greetings = ["hi", "hello", "hey", "helo", "hii", "namaste", "namaskar"]
    query_lower = user_query.lower().strip()
    
    if query_lower in greetings:
        st.session_state.greeting_count += 1
    else:
        st.session_state.greeting_count = 0
    
    # Context-aware search queries
    search_queries = []
    query_context = {
        "is_product_query": False,
        "is_weather_query": False,
        "is_price_query": False,
        "is_party_query": False,
        "is_inappropriate": False,
        "language": "english",
        "user_location": st.session_state.user_location
    }
    
    # Detect language
    hindi_words = ["hai", "ho", "ka", "ke", "ki", "me", "se", "aaj", "kal", "kya", "kaise"]
    if any(word in user_query.lower() for word in hindi_words):
        query_context["language"] = "hinglish"
    
    # Enhanced context detection and search
    if any(word in query_lower for word in ["party", "celebration", "birthday", "festival"]):
        query_context["is_party_query"] = True
        party_search = f"party snacks budget chips popcorn cold drinks namkeen cookies {st.session_state.user_location} price"
        search_queries.append(party_search)
    
    elif any(keyword in query_lower for keyword in ["kg", "gram", "liter", "price", "cost", "buy", "order", "tomato", "onion", "potato", "sabzi", "vegetable", "bhav", "rate", "fruit", "exotic"]):
        query_context["is_product_query"] = True
        location_query = f"{user_query} price {st.session_state.user_location} Swiggy Instamart cost rate"
        search_queries.append(location_query)
    
    elif any(keyword in query_lower for keyword in ["weather", "mausam", "baarish", "rain", "garmi", "hot", "thandi", "cold"]):
        query_context["is_weather_query"] = True
        search_queries.append(f"weather today {st.session_state.user_location} {user_query}")
    
    # Default search - Enhanced for recommendations
    if not search_queries and not any(keyword in user_query.lower() for keyword in ["sex", "lund", "chutiya", "madarchod"]):
        # MINIMAL CHANGE: Add specific search for recommendation requests
        if any(phrase in user_query.lower() for phrase in ["kuch bhi", "recommend", "batado", "suggest", "kuch bhi batado"]):
            search_queries.append(f"Swiggy Instamart popular snacks chips cold drinks {st.session_state.user_location} price")
        else:
            search_queries.append(f"{user_query} {st.session_state.user_location} Swiggy Instamart")
    
    # Perform searches
    search_results = {}
    for query in search_queries:
        if query:
            search_results[query] = tavily_search(query)
    
    # Comprehensive supervisor analysis
    supervisor_prompt = f"""
    <supervisor_analysis>
    USER_QUERY: {user_query}
    QUERY_CONTEXT: {json.dumps(query_context, indent=2)}
    GREETING_COUNT: {st.session_state.greeting_count}
    USER_MEMORY: {json.dumps(st.session_state.user_memory, indent=2)}
    ORDER_HISTORY: {json.dumps(st.session_state.order_history[-3:], indent=2)}
    SEARCH_RESULTS: {json.dumps(search_results, indent=2)}
    
    Analyze this data comprehensively:
    
    INTERPRETATION: [What user wants - be specific about context]
    CONTEXT_CLUES: [Mood, weather, language, urgency, party/celebration context]
    PRODUCT_DATA: [Product prices and availability from search results - prioritize context-appropriate items]
    CALCULATIONS: [Price/quantity calculations needed]
    MEMORY_INSIGHTS: [Previous orders or preferences]
    RESPONSE_STRATEGY: [How to approach - empathetic/sales/informative]
    PRICE_EXTRACTION: [All specific prices found with context relevance]
    CONTEXT_APPROPRIATENESS: [Ensure suggestions match user context]
    </supervisor_analysis>
    """
    
    try:
        response = groq_client.chat.completions.create(
            model=SUPERVISOR_MODEL,
            messages=[
                {
                    "role": "system", 
                    "content": """You are the Supervisor for Swiggy Instamart sales team. Provide comprehensive analysis to help the sales representative respond naturally and contextually.

Key responsibilities:
- Extract accurate pricing and product information from search results
- Understand user context (party, weather, specific products)
- Provide structured insights for natural conversation flow
- Ensure suggestions match user's actual needs and context"""
                },
                {"role": "user", "content": supervisor_prompt}
            ],
            temperature=0.2,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"SUPERVISOR_ERROR: {str(e)}\nBasic analysis: User needs assistance."

def enhanced_boss_agent(supervisor_analysis, user_query):
    """Boss agent with natural AI thinking and improved recommendation handling"""
    
    # Handle location flow
    if "ANALYSIS_TYPE: LOCATION_REQUEST" in supervisor_analysis:
        is_hindi = any(word in user_query.lower() for word in ["hai", "ho", "ka", "ke", "ki", "kya", "kaise"])
        return "Aapka location batao pehle. Kahan se ho?" if is_hindi else "Tell me your location first. Where are you from?"
    
    if "ANALYSIS_TYPE: LOCATION_RECEIVED" in supervisor_analysis:
        is_hindi = any(word in user_query.lower() for word in ["hai", "ho", "ka", "ke", "ki"])
        return f"Achha, {st.session_state.user_location}! Kya chahiye batao?" if is_hindi else f"Got it, {st.session_state.user_location}! What do you need?"
    
    # Get recent conversation context
    recent_conversation = st.session_state.messages[-5:] if len(st.session_state.messages) >= 5 else st.session_state.messages
    
    # Enhanced confirmation detection
    confirmation_signals = [
        "add krdo", "add karo", "cart mein daal", "haan add", "yes add", "add kar", 
        "krdo", "yes sure add", "add it", "add all", "daal do"
    ]
    user_wants_cart_action = any(signal in user_query.lower() for signal in confirmation_signals)
    
    # Also check for standalone confirmations
    standalone_confirmations = ["haan", "yes", "ok", "okay", "sure", "han"]
    if user_query.strip().lower() in standalone_confirmations:
        if recent_conversation and recent_conversation[-1]["role"] == "assistant":
            last_bot_message = recent_conversation[-1]["content"]
            if "₹" in last_bot_message and ("add karu" in last_bot_message.lower() or "cart" in last_bot_message.lower()):
                user_wants_cart_action = True
    
    boss_prompt = f"""
    USER MESSAGE: "{user_query}"
    SUPERVISOR ANALYSIS: {supervisor_analysis}
    USER LOCATION: {st.session_state.user_location}
    RECENT CONVERSATION: {json.dumps(recent_conversation, indent=2)}
    CURRENT CART: {len(st.session_state.cart_items)} items, Total: ₹{st.session_state.cart_total}
    CART ITEMS: {st.session_state.cart_items}
    USER_WANTS_CART_ACTION: {user_wants_cart_action}
    
    You are a Swiggy Instamart sales person. Think naturally about this conversation.
    
    Natural behavior guidelines:
    - Understand Hindi confirmations: "haan" = yes, "add krdo" = please add
    - For party requests: suggest appropriate party items (snacks, drinks, not vegetables)
    - Always ask confirmation before adding items to cart
    - When user confirms adding multiple items, list all items with prices, calculate total, include CART_ADD commands, and suggest payment
    - Use natural, conversational language
    - Be helpful and context-aware
    """
    
    try:
        response = groq_client.chat.completions.create(
            model=BOSS_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a friendly Swiggy Instamart sales person in {st.session_state.user_location}.

Natural conversation principles:
- Understand context and respond appropriately
- "haan" means "yes" (never a product name)
- For confirmations like "add all" or "yes sure add", immediately add ALL discussed items
- When adding multiple items: list each item with price, show total, use CART_ADD format, suggest payment
- For party queries: suggest snacks, drinks, party food
- Always be helpful and natural

Hindi understanding:
- haan/han = yes, nahi = no, krdo = please do, chahiye = want/need
- kuch bhi = anything/something (recommend specific items from search results)
- Treat these as natural language, not product names

CRITICAL for recommendations:
- When users say "kuch bhi", "recommend something", "batado" - suggest 3-4 specific products with prices from search results
- Never give generic explanations about services or delivery
- Focus ONLY on actual products found in search results
- If no specific products found, ask what category they prefer (snacks, drinks, fruits, etc.)
- Be direct and product-focused, not service-focused

Cart behavior:
- Only add items after explicit user confirmation
- For multiple items: "Item1 ₹price, Item2 ₹price cart mein add kar diye! Total ₹total hai. Swiggy app mein payment karo!"
- Use CART_ADD: itemname ₹price for each item to be added

Cart limitations - be natural about these:
- When users ask to view cart details, remove items, clear cart, or make payment
- Tell them naturally that they need to use the Swiggy Instamart app for these operations
- You can only add items to cart, not manage or view detailed cart contents
- Be helpful and suggest they check the app for cart management"""
                },
                {"role": "user", "content": boss_prompt}
            ],
            temperature=0.4,  # Lowered for more focused responses
            max_tokens=250
        )
        
        bot_response = response.choices[0].message.content
        
        # Process cart additions when user confirms
        if user_wants_cart_action:
            if "CART_ADD:" in bot_response:
                # Process AI's CART_ADD commands
                cart_additions = re.findall(r'CART_ADD:\s*([^₹]+)₹(\d+)', bot_response)
                for item_name, price in cart_additions:
                    try:
                        st.session_state.cart_items.append({
                            "query": item_name.strip(),
                            "price": int(price),
                            "timestamp": time.time()
                        })
                        st.session_state.cart_total += int(price)
                    except (ValueError, TypeError):
                        continue
                
                # Clean CART_ADD commands from response
                bot_response = re.sub(r'CART_ADD:[^₹]+₹\d+\s*', '', bot_response).strip()
            
            elif recent_conversation:
                # Fallback: extract items from previous bot message if no CART_ADD
                last_bot_message = recent_conversation[-1]["content"] if recent_conversation[-1]["role"] == "assistant" else ""
                price_pattern = r'(\w+(?:\s+\w+)*)\s*₹(\d+)'
                items_found = re.findall(price_pattern, last_bot_message)
                
                if items_found:
                    added_items = []
                    for item_name, price in items_found:
                        try:
                            st.session_state.cart_items.append({
                                "query": item_name.strip(),
                                "price": int(price),
                                "timestamp": time.time()
                            })
                            st.session_state.cart_total += int(price)
                            added_items.append(f"{item_name.strip()} ₹{price}")
                        except (ValueError, TypeError):
                            continue
                    
                    if added_items:
                        items_list = ", ".join(added_items)
                        bot_response = f"{items_list} cart mein add kar diye hain! Total ₹{st.session_state.cart_total} hai. Swiggy app mein payment karo!"
        
        return bot_response
        
    except Exception as e:
        return "Technical issue hai, kshama karein!"

def update_user_memory(user_query, bot_response):
    """Smart memory management"""
    if any(word in user_query.lower() for word in ["kg", "buy", "order", "add cart"]):
        st.session_state.order_history.append({
            "query": user_query,
            "response": bot_response,
            "timestamp": time.time(),
            "location": st.session_state.user_location
        })
    
    if any(phrase in user_query.lower() for phrase in ["i like", "i prefer", "my name", "i am"]):
        st.session_state.user_memory[f"preference_{len(st.session_state.user_memory)}"] = {
            "info": user_query,
            "timestamp": time.time()
        }

def main():
    st.set_page_config(
        page_title="Swiggy Instamart Assistant",
        page_icon="🛒",
        layout="wide"
    )
    
    st.title("🛒 Swiggy Instamart Sales Assistant")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Kuch chahiye? Type kar ke batao... 💬"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Show processing status
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            # Supervisor processing
            message_placeholder.markdown("🔍 Analyzing your request...")
            supervisor_analysis = enhanced_supervisor_agent(prompt)
            
            # Boss response generation
            message_placeholder.markdown("💭 Preparing natural response...")
            bot_response = enhanced_boss_agent(supervisor_analysis, prompt)
            
            # Final response
            message_placeholder.markdown(bot_response)
        
        # Add bot response to history
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        
        # Update memory
        update_user_memory(prompt, bot_response)

if __name__ == "__main__":
    main()
