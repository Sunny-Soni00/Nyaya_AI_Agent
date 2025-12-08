from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
import json
import asyncio
from datetime import datetime
from typing import List, Dict
from io import BytesIO
from deepgram_service import DeepgramTranscriber
from llm_service import GroqLLMService
from evidence_service import EvidenceManager
from meeting_service import MeetingManager
from criminal_records_service import criminal_records_manager
from report_service import report_generator
from legal_document_analyzer import legal_document_analyzer

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store transcripts in memory (for demo - backward compatibility)
session_transcript = []
llm_service = GroqLLMService()
evidence_manager = EvidenceManager()

# Meeting system (new)
meeting_manager = MeetingManager()

# Store WebSocket connections per meeting
meeting_connections: Dict[str, Dict[str, WebSocket]] = {}

# Store WebRTC signaling connections
signaling_connections: Dict[str, Dict[str, WebSocket]] = {}


@app.get("/")
async def root():
    return {"message": "Nyaya-Sahayak Backend Running"}


# ============ MEETING ENDPOINTS (NEW) ============

@app.post("/auth/login")
async def login(data: dict):
    """Create a new user session"""
    name = data.get("name", "").strip()
    role = data.get("role", "Observer").strip()
    if not name:
        return JSONResponse(
            status_code=400,
            content={"error": "Name is required"}
        )
    
    user = meeting_manager.create_user(name, role)
    return {
        "user_id": user.user_id,
        "name": user.name,
        "role": user.role,
        "message": f"Welcome, {name}!"
    }


@app.post("/meeting/create")
async def create_meeting(data: dict):
    """Create a new meeting"""
    user_id = data.get("user_id")
    
    user = meeting_manager.get_user(user_id)
    if not user:
        return JSONResponse(
            status_code=404,
            content={"error": "User not found. Please login first."}
        )
    
    meeting = meeting_manager.create_meeting(user)
    
    # Initialize meeting connections dict
    meeting_connections[meeting.meeting_id] = {}
    
    return {
        "meeting_id": meeting.meeting_id,
        "host_name": meeting.host_name,
        "created_at": meeting.created_at.isoformat(),
        "message": f"Meeting {meeting.meeting_id} created successfully"
    }


@app.post("/meeting/join")
async def join_meeting(data: dict):
    """Join an existing meeting"""
    meeting_id = data.get("meeting_id", "").strip().upper()
    user_id = data.get("user_id")
    
    if not meeting_id:
        return JSONResponse(
            status_code=400,
            content={"error": "Meeting ID is required"}
        )
    
    user = meeting_manager.get_user(user_id)
    if not user:
        return JSONResponse(
            status_code=404,
            content={"error": "User not found. Please login first."}
        )
    
    meeting = meeting_manager.join_meeting(meeting_id, user)
    if not meeting:
        return JSONResponse(
            status_code=404,
            content={"error": f"Meeting {meeting_id} not found or inactive"}
        )
    
    return {
        "meeting_id": meeting.meeting_id,
        "host_name": meeting.host_name,
        "participants": meeting.get_participant_list(),
        "message": f"{user.name} joined meeting {meeting_id}"
    }


@app.get("/meeting/{meeting_id}")
async def get_meeting_info(meeting_id: str):
    """Get meeting information"""
    meeting = meeting_manager.get_meeting(meeting_id.upper())
    if not meeting:
        return JSONResponse(
            status_code=404,
            content={"error": "Meeting not found"}
        )
    
    return meeting.to_dict()


@app.get("/meeting/{meeting_id}/participants")
async def get_participants(meeting_id: str):
    """Get list of participants in meeting"""
    meeting_id_upper = meeting_id.upper()
    meeting = meeting_manager.get_meeting(meeting_id_upper)
    if not meeting:
        print(f"⚠️ Meeting {meeting_id_upper} not found. Active meetings: {list(meeting_manager.meetings.keys())}")
        return JSONResponse(
            status_code=404,
            content={"error": f"Meeting {meeting_id_upper} not found. Please create or join a meeting first."}
        )
    
    return {
        "meeting_id": meeting.meeting_id,
        "participants": meeting.get_participant_list()
    }


@app.get("/meeting/{meeting_id}/transcript")
async def get_meeting_transcript(meeting_id: str):
    """Get meeting transcript"""
    meeting = meeting_manager.get_meeting(meeting_id.upper())
    if not meeting:
        return JSONResponse(
            status_code=404,
            content={"error": "Meeting not found"}
        )
    
    return {
        "meeting_id": meeting.meeting_id,
        "transcript": meeting.transcript
    }


