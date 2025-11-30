import os
import requests
from dotenv import load_dotenv
import asyncio
import json

load_dotenv()


class DeepgramTranscriber:
    def __init__(self):
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPGRAM_API_KEY not found in environment")
        
        self.ws_url = "wss://api.deepgram.com/v1/listen"
        self.connection = None
    
    async def connect(self):
        """Establish connection to Deepgram streaming API using websockets"""
        import websockets
        
        # Build query parameters - optimized for better Hindi-English transcription
        params = {
            "model": "nova-2",
            "language": "hi",  # Hindi for better Hinglish transcription
            "smart_format": "true",
            "interim_results": "true",
            "punctuate": "true",
            "diarize": "false",
            "encoding": "linear16",
            "sample_rate": "16000",
            "endpointing": "500",  # Longer endpoint detection for continuous speech
            "utterance_end_ms": "2000",  # Wait 2 seconds of silence before finalizing
            "vad_events": "true",
            "filler_words": "false"  # Remove filler words
        }
        
        # Build URL with parameters
        url_params = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{self.ws_url}?{url_params}"
        
        # Connect with authorization header (correct syntax)
        self.connection = await websockets.connect(
            full_url,
            additional_headers={"Authorization": f"Token {self.api_key}"},
            ping_interval=20,  # Send ping every 20 seconds
            ping_timeout=30,   # Wait 30 seconds for pong response
            close_timeout=10   # Timeout for close handshake
        )
        
        print("✅ Deepgram WebSocket connection established")
        return self.connection
    
    async def close(self):
        """Close Deepgram connection"""
        if self.connection:
            await self.connection.close()
            print("❌ Deepgram connection closed")
    
    def transcribe_file(self, audio_data, filename="audio"):
        """Transcribe audio file (non-streaming) - for uploaded audio files"""
        url = "https://api.deepgram.com/v1/listen"
        
        # Detect content type from filename
        content_type = "audio/wav"
        if filename.lower().endswith('.mp3'):
            content_type = "audio/mpeg"
        elif filename.lower().endswith('.m4a'):
            content_type = "audio/mp4"
        elif filename.lower().endswith('.ogg'):
            content_type = "audio/ogg"
        elif filename.lower().endswith('.webm'):
            content_type = "audio/webm"
        
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": content_type
        }
        params = {
            "model": "nova-2",
            "language": "hi",  # Hindi for better Hinglish
            "smart_format": "true",
            "diarize": "true",
            "punctuate": "true",
            "paragraphs": "true",
            "utterances": "true"
        }
        
        response = requests.post(url, headers=headers, params=params, data=audio_data)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Deepgram API error: {response.status_code} - {response.text}")