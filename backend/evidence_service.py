import os
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract
from io import BytesIO

class EvidenceManager:
    def __init__(self):
        self.embeddings = None  # Lazy load to speed up startup
        self.vector_store = None
        self.documents = []
        self.audio_transcripts = {}  # Store audio transcripts separately
        self.text_splitter = None  # Lazy load
        self.file_storage = {}  # Store original file bytes for download
    
    def _ensure_embeddings(self):
        """Lazy load embeddings model only when needed"""
        if self.embeddings is None:
            print("🔄 Loading embeddings model...")
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
            except ImportError:
                from langchain_community.embeddings import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            print("✅ Embeddings model loaded")
    
    def _ensure_text_splitter(self):
        """Lazy load text splitter"""
        if self.text_splitter is None:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
    
    def extract_text_from_pdf(self, file_bytes):
        """Extract text from PDF file"""
        try:
            pdf = PdfReader(BytesIO(file_bytes))
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise Exception(f"Error extracting PDF text: {e}")
    
    def extract_text_from_image(self, file_bytes):
        """Extract text from image using OCR"""
        try:
            image = Image.open(BytesIO(file_bytes))
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            raise Exception(f"Error extracting image text: {e}")
    
    def process_file(self, file_bytes, filename, file_type="document"):
        """Process uploaded file (PDF, Image, or Audio)"""
        file_ext = filename.lower().split('.')[-1]
        
        # Store original file for download
        self.file_storage[filename] = {
            "content": file_bytes,
            "type": file_type,
            "extension": file_ext
        }
        
        if file_type == "audio":
            # Audio files are processed separately with transcription
            # Just return 0 chunks as they're handled differently
            return 0
        elif file_ext == 'pdf':
            text = self.extract_text_from_pdf(file_bytes)
        elif file_ext in ['jpg', 'jpeg', 'png', 'bmp', 'tiff']:
            text = self.extract_text_from_image(file_bytes)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        # Split text into chunks
        self._ensure_text_splitter()
        chunks = self.text_splitter.split_text(text)
        
        # Store metadata
        docs = [{"content": chunk, "filename": filename} for chunk in chunks]
        self.documents.extend(docs)
        
        return len(chunks)
    
    def add_audio_transcript(self, filename, transcript_text, transcript_data=None):
        """Add audio transcript to evidence"""
        # Store full transcript data
        self.audio_transcripts[filename] = {
            "text": transcript_text,
            "data": transcript_data
        }
        
        # Split and add to documents for RAG
        self._ensure_text_splitter()
        chunks = self.text_splitter.split_text(transcript_text)
        docs = [{"content": chunk, "filename": filename} for chunk in chunks]
        self.documents.extend(docs)
        
        return len(chunks)
    
    def build_vector_store(self):
        """Build FAISS vector store from all documents"""
        if not self.documents:
            return False
        
        self._ensure_embeddings()  # Load embeddings only when needed
        
        texts = [doc["content"] for doc in self.documents]
        metadatas = [{"filename": doc["filename"]} for doc in self.documents]
        
        from langchain_community.vectorstores import FAISS
        self.vector_store = FAISS.from_texts(
            texts=texts,
            embedding=self.embeddings,
            metadatas=metadatas
        )
        
        return True
    
    def search_evidence(self, query, k=3):
        """Search for relevant evidence chunks"""
        if not self.vector_store:
            return []
        
        self._ensure_embeddings()  # Ensure embeddings loaded
        
        results = self.vector_store.similarity_search_with_score(query, k=k)
        
        return [
            {
                "content": doc.page_content,
                "filename": doc.metadata.get("filename", "Unknown"),
                "score": float(score)
            }
            for doc, score in results
        ]
    
    def get_all_evidence_text(self):
        """Get all evidence as combined text"""
        return "\n\n".join([f"[{doc['filename']}]\n{doc['content']}" for doc in self.documents])
    
    def get_evidence_list(self):
        """Get list of all evidence documents with metadata for report"""
        evidence_list = []
        
        # Add document evidence
        for doc in self.documents:
            evidence_list.append({
                "name": doc.get('filename', 'Unknown'),
                "type": doc.get('type', 'document'),
                "analysis": doc.get('content', '')[:500] + "..." if len(doc.get('content', '')) > 500 else doc.get('content', '')
            })
        
        # Add audio transcripts
        for filename, transcript_data in self.audio_transcripts.items():
            evidence_list.append({
                "name": filename,
                "type": "audio",
                "analysis": transcript_data.get('transcript', '')[:500] + "..." if len(transcript_data.get('transcript', '')) > 500 else transcript_data.get('transcript', '')
            })
        
        return evidence_list
    
    def clear_evidence(self):
        """Clear all evidence"""
        self.documents = []
        self.audio_transcripts = {}
        self.vector_store = None
    
    def get_audio_transcript(self, filename):
        """Get transcript for a specific audio file"""
        return self.audio_transcripts.get(filename)
