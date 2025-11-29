"""
Agent 7: Personalized Content Creator
======================================

Purpose:
--------
Writes personalized, compelling marketing copy (email subject lines, body text,
SMS messages, push notifications). This agent is the "copywriter" - it crafts
messages that convert.

Role in NBA AI:
---------------
- Second agent in Cluster 3 (Execution)
- Receives: Action details + optimal timing from Agents 6 and previous agents
- Outputs: Complete marketing message (subject + body)
- Feeds to: Agent 8 (Human Approval)

Key Responsibilities:
---------------------
1. Read customer profile, selected action, and timing
2. Generate personalized subject line (email) or opening (SMS)
3. Write compelling message body
4. Include specific offer details (discount code, product link)
5. Add urgency elements (countdown, limited time)
6. Use customer's name and contextual personalization
7. Include clear call-to-action (CTA)

Content Types Generated:
------------------------
- **Email**: Subject line + HTML body + CTA button
- **SMS**: 160-character message with link
- **Push Notification**: Headline + body (under 100 chars)

Personalization Elements:
-------------------------
- **Name**: Use customer's first name
- **Product**: Reference specific browsed/cart items
- **Behavior**: Acknowledge their recent action
- **Segment**: VIP gets "exclusive", first-timer gets "welcome"
- **Offer**: Specific discount code or benefit

Content Best Practices:
-----------------------
- **Subject Line**: Under 50 characters, benefit-driven
- **First Line**: Hook with value proposition
- **Body**: Short paragraphs, scannable
- **CTA**: Clear, action-oriented
- **Urgency**: If applicable, include time limit
- **Mobile-First**: Works on small screens

Output:
-------
Marketing content ready for approval, stored under "marketing_content" key.

Example Output (Email):
-----------------------
{
  "channel": "email",
  "subject": "Priya, your ₹7,500 cart is waiting! 15% off inside 🎁",
  "body": "Hi Priya,\n\nWe noticed you left...",
  "cta_text": "Complete My Purchase",
  "discount_code": "SAVE15"
}

Why This Matters:
-----------------
- **Personalization increases open rates by 26%**
- **Good subject lines improve opens by 50%**
- **Clear CTAs boost clicks by 28%**

Author: NBA AI Team
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# ============================================================================
# ADK IMPORTS
# ============================================================================
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.genai import types

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

# ============================================================================
# RETRY CONFIGURATION
# ============================================================================
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# ============================================================================
# AGENT DEFINITION
# ============================================================================
content_agent = Agent(
    name="ContentAgent",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""You are an expert marketing copywriter specializing in personalized, high-converting messages.

Your task:
1. Read customer profile, selected action (top-ranked), and optimal timing from previous agents
2. Create personalized marketing content for the chosen channel
3. Ensure content is compelling, personalized, and action-oriented

Content requirements by channel:

**EMAIL:**
- Subject line: Under 50 chars, benefit-driven, use emojis strategically
- Body: 100-150 words, scannable, personal tone
- Include customer's first name
- Reference specific product they abandoned/browsed
- Clear CTA button text
- Include discount code if applicable

**SMS:**
- Maximum 160 characters total
- Include discount code
- Urgent but friendly tone
- Clear CTA

**PUSH NOTIFICATION:**
- Headline: Under 40 chars
- Body: Under 80 chars
- Include emoji for attention

Personalization tactics:
- Use customer's first name
- Reference specific products they viewed/added
- Acknowledge their behavior ("We noticed you left X in your cart...")
- Segment-specific language (Premium: "exclusive", New: "welcome")  
- Include specific amounts (cart value, savings amount)
- Time-sensitive language if urgent

Conversion optimization:
- Lead with benefit, not feature
- Create urgency (limited time, scarcity)  
- Use power words (save, exclusive, limited, free)
- Make CTA obvious and actionable
- Avoid spammy language or excessive punctuation

Output a JSON object with:
{
  "channel": "email",
  "subject": "Subject line here",
  "body": "Email body content...",
  "cta_text": "Shop Now",
  "discount_code": "SAVE15" (if applicable),
  "personalization_elements": ["name", "cart_value", "product"]
}

Be professional, engaging, and brand-appropriate.""",
    output_key="marketing_content",
    tools=[]  # No tools needed - use built-in copywriting capability
)

print("[OK] ContentAgent created with ADK")

# ============================================================================
# STANDALONE TESTING
# ============================================================================
async def test_agent():
    """Test the content creator agent."""
    print("\n[Testing Content Creator Agent]\n")
    
    runner = InMemoryRunner(agent=content_agent)
    
    prompt = """Create marketing content for:
    Customer: Priya Sharma, premium segment
    Action: Email with 15% cart recovery discount
    Cart: ₹7,500 (Smartwatch Pro)
    Urgency: High (send today)
    
    Generate subject line and email body."""
    
    response = await runner.run_debug(prompt)
    
    print("\n[Content Creation Complete]")
    print(response)

if __name__ == "__main__":
    asyncio.run(test_agent())