@app.post("/meeting/{meeting_id}/leave")
async def leave_meeting(meeting_id: str, data: dict):
    """Leave a meeting"""
    user_id = data.get("user_id")
    meeting = meeting_manager.get_meeting(meeting_id.upper())
    
    if meeting and user_id:
        meeting.remove_participant(user_id)
        return {"message": "Left meeting successfully"}
    
    return JSONResponse(
        status_code=404,
        content={"error": "Meeting or user not found"}
    )


# ============ ORIGINAL ENDPOINTS (KEPT FOR BACKWARD COMPATIBILITY) ============

@app.websocket("/ws/transcribe/{meeting_id}/{user_id}")
async def websocket_transcribe(websocket: WebSocket, meeting_id: str, user_id: str):
    await websocket.accept()
    meeting_id = meeting_id.upper()
    
    # Get meeting and user info
    meeting = meeting_manager.get_meeting(meeting_id)
    user = meeting_manager.get_user(user_id)
    
    if not meeting or not user:
        await websocket.close(code=4004, reason="Meeting or user not found")
        return
    
    transcriber = DeepgramTranscriber()
    
    try:
        print(f"🎤 WebSocket connected - Starting transcription for {user.name} in {meeting_id}...")
        
        # Start Deepgram connection
        deepgram_ws = await transcriber.connect()
        
        # Task to receive audio from frontend and send to Deepgram
        async def forward_audio():
            audio_received = False
            try:
                while True:
                    # Receive audio data from frontend
                    data = await websocket.receive_bytes()
                    
                    if not audio_received:
                        audio_received = True
                        print("🎵 Audio stream started")
                    
                    # Forward to Deepgram (check connection state)
                    try:
                        await deepgram_ws.send(data)
                    except Exception as send_error:
                        print(f"⚠️ Cannot send to Deepgram: {send_error}")
                        break
            except WebSocketDisconnect:
                print("Frontend disconnected")
            except Exception as e:
                print(f"Error forwarding audio: {e}")
        
        # Task to receive transcriptions from Deepgram and send to frontend
        async def receive_transcriptions():
            try:
                async for message in deepgram_ws:
                    transcript_data = json.loads(message)
                    
                    # Debug: Print structure to understand response format
                    # print(f"DEBUG: {json.dumps(transcript_data, indent=2)}")
                    
                    # Check if this contains a channel result
                    if "channel" in transcript_data:
                        channel = transcript_data["channel"]
                        
                        # Get alternatives
                        if "alternatives" in channel and len(channel["alternatives"]) > 0:
                            alternative = channel["alternatives"][0]
                            text = alternative.get("transcript", "")
                            is_final = transcript_data.get("is_final", False)
                            
                            if text.strip():
                                if is_final:
                                    # Store transcript with timestamp and speaker name
                                    entry = {
                                        "timestamp": datetime.now().isoformat(),
                                        "speaker": user.name,
                                        "user_id": user_id,
                                        "text": text
                                    }
                                    # Add to meeting transcript
                                    meeting.add_transcript_entry(entry)
                                    # Also add to global session_transcript for backward compatibility
                                    session_transcript.append(entry)
                                    
                                    # Broadcast to all participants in the meeting
                                    broadcast_message = {
                                        "type": "transcript",
                                        "data": entry
                                    }
                                    
                                    # Send to all signaling connections in this meeting
                                    if meeting_id in signaling_connections:
                                        for participant_id, ws in signaling_connections[meeting_id].items():
                                            try:
                                                await ws.send_json(broadcast_message)
                                            except:
                                                pass
                                    
                                    print(f"📝 Transcript ({user.name}): {text}")
                                else:
                                    # Send interim results
                                    await websocket.send_json({
                                        "type": "interim",
                                        "data": {"text": text}
                                    })
            
            except Exception as e:
                error_msg = str(e)
                if "keepalive ping timeout" in error_msg or "ConnectionClosedError" in str(type(e)):
                    print("⚠️ Deepgram connection timed out (likely no audio received)")
                    # Send notification to frontend
                    try:
                        await websocket.send_json({
                            "type": "warning",
                            "message": "No voice detected. Please speak into the microphone."
                        })
                    except:
                        pass
                else:
                    print(f"Error receiving transcriptions: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Run both tasks concurrently
        try:
            await asyncio.gather(
                forward_audio(),
                receive_transcriptions(),
                return_exceptions=True  # Don't crash if one task fails
            )
        except Exception as e:
            print(f"⚠️ Transcription session error: {e}")
    
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await transcriber.close()


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """Chat interface for asking questions about the session"""
    await websocket.accept()
    
    try:
        while True:
            # Receive question from frontend
            data = await websocket.receive_json()
            question = data.get("question", "")
            
            print(f"💬 Question: {question}")
            
            # Prepare context from session transcript
            transcript_context = "\n".join([
                f"[{entry['timestamp']}] {entry['speaker']}: {entry['text']}"
                for entry in session_transcript
            ])
            
            # Get relevant evidence
            evidence_context = ""
            if evidence_manager.vector_store:
                evidence_results = evidence_manager.search_evidence(question, k=3)
                if evidence_results:
                    evidence_context = "\n\nRELEVANT EVIDENCE:\n"
                    for i, result in enumerate(evidence_results, 1):
                        evidence_context += f"\n[Evidence {i} from {result['filename']}]:\n{result['content']}\n"
            
            # Combine all context
            full_context = transcript_context + evidence_context
            
            # Get response from LLM
            response = await llm_service.ask_question(question, full_context)
            
            # Send response back to frontend
            await websocket.send_json({
                "type": "answer",
                "data": {
                    "question": question,
                    "answer": response
                }
            })
            
            print(f"🤖 Answer: {response}")
    
    except WebSocketDisconnect:
        print("Chat WebSocket disconnected")
    except Exception as e:
        print(f"Chat error: {e}")


@app.websocket("/ws/signaling/{meeting_id}/{user_id}")
async def websocket_signaling(websocket: WebSocket, meeting_id: str, user_id: str):
    """WebRTC signaling for peer-to-peer video connections"""
    meeting_id = meeting_id.upper()
    await websocket.accept()
    
    # Initialize meeting signaling room if not exists
    if meeting_id not in signaling_connections:
        signaling_connections[meeting_id] = {}
    
    # Add this user's connection
    signaling_connections[meeting_id][user_id] = websocket
    print(f"📹 User {user_id} connected to signaling for meeting {meeting_id}")
    
    # Notify user of all existing participants
    existing_users = [uid for uid in signaling_connections[meeting_id].keys() if uid != user_id]
    if existing_users:
        await websocket.send_json({
            "type": "existing_participants",
            "user_ids": existing_users
        })
    
    # Notify all other participants about the new user
    for uid, ws in signaling_connections[meeting_id].items():
        if uid != user_id:
            try:
                await ws.send_json({
                    "type": "new_participant",
                    "user_id": user_id
                })
            except:
                pass
    
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            target_user_id = data.get("target_user_id")
            
            # Forward signaling messages to target user
            if target_user_id and target_user_id in signaling_connections[meeting_id]:
                try:
                    await signaling_connections[meeting_id][target_user_id].send_json({
                        "type": message_type,
                        "from_user_id": user_id,
                        "data": data.get("data")
                    })
                except Exception as e:
                    print(f"Error forwarding signaling message: {e}")
    
    except WebSocketDisconnect:
        print(f"📹 User {user_id} disconnected from signaling")
    except Exception as e:
        print(f"Signaling error: {e}")
    finally:
        # Remove user from signaling connections
        if meeting_id in signaling_connections and user_id in signaling_connections[meeting_id]:
            del signaling_connections[meeting_id][user_id]
        
        # Notify other participants about user leaving
        if meeting_id in signaling_connections:
            for uid, ws in signaling_connections[meeting_id].items():
                try:
                    await ws.send_json({
                        "type": "participant_left",
                        "user_id": user_id
                    })
                except:
                    pass


@app.get("/transcript")
async def get_transcript():
    """Get full session transcript"""
    return {"transcript": session_transcript}


@app.post("/clear")
async def clear_transcript():
    """Clear session transcript"""
    session_transcript.clear()
    return {"message": "Transcript cleared"}


@app.post("/evidence/upload")
async def upload_evidence(files: List[UploadFile] = File(...)):
    """Upload multiple evidence files (PDF, images, or audio)"""
    try:
        processed_files = []
        
        for file in files:
            # Validate file type
            file_ext = file.filename.lower().split('.')[-1]
            
            # Read file content
            content = await file.read()
            
            # Check if audio file
            if file_ext in ['mp3', 'wav', 'm4a', 'ogg', 'webm']:
                # Transcribe audio file
                print(f"🎵 Transcribing audio: {file.filename}...")
                transcriber = DeepgramTranscriber()
                transcript_result = transcriber.transcribe_file(content, file.filename)
                
                # Extract transcript text
                transcript_text = ""
                if "results" in transcript_result and "channels" in transcript_result["results"]:
                    channels = transcript_result["results"]["channels"]
                    if len(channels) > 0 and "alternatives" in channels[0]:
                        alternatives = channels[0]["alternatives"]
                        if len(alternatives) > 0:
                            transcript_text = alternatives[0].get("transcript", "")
                
                if transcript_text:
                    # Add to evidence manager
                    num_chunks = evidence_manager.add_audio_transcript(
                        file.filename, 
                        transcript_text,
                        transcript_result
                    )
                    processed_files.append({
                        "filename": file.filename,
                        "type": "audio",
                        "chunks": num_chunks,
                        "has_transcript": True
                    })
                    print(f"🎵 Audio transcribed: {file.filename} ({num_chunks} chunks)")
                else:
                    processed_files.append({
                        "filename": file.filename,
                        "type": "audio",
                        "chunks": 0,
                        "has_transcript": False,
                        "error": "No transcript generated"
                    })
            
            elif file_ext in ['pdf', 'jpg', 'jpeg', 'png', 'bmp', 'tiff']:
                # Process document/image
                num_chunks = evidence_manager.process_file(content, file.filename, "document")
                processed_files.append({
                    "filename": file.filename,
                    "type": "document",
                    "chunks": num_chunks
                })
                print(f"📄 Processed: {file.filename} ({num_chunks} chunks)")
            else:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Unsupported file type: {file.filename}"}
                )
        
        # Build vector store
        evidence_manager.build_vector_store()
        
        return {
            "message": f"Successfully processed {len(files)} evidence file(s)",
            "files": processed_files,
            "total_documents": len(evidence_manager.documents)
        }
    
    except Exception as e:
        print(f"❌ Error uploading evidence: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/evidence")
