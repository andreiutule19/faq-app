from typing import Optional
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from app.core.settings import settings
import logging

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=settings.openai_api_key,
            temperature=0.7
        )
    
    async def get_answer(self, user_question: str, context: Optional[str] = None) -> str:
        try:
            system_message = SystemMessage(content="""
            You are a helpful IT support assistant. Answer user questions about account management, 
            password resets, profile settings, and general IT support topics. Answer only if you know the answer, don't guess.
            Be concise and provide actionable steps when possible.
            If you don't know the answer or the question is not related to IT support, politely redirect the user with "I'm not sure, please contact IT support! ".
            """)
            
            human_message = HumanMessage(content=user_question)
            
            if context:
                human_message.content = f"Context: {context}\n\nQuestion: {user_question}"
            
            response = await self.llm.ainvoke([system_message, human_message])
            return response.content
            
        except Exception as e:
            logger.error(f"Error getting OpenAI response: {e}")
            return "I'm sorry, I'm having trouble processing your request right now. Please try again later."