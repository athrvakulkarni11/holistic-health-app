"""
Chat Engine — Direct conversational AI interface for health queries.
Maintains conversation history and uses knowledge base + web search for
evidence-based responses. Supports file context injection.
"""
import json
import re
import uuid
from datetime import datetime
from groq import Groq
from app.config import GROQ_API_KEY, GROQ_MODEL
from app.knowledge_base import KnowledgeBaseService
from app.web_search import WebSearchService


class ChatSession:
    """Represents a single chat conversation with history."""

    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.messages: list[dict] = []
        self.created_at = datetime.now().isoformat()
        self.file_context: str = ""  # Text from uploaded files

    def add_message(self, role: str, content: str):
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })

    def get_groq_messages(self) -> list[dict]:
        """Return messages in Groq-compatible format (only role + content)."""
        return [{"role": m["role"], "content": m["content"]} for m in self.messages]

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "message_count": len(self.messages),
            "messages": self.messages,
        }


class ChatEngine:
    """Handles direct conversational health AI interactions."""

    SYSTEM_PROMPT = """You are HolisticAI, an expert health assistant specialized in biomarker analysis, nutrition, and wellness.

You are NOT a doctor. Always recommend consulting healthcare professionals for medical decisions.

Your capabilities:
1. Analyze biomarker values and explain what they mean
2. Provide evidence-based dietary and lifestyle recommendations
3. Explain health conditions, symptoms, and management
4. Discuss supplement interactions and safety
5. Help interpret lab reports
6. Answer general health and wellness questions

Guidelines:
- Be comprehensive yet easy to understand
- Always cite evidence or explain the basis for your recommendations
- Use the knowledge base and web search context provided to you
- Be empathetic and supportive
- If you are uncertain, say so clearly
- Include appropriate disclaimers for medical advice
- Format your responses with clear sections and bullet points when helpful
- If a user shares a file or lab report data, analyze it thoroughly

When lab data or file context is provided, proactively analyze all values and flag anything abnormal."""

    def __init__(self):
        self.groq_client = None
        if GROQ_API_KEY:
            self.groq_client = Groq(api_key=GROQ_API_KEY)

        self.kb = KnowledgeBaseService()
        self.web_search = WebSearchService()
        self.sessions: dict[str, ChatSession] = {}

    def get_or_create_session(self, session_id: str = None) -> ChatSession:
        """Get an existing session or create a new one."""
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]

        session = ChatSession(session_id)
        self.sessions[session.session_id] = session
        return session

    def _gather_context(self, user_message: str) -> str:
        """Search knowledge base and web for relevant context."""
        context_parts = []

        # Knowledge base search
        kb_results = self.kb.search(user_message, n_results=3)
        if kb_results:
            kb_text = "\n".join([
                f"• {r['metadata'].get('biomarker', 'Info')}: {r['content'][:300]}"
                for r in kb_results
            ])
            context_parts.append(f"**Medical Knowledge Base:**\n{kb_text}")

        # Web search for current information
        web_results = self.web_search.search_general(user_message)
        if web_results:
            web_text = "\n".join([
                f"• [{r['title']}]({r['url']}): {r['body']}"
                for r in web_results[:3]
            ])
            context_parts.append(f"**Latest Web Research:**\n{web_text}")

        return "\n\n".join(context_parts) if context_parts else ""

    def _check_safety(self, message: str) -> str:
        """
        Check for emergency keywords and return a safety intervention message if needed.
        Returns None if no safety intervention is required.
        """
        emergency_keywords = [
            "suicide", "kill myself", "want to die", "end my life",
            "heart attack", "chest pain", "stroke", "difficulty breathing",
            "call 911", "emergency", "overdose", "bleeding profusely"
        ]
        
        message_lower = message.lower()
        for keyword in emergency_keywords:
            if keyword in message_lower:
                return (
                    "**⚠️ MEDICAL EMERGENCY WARNING**\n\n"
                    "It sounds like you may be experiencing a medical emergency or crisis. "
                    "**I am an AI, not a doctor, and I cannot help in emergencies.**\n\n"
                    "Please take immediate action:\n"
                    "- **Call 911** or your local emergency number immediately.\n"
                    "- Go to the nearest emergency room.\n"
                    "- If you are in mental health crisis, call or text **988** (Suicide & Crisis Lifeline).\n\n"
                    "Your safety is the most important thing right now. Please get professional help immediately."
                )
        return None

    def chat(self, session_id: str, user_message: str, file_text: str = None) -> dict:
        """
        Process a chat message and return AI response.
        Optionally includes file context from uploaded documents.
        """
        if not self.groq_client:
            return {
                "session_id": session_id or "error",
                "response": "Chat is unavailable — GROQ_API_KEY is not configured.",
                "error": True,
            }

        session = self.get_or_create_session(session_id)

        # If file text is provided, add it as context
        if file_text:
            session.file_context = file_text
            context_note = f"\n\n[The user has uploaded a file. Here is the extracted content:\n{file_text[:4000]}\n--- End of file content ---]"
            enriched_message = user_message + context_note
        else:
            enriched_message = user_message

        # Gather external context
        external_context = self._gather_context(user_message)

        # Build the full user message with context
        full_message = enriched_message
        if external_context:
            full_message += f"\n\n[REFERENCE CONTEXT - Use this to provide accurate information:]\n{external_context}"

        # 🚨 SAFETY CHECK INTERCEPTION 🚨
        safety_response = self._check_safety(user_message)
        if safety_response:
             # Add to history so user sees it
            session.add_message("user", user_message)
            session.add_message("assistant", safety_response)
            return {
                "session_id": session.session_id,
                "response": safety_response,
                "error": False,
                "sources_used": False,
            }

        # Add to session history
        session.add_message("user", user_message)  # Store original for display

        # Build messages for Groq
        groq_messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

        # Add file context reminder if it exists
        if session.file_context:
            groq_messages.append({
                "role": "system",
                "content": f"The user previously uploaded a file with this content (use for reference):\n{session.file_context[:2000]}"
            })

        # Add history (last 10 messages for context window management)
        history = session.get_groq_messages()
        if len(history) > 10:
            history = history[-10:]

        # Replace the last user message with the enriched version
        for msg in history[:-1]:
            groq_messages.append(msg)
        groq_messages.append({"role": "user", "content": full_message})

        try:
            response = self.groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=groq_messages,
                temperature=0.4,
                max_tokens=4096,
            )
            assistant_message = response.choices[0].message.content

            # Store assistant response in session
            session.add_message("assistant", assistant_message)

            return {
                "session_id": session.session_id,
                "response": assistant_message,
                "error": False,
                "sources_used": bool(external_context),
            }

        except Exception as e:
            error_msg = f"I encountered an error processing your request: {str(e)}"
            session.add_message("assistant", error_msg)
            return {
                "session_id": session.session_id,
                "response": error_msg,
                "error": True,
            }

    def get_session_history(self, session_id: str) -> dict:
        """Get the message history for a session."""
        if session_id in self.sessions:
            return self.sessions[session_id].to_dict()
        return {"error": "Session not found"}

    def clear_session(self, session_id: str) -> dict:
        """Clear a chat session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return {"status": "cleared"}
        return {"error": "Session not found"}
