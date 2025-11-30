import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class GroqLLMService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"
    
    async def ask_question(self, question: str, context: str) -> str:
        """Ask a question about the court session using LLM"""
        
        system_prompt = """You are a legal assistant AI helping judges analyze court proceedings.
You have access to the live transcript of the current session.
Answer questions accurately based only on the provided transcript.
If information is not in the transcript, clearly say so.
Be concise and professional."""
        
        user_prompt = f"""
COURT SESSION TRANSCRIPT:
{context if context else "No transcript available yet."}

QUESTION: {question}

Provide a clear, professional answer based on the transcript above.
"""
        
        try:
            # Use Groq's chat completion
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for factual responses
                max_tokens=500,
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            return f"Error processing question: {str(e)}"
    
    def summarize_session(self, transcript: str) -> str:
        """Generate a summary of the court session"""
        
        prompt = f"""
Summarize this court session transcript in a professional legal format:

TRANSCRIPT:
{transcript}

Provide:
1. Key arguments presented
2. Main evidence discussed
3. Important points raised
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a legal document summarizer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000,
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"Error generating summary: {str(e)}"