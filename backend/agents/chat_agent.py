"""
Chat Agent - Handles conversational interactions with users
Uses Gemini to provide intelligent responses about claims, policies, and general questions
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from typing import Dict, Any, Optional, List
from datetime import datetime
import re


class ChatAgent:
    """Agent to handle conversational chat interactions"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.name = "Chat Assistant"
        self.conversation_history: List[Dict[str, str]] = []
    
    async def chat(
        self, 
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user message and generate intelligent response
        
        Args:
            user_message: User's input message
            context: Optional context (claim data, user info, etc.)
            conversation_id: Optional conversation ID for history tracking
            
        Returns:
            Dict with response text, suggestions, and metadata
        """
        
        # Build context string
        context_str = ""
        if context:
            if context.get("claim_data"):
                claim = context["claim_data"]
                context_str = f"""
Current Claim Context:
- Policy Number: {claim.get('policy_number', 'N/A')}
- Claim Type: {claim.get('claim_type', 'N/A')}
- Claim Amount: ${claim.get('claim_amount', 0)}
- Status: {claim.get('status', 'N/A')}
"""
            if context.get("available_claims"):
                context_str += f"\nUser has {len(context['available_claims'])} submitted claim(s)."
        
        # Build prompt with system instructions
        system_prompt = """You are a helpful AI Claims Assistant for an insurance company. 
Your role is to:
1. Help users submit insurance claims through a conversational interface
2. Answer questions about claims, policies, and insurance processes
3. Guide users through the claim submission process step-by-step
4. Provide friendly, professional, and accurate information
5. Ask clarifying questions when needed
6. Help users understand claim status and next steps

Guidelines:
- Be conversational and friendly, but professional
- Break down complex information into simple steps
- Use emojis sparingly to make responses engaging
- If asked about a specific claim, use the provided context
- If you don't know something, admit it and suggest contacting support
- Always guide users toward completing their claim submission

Current conversation context will be provided. Use it to give relevant, personalized responses."""
        
        # Build the full prompt
        prompt = ChatPromptTemplate.from_messages([
            ("human", f"""{system_prompt}

{context_str}

User Message: {user_message}

Provide a helpful, conversational response. If the user is asking about:
- Claim submission: Guide them through the process
- Claim status: Use context if available, otherwise ask for claim ID
- General questions: Answer helpfully
- Policy questions: Provide general guidance and suggest checking their policy document

Respond naturally and conversationally.""")
        ])
        
        try:
            # Get response from LLM
            response = await self.llm.ainvoke(prompt.format_messages())
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Extract suggestions/actions from response
            suggestions = self._extract_suggestions(response_text, user_message)
            
            # Determine intent
            intent = self._detect_intent(user_message)
            
            return {
                "response": response_text,
                "suggestions": suggestions,
                "intent": intent,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "response": f"I apologize, but I encountered an error: {str(e)}. Please try again or contact support.",
                "suggestions": ["Try rephrasing your question", "Contact support"],
                "intent": "error",
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_suggestions(self, response_text: str, user_message: str) -> List[str]:
        """Extract suggested next actions from response"""
        suggestions = []
        lower_msg = user_message.lower()
        
        # Context-based suggestions
        if "claim" in lower_msg and "submit" in lower_msg:
            suggestions = ["Start claim submission", "View existing claims", "Check claim status"]
        elif "status" in lower_msg or "progress" in lower_msg:
            suggestions = ["View dashboard", "Check specific claim", "Contact support"]
        elif "help" in lower_msg or "how" in lower_msg:
            suggestions = ["View FAQ", "Start claim", "Contact support"]
        else:
            suggestions = ["Submit a claim", "View dashboard", "Get help"]
        
        return suggestions
    
    def _detect_intent(self, user_message: str) -> str:
        """Detect user intent from message"""
        lower_msg = user_message.lower()
        
        if any(word in lower_msg for word in ["submit", "file", "new claim"]):
            return "submit_claim"
        elif any(word in lower_msg for word in ["status", "progress", "update"]):
            return "check_status"
        elif any(word in lower_msg for word in ["help", "how", "what", "explain"]):
            return "get_help"
        elif any(word in lower_msg for word in ["policy", "coverage", "covered"]):
            return "policy_question"
        elif any(word in lower_msg for word in ["thank", "thanks", "bye", "goodbye"]):
            return "closing"
        else:
            return "general_query"

