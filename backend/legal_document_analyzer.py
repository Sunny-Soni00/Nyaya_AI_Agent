"""
Legal Document Analyzer Service
Analyzes legal documents and provides simplified summaries using Groq AI
"""

import os
from typing import Dict, List, Optional
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LegalDocumentAnalyzer:
    def __init__(self):
        """Initialize the Legal Document Analyzer with Groq client"""
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            print("Warning: GROQ_API_KEY not found. Legal document analysis will not work.")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
    
    def analyze_document(self, content: str) -> Dict:
        """
        Analyze a legal document and return simplified summary with color-coded highlights
        
        Args:
            content: The legal document text to analyze
            
        Returns:
            Dictionary containing:
            - summary: Color-coded summary with [CRITICAL:], [AMOUNT:], [DATE:] tags
            - colorCodedOriginalText: Original text with color coding
            - keyPoints: List of key points
            - extraInfo: Additional information
            - wordHelper: List of difficult terms with definitions
            - verifiableClaims: Claims that can be verified with links
        """
        
        system_prompt = """You are an expert Legal Document Analyzer AI. Your task is to analyze legal documents and make them easy to understand for common people.

Your analysis should:
1. Identify critical information (warnings, restrictions, penalties) and tag with [CRITICAL:text]
2. Identify monetary amounts and tag with [AMOUNT:text]
3. Identify dates and deadlines and tag with [DATE:text]
4. Extract key points that a person MUST know
5. Provide simple definitions for legal terminology
6. Identify verifiable legal claims

You MUST respond with ONLY a valid JSON object (no markdown, no code blocks) with this exact structure:
{
    "summary": "Brief summary with [CRITICAL:], [AMOUNT:], [DATE:] tags",
    "colorCodedOriginalText": "Full document text with color coding tags",
    "keyPoints": ["Point 1", "Point 2", "Point 3"],
    "extraInfo": ["Additional info 1", "Additional info 2"],
    "wordHelper": [
        {"term": "Legal Term", "simpleDefinition": "Simple explanation", "detailedDefinition": "Detailed explanation"}
    ],
    "verifiableClaims": [
        {"claim": "Legal claim or reference", "link": "https://google.com/search?q=relevant+search"}
    ]
}

Make everything clear and simple. Use Indian legal context when relevant."""

        user_prompt = f"""Analyze the following legal document and provide a comprehensive breakdown:

DOCUMENT:
\"\"\"
{content}
\"\"\"

Respond with ONLY the JSON object, no other text."""

        if not self.client:
            raise Exception("Groq API client not initialized. Check GROQ_API_KEY.")

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            import json
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            # Add original text for Q&A later
            result['originalText'] = content
            
            return result
            
        except Exception as e:
            print(f"Error analyzing document: {str(e)}")
            raise Exception(f"Failed to analyze document: {str(e)}")
    
    def answer_question(self, question: str, document_text: str) -> Dict:
        """
        Answer a question about the analyzed document
        
        Args:
            question: User's question
            document_text: Original document text
            
        Returns:
            Dictionary with answer and suggestions
        """
        
        system_prompt = """You are a helpful legal document assistant. Answer questions about legal documents in simple, clear language. 
Provide accurate answers based on the document content. If something is not in the document, say so clearly.

Respond with ONLY a valid JSON object (no markdown, no code blocks):
{
    "answer": "Clear answer to the question",
    "suggestions": ["Related question 1?", "Related question 2?"]
}"""

        user_prompt = f"""Based on this document, answer the question:

DOCUMENT:
\"\"\"
{document_text}
\"\"\"

QUESTION: {question}

Respond with ONLY the JSON object."""

        if not self.client:
            raise Exception("Groq API client not initialized. Check GROQ_API_KEY.")

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model,
                temperature=0.2,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Error answering question: {str(e)}")
            raise Exception(f"Failed to answer question: {str(e)}")


# Global instance
legal_document_analyzer = LegalDocumentAnalyzer()