async def get_evidence():
    """Get list of all uploaded evidence"""
    filenames = list(set([doc["filename"] for doc in evidence_manager.documents]))
    
    # Add file type info
    file_list = []
    for filename in filenames:
        file_ext = filename.lower().split('.')[-1]
        is_audio = file_ext in ['mp3', 'wav', 'm4a', 'ogg', 'webm']
        file_list.append({
            "filename": filename,
            "type": "audio" if is_audio else "document",
            "has_transcript": filename in evidence_manager.audio_transcripts
        })
    
    return {
        "files": file_list,
        "total_chunks": len(evidence_manager.documents)
    }


@app.get("/evidence/transcript/{filename}")
async def get_audio_transcript(filename: str):
    """Get transcript for a specific audio file"""
    transcript = evidence_manager.get_audio_transcript(filename)
    if transcript:
        return {
            "filename": filename,
            "transcript": transcript["text"],
            "data": transcript.get("data")
        }
    else:
        return JSONResponse(
            status_code=404,
            content={"error": "Transcript not found"}
        )


@app.get("/evidence/download/{filename}")
async def download_evidence(filename: str):
    """Download an evidence file"""
    if filename not in evidence_manager.file_storage:
        return JSONResponse(
            status_code=404,
            content={"error": "File not found"}
        )
    
    file_data = evidence_manager.file_storage[filename]
    file_content = file_data["content"]
    file_ext = file_data["extension"]
    
    # Determine MIME type
    mime_types = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "bmp": "image/bmp",
        "tiff": "image/tiff",
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "m4a": "audio/mp4",
        "ogg": "audio/ogg",
        "webm": "audio/webm"
    }
    
    media_type = mime_types.get(file_ext, "application/octet-stream")
    
    return StreamingResponse(
        BytesIO(file_content),
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@app.post("/clear-evidence")
async def clear_evidence():
    """Clear all evidence"""
    evidence_manager.clear_evidence()
    return {"message": "Evidence cleared"}


@app.delete("/evidence/{filename}")
async def delete_evidence(filename: str):
    """Delete a specific evidence file"""
    try:
        # Remove documents with matching filename
        evidence_manager.documents = [
            doc for doc in evidence_manager.documents 
            if doc["filename"] != filename
        ]
        
        # Remove audio transcript if exists
        if filename in evidence_manager.audio_transcripts:
            del evidence_manager.audio_transcripts[filename]
        
        # Rebuild vector store if documents remain
        if evidence_manager.documents:
            evidence_manager.build_vector_store()
        else:
            evidence_manager.vector_store = None
        
        return {"message": f"Deleted {filename}"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/search-evidence")
async def search_evidence(query: dict):
    """Search evidence for relevant information"""
    q = query.get("query", "")
    if not q:
        return {"error": "Query is required"}
    
    results = evidence_manager.search_evidence(q, k=5)
    return {"results": results}


# ============ CRIMINAL RECORDS ENDPOINTS ============

@app.get("/criminal-records")
async def get_criminal_records():
    """Get all criminal records"""
    try:
        records = criminal_records_manager.get_all_records()
        return {
            "records": records,
            "total": len(records),
            "flagged": len(criminal_records_manager.get_flagged_records())
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/criminal-records/search/{name}")
async def search_criminal_record(name: str):
    """Search for a criminal record by name"""
    try:
        record = criminal_records_manager.search_by_name(name)
        if record:
            return {"found": True, "record": record}
        else:
            return {"found": False, "message": f"No record found for '{name}'"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/criminal-records/flagged")
async def get_flagged_records():
    """Get only flagged criminal records"""
    try:
        records = criminal_records_manager.get_flagged_records()
        return {"records": records, "count": len(records)}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/criminal-records/add")
async def add_criminal_record(record: dict):
    """Add a new criminal record"""
    try:
        success = criminal_records_manager.add_record(record)
        if success:
            return {"success": True, "message": "Record added successfully"}
        else:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Invalid record format"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/generate-report")
async def generate_report(data: dict):
    """Generate comprehensive court proceeding report"""
    try:
        meeting_id = data.get("meeting_id")
        judge_statement = data.get("judge_statement", "")
        
        if not meeting_id:
            return JSONResponse(
                status_code=400,
                content={"error": "Meeting ID required"}
            )
        
        # Get meeting from meeting manager
        meeting = meeting_manager.get_meeting(meeting_id.upper())
        if not meeting:
            return JSONResponse(
                status_code=404,
                content={"error": "Meeting not found"}
            )
        
        # Prepare meeting data for report
        meeting_data = {
            "meeting_id": meeting_id,
            "transcript": meeting.transcript,
            "evidence": evidence_manager.get_evidence_list(),
            "criminal_records": data.get("criminal_records_checked", []),
            "chat_history": data.get("chat_history", []),
            "judge_statement": judge_statement,
            "participants": meeting.get_participant_list(),
            "start_time": meeting.created_at.isoformat(),
            "duration": data.get("duration", "N/A")
        }
        
        # Generate report
        report = report_generator.generate_report_content(meeting_data)
        
        if not report:
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to generate report"}
            )
        
        # Combine all sections into full report text
        full_report = (
            report['header'] +
            report['participants'] +
            report['criminal_records'] +
            "\n═══════════════════════════════════════════════════════════════\n" +
            "                     EXECUTIVE SUMMARY\n" +
            "              (AI-Generated Analysis & Overview)\n" +
            "═══════════════════════════════════════════════════════════════\n\n" +
            report['ai_analysis'] + "\n" +
            report['transcript'] +
            report['evidence'] +
            "\n═══════════════════════════════════════════════════════════════\n" +
            "                  JUDGE'S FINAL STATEMENT\n" +
            "═══════════════════════════════════════════════════════════════\n\n" +
            (judge_statement if judge_statement else "No final statement has been provided by the presiding judge at this time.\n") + "\n" +
            report['footer']
        )
        
        return {
            "success": True,
            "report": full_report,
            "sections": report
        }
        
    except Exception as e:
        print(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/chat")
async def chat(data: dict):
    """Chat with AI assistant using Groq LLM"""
    try:
        message = data.get("message", "")
        if not message:
            return JSONResponse(
                status_code=400,
                content={"error": "Message is required"}
            )
        
        # Get transcript context
        transcript_context = ""
        if session_transcript:
            transcript_context = "TRANSCRIPT:\n"
            for entry in session_transcript:
                transcript_context += f"[{entry['timestamp']}] {entry.get('speaker', 'Speaker')}: {entry['text']}\n"
        
        # Get evidence context
        evidence_context = ""
        if evidence_manager.vector_store:
            evidence_results = evidence_manager.search_evidence(message, k=3)
            if evidence_results:
                evidence_context = "\n\nRELEVANT EVIDENCE:\n"
                for i, result in enumerate(evidence_results, 1):
                    evidence_context += f"\n[Evidence {i} from {result['filename']}]:\n{result['content']}\n"
        
        # Get criminal records context
        criminal_records_context = ""
        # Check if question mentions criminal records, names, or record-related keywords
        record_keywords = ['criminal', 'record', 'crime', 'flagged', 'history', 'conviction', 'assault', 'theft', 'fraud']
        if any(keyword in message.lower() for keyword in record_keywords):
            criminal_records_context = "\n\n" + criminal_records_manager.get_all_records_text()
        
        # Combine context
        full_context = transcript_context + evidence_context + criminal_records_context
        
        # Get response from Groq LLM
        response = await llm_service.ask_question(message, full_context)
        
        return {"response": response}
    
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Chat failed: {str(e)}"}
        )


# ==================== Legal Document Analyzer Endpoints ====================

@app.post("/analyze-legal-document")
async def analyze_legal_document(data: dict):
    """
    Analyze a legal document and provide simplified summary
    
    Request body:
    {
        "content": "Document text to analyze"
    }
    
    Returns:
    {
        "summary": "Color-coded summary",
        "keyPoints": [...],
        "wordHelper": [...],
        "verifiableClaims": [...],
        "originalText": "..."
    }
    """
    try:
        content = data.get("content", "").strip()
        
        if not content:
            return JSONResponse(
                status_code=400,
                content={"error": "No content provided"}
            )
        
        # Analyze the document
        result = legal_document_analyzer.analyze_document(content)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        print(f"Error in analyze_legal_document: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Analysis failed: {str(e)}"}
        )


@app.post("/ask-question-legal")
async def ask_question_legal(data: dict):
    """
    Answer a question about an analyzed legal document
    
    Request body:
    {
        "question": "User's question",
        "originalText": "Original document text"
    }
    
    Returns:
    {
        "answer": "AI's answer",
        "suggestions": ["Follow-up question 1", ...]
    }
    """
    try:
        question = data.get("question", "").strip()
        original_text = data.get("originalText", "").strip()
        
        if not question or not original_text:
            return JSONResponse(
                status_code=400,
                content={"error": "Question and original text are required"}
            )
        
        # Get answer
        result = legal_document_analyzer.answer_question(question, original_text)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        print(f"Error in ask_question_legal: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to answer question: {str(e)}"}
        )


