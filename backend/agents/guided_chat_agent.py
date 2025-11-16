"""
AI-Driven Guided Chat Agent - Handles conversational claim submission
Uses AI to understand natural language, extract information flexibly, and ask intelligent follow-ups
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import re
import json


class GuidedChatAgent:
    """AI-driven agent that guides users through claim submission conversationally"""
    
    # Required fields for claim submission
    REQUIRED_FIELDS = [
        "policy_number",
        "claim_type",
        "claim_amount",
        "incident_date",
        "claimant_name",
        "claimant_email",
        "description",
        "documents"  # Documents are optional but we'll ask for them
    ]
    
    # Field labels for display
    FIELD_LABELS = {
        "policy_number": "Policy Number",
        "claim_type": "Claim Type",
        "claim_amount": "Claim Amount",
        "incident_date": "Incident Date",
        "claimant_name": "Full Name",
        "claimant_email": "Email Address",
        "description": "Incident Description"
    }
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.name = "AI Claims Assistant"
    
    def is_complete(self, collected_data: Dict[str, Any]) -> bool:
        """Check if all required fields are collected (documents are optional)"""
        required_without_docs = [f for f in self.REQUIRED_FIELDS if f != "documents"]
        return all(
            field in collected_data and collected_data[field] 
            for field in required_without_docs
        )
    
    def _normalize_claim_type(self, claim_type: str) -> Optional[str]:
        """Normalize claim type to standard values"""
        claim_type_lower = claim_type.lower().strip()
        
        # Direct matches
        type_map = {
            "auto": "auto", "car": "auto", "vehicle": "auto", "automobile": "auto",
            "health": "health", "medical": "health", "healthcare": "health",
            "home": "home", "house": "home", "property": "home", "homeowner": "home",
            "life": "life", "life insurance": "life"
        }
        
        if claim_type_lower in type_map:
            return type_map[claim_type_lower]
        
        # Partial matches
        for key, value in type_map.items():
            if key in claim_type_lower or claim_type_lower in key:
                return value
        
        return None
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract monetary amount from text"""
        # Remove currency symbols and extract numbers
        amount_pattern = r'[\$]?[\s]*([\d,]+\.?\d*)'
        matches = re.findall(amount_pattern, text)
        
        if matches:
            try:
                # Get the largest number (likely the amount)
                amounts = [float(m.replace(',', '')) for m in matches]
                return max(amounts) if amounts else None
            except ValueError:
                return None
        
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from text and normalize to YYYY-MM-DD. Handles relative dates like 'today', 'yesterday'"""
        text_lower = text.lower().strip()
        today = datetime.now().date()
        
        # Handle relative dates
        relative_dates = {
            "today": today,
            "yesterday": today - timedelta(days=1),
            "tomorrow": today + timedelta(days=1),
            "day before yesterday": today - timedelta(days=2),
            "2 days ago": today - timedelta(days=2),
            "3 days ago": today - timedelta(days=3),
            "a week ago": today - timedelta(weeks=1),
            "last week": today - timedelta(weeks=1),
            "last month": today - timedelta(days=30),
        }
        
        # Check for relative date keywords
        for keyword, date_obj in relative_dates.items():
            if keyword in text_lower:
                return date_obj.strftime("%Y-%m-%d")
        
        # Handle "X days ago" pattern
        days_ago_match = re.search(r'(\d+)\s*days?\s*ago', text_lower)
        if days_ago_match:
            days = int(days_ago_match.group(1))
            date_obj = today - timedelta(days=days)
            return date_obj.strftime("%Y-%m-%d")
        
        # Handle "X weeks ago" pattern
        weeks_ago_match = re.search(r'(\d+)\s*weeks?\s*ago', text_lower)
        if weeks_ago_match:
            weeks = int(weeks_ago_match.group(1))
            date_obj = today - timedelta(weeks=weeks)
            return date_obj.strftime("%Y-%m-%d")
        
        # Handle "X months ago" pattern (approximate)
        months_ago_match = re.search(r'(\d+)\s*months?\s*ago', text_lower)
        if months_ago_match:
            months = int(months_ago_match.group(1))
            date_obj = today - timedelta(days=months * 30)
            return date_obj.strftime("%Y-%m-%d")
        
        # Try YYYY-MM-DD format first
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
        if date_match:
            return date_match.group(1)
        
        # Try MM/DD/YYYY or DD/MM/YYYY
        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text)
        if date_match:
            month, day, year = date_match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Try other date formats
        date_patterns = [
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY-MM-DD
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # MM-DD-YY or MM-DD-YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                parts = match.groups()
                if len(parts[0]) == 4:  # Year first
                    return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
                else:  # Month first
                    year = parts[2] if len(parts[2]) == 4 else f"20{parts[2]}"
                    return f"{year}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
        
        # Try month name formats (e.g., "November 15, 2025" or "15 Nov 2025")
        month_names = {
            'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
            'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
            'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'sept': 9,
            'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
        }
        
        # Pattern: "Month Day, Year" or "Day Month Year"
        month_day_year = re.search(r'(\w+)\s+(\d{1,2}),?\s+(\d{4})', text_lower)
        if month_day_year:
            month_name, day, year = month_day_year.groups()
            if month_name in month_names:
                month_num = month_names[month_name]
                return f"{year}-{month_num:02d}-{int(day):02d}"
        
        # Pattern: "Day Month Year"
        day_month_year = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', text_lower)
        if day_month_year:
            day, month_name, year = day_month_year.groups()
            if month_name in month_names:
                month_num = month_names[month_name]
                return f"{year}-{month_num:02d}-{int(day):02d}"
        
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    async def _extract_information(self, user_message: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to extract claim information from user's natural language message"""
        
        # Build context of what we already have
        existing_info = []
        for field, label in self.FIELD_LABELS.items():
            if field in collected_data and collected_data[field]:
                existing_info.append(f"{label}: {collected_data[field]}")
        # Handle documents separately
        if "documents" in collected_data and isinstance(collected_data["documents"], list) and len(collected_data["documents"]) > 0:
            existing_info.append(f"Documents: {len(collected_data['documents'])} file(s) uploaded")
        
        context_str = "\n".join(existing_info) if existing_info else "No information collected yet"
        
        # Missing fields - prioritize the first missing one (exclude documents)
        missing_fields = [
            self.FIELD_LABELS[field] 
            for field in self.REQUIRED_FIELDS 
            if field != "documents" and field in self.FIELD_LABELS and (field not in collected_data or not collected_data[field])
        ]
        
        # Determine what we're currently asking for (first missing field, exclude documents)
        current_question_field = None
        for field in self.REQUIRED_FIELDS:
            if field != "documents" and field in self.FIELD_LABELS and (field not in collected_data or not collected_data[field]):
                current_question_field = self.FIELD_LABELS[field]
                break
        
        prompt = ChatPromptTemplate.from_messages([
            ("human", f"""You are an AI assistant helping to extract claim information from user messages.

Current collected information:
{context_str}

Currently asking for: {current_question_field if current_question_field else 'All information collected'}

Missing information needed (in order):
{', '.join(missing_fields) if missing_fields else 'All information collected'}

User's message: "{user_message}"

CRITICAL RULES:
1. If we're asking for a specific field and user provides a simple answer (like a number or short text), it's likely for that field
2. Policy numbers can be: pure numbers (1234567), alphanumeric (POL123), or with dashes (POL-123)
3. Claim amounts are usually larger numbers with currency symbols ($5000) or clearly stated as amounts
4. If user provides just a number and we're asking for policy_number, treat it as policy_number NOT claim_amount
5. Only extract information that is clearly provided - don't guess

Your task:
1. Extract claim-related information from the user's message
2. Prioritize the field we're currently asking for
3. Return ONLY a JSON object with extracted information

Return format (JSON only, no other text):
{{
    "policy_number": "extracted string or null",
    "claim_type": "auto/health/home/life or null",
    "claim_amount": number or null,
    "incident_date": "YYYY-MM-DD or null",
    "claimant_name": "extracted string or null",
    "claimant_email": "extracted string or null",
    "description": "extracted string or null"
}}

Extraction rules:
- policy_number: Can be numbers (1234567), alphanumeric (POL123), or with dashes. If we're asking for policy_number and user provides a number, it's likely the policy number.
- claim_type: Normalize to "auto", "health", "home", or "life". Look for keywords like "car", "auto", "medical", "health", "home", "house", "life"
- claim_amount: Only extract if clearly an amount (has $, "dollars", "amount", or context suggests money). Don't confuse with policy numbers.
- incident_date: Look for dates in any format, normalize to YYYY-MM-DD
- claimant_name: Look for proper names (capitalized words)
- claimant_email: Look for email pattern (contains @)
- description: Extract if message is descriptive and doesn't match other fields

IMPORTANT: If we're currently asking for "{current_question_field}" and the user's message is a simple answer (like a number or short text), prioritize that field.

Return ONLY the JSON object, nothing else.""")
        ])
        
        try:
            response = await self.llm.ainvoke(prompt.format_messages())
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Clean response - remove markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            response_text = response_text.strip()
            if response_text.endswith("```"):
                response_text = response_text[:-3].strip()
            
            # Parse JSON
            extracted = json.loads(response_text)
            
            # Merge with existing data, prioritizing extracted values
            updated_data = collected_data.copy()
            
            # Determine what field we're currently asking for
            current_field = None
            for field in self.REQUIRED_FIELDS:
                if field not in collected_data or not collected_data[field]:
                    current_field = field
                    break
            
            # Special handling: if we're asking for policy_number and user provides a simple number
            # prioritize it as policy_number, not claim_amount
            if current_field == "policy_number":
                # Check if user message is a simple number (likely policy number)
                simple_number = re.match(r'^\d{4,}$', user_message.strip())
                if simple_number:
                    # If AI extracted it as claim_amount but not policy_number, fix it
                    if extracted.get("claim_amount") and not extracted.get("policy_number"):
                        # This is likely a policy number, not an amount
                        extracted["policy_number"] = user_message.strip()
                        extracted["claim_amount"] = None
            
            for field in self.REQUIRED_FIELDS:
                extracted_value = extracted.get(field)
                
                # Only update if we don't already have this field OR if extracted value is more complete
                if extracted_value is not None and extracted_value != "":
                    # Skip if we already have this field and it's not empty (unless it's clearly wrong)
                    if field in updated_data and updated_data[field]:
                        # Only overwrite if the new value seems more complete/correct
                        if field == "policy_number" and current_field == "policy_number":
                            # If we're asking for policy_number, prioritize the new value
                            pass  # Allow update
                        elif field == "claim_amount" and current_field != "policy_number":
                            # Only update amount if we're not currently asking for policy number
                            pass  # Allow update
                        else:
                            # For other fields, only update if new value is more complete
                            if len(str(extracted_value)) > len(str(updated_data[field])):
                                pass  # Allow update
                            else:
                                continue  # Skip update
                    
                    # Normalize values
                    if field == "claim_type":
                        normalized = self._normalize_claim_type(str(extracted_value))
                        if normalized:
                            updated_data[field] = normalized
                    elif field == "claim_amount":
                        # Only set amount if it's reasonable (not a policy number)
                        if isinstance(extracted_value, (int, float)):
                            # If it's a very large number and we're asking for policy_number, skip it
                            if current_field == "policy_number" and extracted_value > 1000000:
                                continue  # Likely a policy number, not an amount
                            updated_data[field] = float(extracted_value)
                        elif isinstance(extracted_value, str):
                            amount = self._extract_amount(extracted_value)
                            if amount:
                                # Check if this might be a policy number instead
                                if current_field == "policy_number" and amount > 1000000:
                                    continue  # Likely a policy number
                                updated_data[field] = amount
                    elif field == "incident_date":
                        if isinstance(extracted_value, str):
                            date = self._extract_date(extracted_value) or extracted_value
                            updated_data[field] = date
                    elif field == "claimant_email":
                        email = self._extract_email(str(extracted_value)) or extracted_value
                        updated_data[field] = email
                    elif field == "policy_number":
                        # Policy number can be any string (numbers, alphanumeric, etc.)
                        updated_data[field] = str(extracted_value).strip()
                    else:
                        updated_data[field] = str(extracted_value).strip()
            
            return updated_data
            
        except Exception as e:
            # Fallback: try rule-based extraction
            return self._fallback_extract(user_message, collected_data)
    
    def _fallback_extract(self, user_message: str, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based extraction if AI fails"""
        updated_data = collected_data.copy()
        message_lower = user_message.lower()
        message_stripped = user_message.strip()
        
        # Determine what field we're currently asking for
        current_field = None
        for field in self.REQUIRED_FIELDS:
            if field not in collected_data or not collected_data[field]:
                current_field = field
                break
        
        # Extract policy number - improved to handle pure numbers
        if not updated_data.get("policy_number"):
            # If we're asking for policy number and user provides a simple number, treat it as policy number
            if current_field == "policy_number":
                # Pure numeric policy numbers (4+ digits)
                if re.match(r'^\d{4,}$', message_stripped):
                    updated_data["policy_number"] = message_stripped
                # Alphanumeric policy numbers
                else:
                    policy_match = re.search(r'\b([A-Z]{2,}\d{4,}|\d{4,}[A-Z]{2,}|POL-?\d+|POL\d+)\b', user_message, re.IGNORECASE)
                    if policy_match:
                        updated_data["policy_number"] = policy_match.group(1).upper()
            else:
                # Not currently asking for policy number, use pattern matching
                policy_match = re.search(r'\b([A-Z]{2,}\d{4,}|\d{4,}[A-Z]{2,}|POL-?\d+|POL\d+)\b', user_message, re.IGNORECASE)
                if policy_match:
                    updated_data["policy_number"] = policy_match.group(1).upper()
        
        # Extract claim type
        if not updated_data.get("claim_type"):
            normalized = self._normalize_claim_type(user_message)
            if normalized:
                updated_data["claim_type"] = normalized
        
        # Extract amount - only if we're NOT asking for policy number
        if not updated_data.get("claim_amount") and current_field != "policy_number":
            amount = self._extract_amount(user_message)
            if amount:
                # Don't treat large numbers as amounts if we're asking for policy number
                if current_field == "policy_number" and amount > 1000000:
                    pass  # Skip, likely a policy number
                else:
                    updated_data["claim_amount"] = amount
        
        # Extract date
        if not updated_data.get("incident_date"):
            date = self._extract_date(user_message)
            if date:
                updated_data["incident_date"] = date
        
        # Extract email
        if not updated_data.get("claimant_email"):
            email = self._extract_email(user_message)
            if email:
                updated_data["claimant_email"] = email
        
        # Extract name (simple heuristic - capitalized words)
        if not updated_data.get("claimant_name"):
            name_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', user_message)
            if name_match:
                updated_data["claimant_name"] = name_match.group(1)
        
        # Extract description (if message is long and doesn't match other patterns)
        if not updated_data.get("description") and len(user_message) > 30:
            # Check if it's not just other fields
            if not any([
                updated_data.get("policy_number") in user_message if updated_data.get("policy_number") else False,
                updated_data.get("claim_type") in message_lower if updated_data.get("claim_type") else False,
                str(updated_data.get("claim_amount", "")) in user_message if updated_data.get("claim_amount") else False
            ]):
                updated_data["description"] = user_message.strip()
        
        return updated_data
    
    async def _generate_response(
        self, 
        user_message: str, 
        collected_data: Dict[str, Any],
        extracted_data: Dict[str, Any]
    ) -> str:
        """Use AI to generate natural, contextual response"""
        
        # Determine what was just collected
        newly_collected = []
        for field in self.REQUIRED_FIELDS:
            if field == "documents":
                # Handle documents separately
                doc_count = len(extracted_data.get("documents", [])) if isinstance(extracted_data.get("documents"), list) else 0
                prev_doc_count = len(collected_data.get("documents", [])) if isinstance(collected_data.get("documents"), list) else 0
                if doc_count > prev_doc_count:
                    newly_collected.append(f"Documents: {doc_count - prev_doc_count} file(s) uploaded")
            elif (field in extracted_data and extracted_data[field] and 
                (field not in collected_data or not collected_data[field])):
                if field in self.FIELD_LABELS:
                    value = extracted_data[field]
                    if field == "claim_amount":
                        newly_collected.append(f"{self.FIELD_LABELS[field]}: ${value:,.2f}")
                    else:
                        newly_collected.append(f"{self.FIELD_LABELS[field]}: {value}")
        
        # Determine what's still missing (exclude documents from required check)
        missing_fields = [
            self.FIELD_LABELS[field] 
            for field in self.REQUIRED_FIELDS 
            if field != "documents" and (field not in extracted_data or not extracted_data[field])
        ]
        
        # Determine what field we're currently asking for
        current_question_field = missing_fields[0] if missing_fields else None
        
        # Build context
        all_collected = []
        for field in self.REQUIRED_FIELDS:
            if field == "documents":
                # Handle documents separately
                doc_count = len(extracted_data.get("documents", [])) if isinstance(extracted_data.get("documents"), list) else 0
                if doc_count > 0:
                    all_collected.append(f"Documents: {doc_count} file(s) uploaded")
            elif field in extracted_data and extracted_data[field]:
                if field in self.FIELD_LABELS:
                    all_collected.append(f"{self.FIELD_LABELS[field]}: {extracted_data[field]}")
        
        context_str = "\n".join(all_collected) if all_collected else "No information collected yet"
        
        is_complete = self.is_complete(extracted_data)
        
        # Check if we should ask for documents
        should_ask_documents = (
            is_complete and 
            (not extracted_data.get("documents") or len(extracted_data.get("documents", [])) == 0)
        )
        
        # Build status message (avoid backslash in f-string expression)
        if is_complete:
            status_msg = "✓ All required information has been collected!"
        else:
            missing_str = ", ".join(missing_fields)
            status_msg = f"Currently asking for: {current_question_field}\nStill need: {missing_str}"
        
        # Build newly collected message
        if newly_collected:
            newly_collected_msg = "Newly collected: " + ", ".join(newly_collected)
        else:
            newly_collected_msg = "No new information extracted"
        
        # Build document prompt if needed
        document_prompt = ""
        if should_ask_documents:
            claim_type = extracted_data.get("claim_type", "claim")
            document_suggestions = {
                "auto": "• Police report\n• Photos of damage\n• Repair estimates\n• Accident report",
                "health": "• Medical receipts\n• Hospital bills\n• Prescription forms\n• Lab reports",
                "home": "• Photos of damage\n• Repair invoices\n• Police report (if applicable)\n• Appraisal documents",
                "life": "• Death certificate\n• Medical records\n• Policy documents\n• Beneficiary information"
            }
            suggestions = document_suggestions.get(claim_type, "• Supporting documentation\n• Receipts\n• Official reports")
            document_prompt = f"\n\nIMPORTANT: After collecting all information, ask the user to upload supporting documents.\nFor {claim_type} claims, suggest:\n{suggestions}\n\nTell them they can upload files using the 📎 button or say 'skip' if they don't have documents right now."
        
        prompt = ChatPromptTemplate.from_messages([
            ("human", f"""You are a friendly, helpful AI Claims Assistant helping a customer submit an insurance claim.

Current collected information:
{context_str}

{status_msg}

User's latest message: "{user_message}"

{newly_collected_msg}

Your task:
1. Acknowledge what information was JUST provided (if any) - be specific
2. If information is complete but no documents uploaded, ask about documents{document_prompt}
3. If information is incomplete, naturally ask for the NEXT missing piece (currently: {current_question_field})
4. Be conversational, friendly, and brief
5. Don't repeat information unnecessarily
6. Ask ONE question at a time to avoid overwhelming the user

CRITICAL: If we're asking for "{current_question_field}" and the user provided a simple answer, acknowledge that you got it and move to the next question.

Guidelines:
- Keep responses SHORT (2-3 sentences max)
- Be natural and conversational
- Use emojis sparingly (✓ for confirmation)
- If user provided the information we asked for, acknowledge it clearly: "✓ Got your [field]!"
- Then immediately ask for the next missing field
- Don't ask for the same field twice if we just collected it
- If all info collected and documents uploaded, mention the submit button
- If user says "skip" for documents, acknowledge and proceed to submit

Generate your response:""")
        ])
        
        try:
            response = await self.llm.ainvoke(prompt.format_messages())
            response_text = response.content if hasattr(response, 'content') else str(response)
            return response_text.strip()
        except Exception as e:
            # Fallback response
            if is_complete:
                summary = self._format_summary(extracted_data)
                return f"✓ Perfect! I have all your information:\n\n{summary}\n\n**Ready to submit?** Click the 'Submit Claim' button below!"
            else:
                next_missing = missing_fields[0] if missing_fields else "information"
                return f"✓ Got it! Now, **what is your {next_missing.lower()}?**"
    
    async def process_message(
        self,
        user_message: str,
        collected_data: Dict[str, Any],
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user message using AI to extract information and generate natural responses
        
        Returns:
            Dict with response, collected_data, is_complete, ready_to_submit, etc.
        """
        
        # Check if user wants to start new claim
        start_keywords = ["new claim", "start", "begin", "submit claim", "file claim", "i want to file", "i need to file"]
        if any(keyword in user_message.lower() for keyword in start_keywords):
            return {
                "response": "👋 Great! I'll help you submit your claim. Let's start by gathering some information.\n\n**What's your policy number?**",
                "next_field": "policy_number",
                "collected_data": {"documents": []},  # Initialize documents list
                "is_complete": False,
                "ready_to_submit": False,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # If all fields collected, handle submission confirmation
        if self.is_complete(collected_data):
            if user_message.lower().strip() in ["yes", "submit", "confirm", "proceed", "go ahead"]:
                return {
                    "response": "Perfect! Your claim is ready. Click the 'Submit Claim' button below to submit.",
                    "next_field": None,
                    "collected_data": collected_data,
                    "is_complete": True,
                    "ready_to_submit": True,
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Show summary and prompt for submission
                summary = self._format_summary(collected_data)
                return {
                    "response": f"**Great! I have all your information:**\n\n{summary}\n\n**Ready to submit?** Click the 'Submit Claim' button below or type 'yes'.",
                    "next_field": None,
                    "collected_data": collected_data,
                    "is_complete": True,
                    "ready_to_submit": True,
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now().isoformat()
                }
        
        # Extract information from user's message using AI
        extracted_data = await self._extract_information(user_message, collected_data)
        
        # Generate natural response
        ai_response = await self._generate_response(user_message, collected_data, extracted_data)
        
        # Determine if complete
        is_complete = self.is_complete(extracted_data)
        
        # Determine next field (for tracking purposes)
        next_field = None
        if not is_complete:
            for field in self.REQUIRED_FIELDS:
                if field not in extracted_data or not extracted_data[field]:
                    next_field = field
                    break
        
        return {
            "response": ai_response,
            "next_field": next_field,
            "collected_data": extracted_data,
            "is_complete": is_complete,
            "ready_to_submit": is_complete,
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat()
        }
    
    def _format_summary(self, collected_data: Dict[str, Any]) -> str:
        """Format collected data as summary"""
        summary_parts = []
        for field in self.REQUIRED_FIELDS:
            if field == "documents":
                # Handle documents separately
                doc_count = len(collected_data.get("documents", [])) if isinstance(collected_data.get("documents"), list) else 0
                if doc_count > 0:
                    summary_parts.append(f"• Documents: {doc_count} file(s) uploaded")
            elif field in collected_data and collected_data[field] and field in self.FIELD_LABELS:
                label = self.FIELD_LABELS[field]
                value = collected_data[field]
                if field == "claim_amount":
                    summary_parts.append(f"• {label}: ${value:,.2f}")
                else:
                    summary_parts.append(f"• {label}: {value}")
        return "\n".join(summary_parts)
