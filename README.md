# Nyaya-Sahayak Real-Time System

Real-time courtroom transcription and AI analysis system with WebSocket streaming.

## Architecture

### Backend (FastAPI + WebSockets)
- **Real-time audio streaming** to Deepgram
- **Live transcription** with speaker diarization
- **AI chat interface** using Groq LLM
- **WebSocket endpoints** for continuous communication

### Frontend (HTML + JavaScript)
- **Video conferencing interface** (Zoom-style)
- **Live caption display**
- **Real-time transcript updates**
- **AI chat panel**

## Setup Instructions

### 1. Install Dependencies

```powershell
cd nyaya-shayak
pip install -r backend/requirements.txt
```

### 2. Configure API Keys

Edit `.env` file with your keys:
```
DEEPGRAM_API_KEY=your_deepgram_key
GROQ_API_KEY=your_groq_key
```

### 3. Start Backend Server

**Option A: Using startup script**
```powershell
.\start_backend.ps1
```

**Option B: Manual start**
```powershell
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server will run on: `http://localhost:8000`

### 4. Open Frontend

Open `frontend/index.html` in your browser or serve it:

```powershell
# Using Python's HTTP server
cd frontend
python -m http.server 3000
```

Then navigate to: `http://localhost:3000`

## API Endpoints

### WebSocket Endpoints

#### `/ws/transcribe`
- **Purpose**: Real-time audio transcription
- **Flow**: 
  1. Frontend sends audio chunks
  2. Backend forwards to Deepgram
  3. Deepgram returns transcription
  4. Backend sends transcript to frontend

#### `/ws/chat`
- **Purpose**: AI Q&A about session
- **Flow**:
  1. Frontend sends question
  2. Backend queries LLM with transcript context
  3. Backend returns AI response

### REST Endpoints

#### `GET /`
- Health check
- Returns: `{"message": "Nyaya-Sahayak Backend Running"}`

#### `GET /transcript`
- Get full session transcript
- Returns: `{"transcript": [...]}`

#### `POST /clear`
- Clear session transcript
- Returns: `{"message": "Transcript cleared"}`

## How It Works

### Real-Time Transcription Flow

```
Browser Microphone
    ↓ (Audio Chunks)
Frontend WebSocket
    ↓
Backend FastAPI Server
    ↓
Deepgram Streaming API
    ↓ (Transcription)
Backend Processing
    ↓ (JSON)
Frontend Display (Live Captions)
```

### AI Chat Flow

```
User Question
    ↓
Frontend → Backend
    ↓
Context: Session Transcript
    ↓
Groq LLM (Llama 3.3 70B)
    ↓
AI Response
    ↓
Frontend Display
```

## Features

### ✅ Implemented
- [x] Real-time audio streaming
- [x] Live transcription with WebSockets
- [x] Speaker diarization
- [x] Interim results (real-time captions)
- [x] Final transcripts with timestamps
- [x] AI chat with session context
- [x] Transcript storage
- [x] Multiple participant support
- [x] Auto-formatting and punctuation

### 🔧 Configuration Options

**Deepgram Settings** (in `deepgram_service.py`):
- `model`: "nova-2" (latest model)
- `language`: "en-IN" (English + Hindi)
- `smart_format`: Auto-formatting
- `interim_results`: Real-time partial results
- `diarize`: Speaker identification
- `sample_rate`: 16000 Hz

**LLM Settings** (in `llm_service.py`):
- `model`: "llama-3.3-70b-versatile"
- `temperature`: 0.3 (factual responses)
- `max_tokens`: 500 per response

## Frontend Features

### Video Interface
- Multi-participant grid layout
- Active speaker highlighting
- Participant name labels
- Camera/Mic toggle controls

### Live Captions
- Real-time caption display
- Speaker identification
- Timestamp tracking
- Auto-scroll

### Transcript Panel
- Full session log
- Searchable content
- Export functionality
- AI chat interface

## Usage

### Starting a Session

1. **Start Backend**: Run `start_backend.ps1`
2. **Open Frontend**: Open `index.html` in browser
3. **Grant Permissions**: Allow microphone access
4. **Start Recording**: Click mic button
5. **Speak**: Audio streams automatically
6. **View Captions**: Real-time captions appear
7. **Ask Questions**: Use AI chat panel

### Example AI Questions

- "What did Speaker 1 say about the incident?"
- "Summarize the key points discussed"
- "Are there any contradictions in the testimonies?"
- "What evidence was mentioned?"

## Troubleshooting

### Backend won't start
- Check Python version (requires 3.8+)
- Install dependencies: `pip install -r backend/requirements.txt`
- Verify API keys in `.env` file

### No transcription appearing
- Check Deepgram API key is valid
- Verify microphone permissions in browser
- Check browser console for WebSocket errors
- Ensure backend is running on port 8000

### WebSocket connection fails
- Backend must be running first
- Check CORS is enabled (already configured)
- Verify WebSocket URL in frontend code
- Check firewall settings

### AI chat not responding
- Verify Groq API key in `.env`
- Check transcript has content
- Look for errors in backend logs
- Ensure model name is correct

## Development

### File Structure

```
nyaya-shayak/
├── backend/
│   ├── main.py              # FastAPI app & WebSocket handlers
│   ├── deepgram_service.py  # Deepgram streaming client
│   ├── llm_service.py       # Groq LLM integration
│   └── requirements.txt     # Python dependencies
├── frontend/
│   └── index.html          # Web interface
├── .env                     # API keys (gitignored)
├── start_backend.ps1       # Startup script
└── README.md               # This file
```

### Adding New Features

**Add a new WebSocket endpoint**:
```python
@app.websocket("/ws/new_feature")
async def new_feature(websocket: WebSocket):
    await websocket.accept()
    # Your logic here
```

**Modify transcription options**:
Edit `deepgram_service.py` → `LiveOptions` parameters

**Change LLM model**:
Edit `llm_service.py` → `self.model` variable

## Performance

- **Latency**: ~500ms for transcription
- **Accuracy**: 95%+ for clear audio
- **Concurrent Users**: Supports multiple WebSocket connections
- **Throughput**: Real-time audio processing

## Security Notes

- API keys are in `.env` (not committed to git)
- CORS is open for development (restrict in production)
- WebSocket connections are not authenticated (add auth for production)
- Session data is in-memory (use database for persistence)

## Production Deployment

### Recommendations

1. **Add Authentication**: Implement JWT tokens for WebSocket auth
2. **Use Database**: Store transcripts in PostgreSQL/MongoDB
3. **Add SSL**: Use HTTPS and WSS (secure WebSocket)
4. **Restrict CORS**: Whitelist specific origins
5. **Load Balancing**: Use nginx for multiple instances
6. **Logging**: Add structured logging with timestamps
7. **Monitoring**: Track WebSocket connections and latency

### Environment Variables (Production)

```
DEEPGRAM_API_KEY=production_key
GROQ_API_KEY=production_key
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=random_secret_key
ALLOWED_ORIGINS=https://yourdomain.com
```

## License

Proprietary - Nyaya-Sahayak System

## Support

For issues or questions, check backend logs:
```powershell
# Backend logs show in terminal
cd backend
uvicorn main:app --reload --log-level debug
```

---

**Status**: ✅ All systems operational
**Last Updated**: November 29, 2025