# ==================== Reviews Endpoints ====================

@app.post("/submit-review")
async def submit_review(data: dict):
    """
    Submit a user review
    
    Request body:
    {
        "name": "User name",
        "role": "Judge/Lawyer/etc",
        "rating": 5,
        "review": "Review text"
    }
    """
    try:
        import json
        from datetime import datetime
        
        # Load existing reviews
        try:
            with open('reviews.json', 'r', encoding='utf-8') as f:
                reviews = json.load(f)
        except FileNotFoundError:
            reviews = []
        
        # Add new review
        new_review = {
            "id": len(reviews) + 1,
            "name": data.get("name", "Anonymous"),
            "role": data.get("role", "User"),
            "rating": data.get("rating", 5),
            "review": data.get("review", ""),
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        
        reviews.append(new_review)
        
        # Save reviews
        with open('reviews.json', 'w', encoding='utf-8') as f:
            json.dump(reviews, f, indent=2, ensure_ascii=False)
        
        return JSONResponse(content={"success": True, "message": "Review submitted successfully"})
        
    except Exception as e:
        print(f"Error submitting review: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to submit review: {str(e)}"}
        )


@app.get("/get-reviews")
async def get_reviews():
    """Get all reviews"""
    try:
        import json
        
        try:
            with open('reviews.json', 'r', encoding='utf-8') as f:
                reviews = json.load(f)
        except FileNotFoundError:
            reviews = []
        
        # Return latest 10 reviews
        return JSONResponse(content={"reviews": reviews[-10:][::-1]})
        
    except Exception as e:
        print(f"Error getting reviews: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get reviews: {str(e)}"}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)