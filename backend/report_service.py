from datetime import datetime
from typing import Dict, List
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class ReportGenerator:
    def __init__(self):
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        
    def generate_report_content(self, meeting_data: Dict) -> Dict:
        """Generate comprehensive court report from meeting data"""
        try:
            # Extract data
            meeting_id = meeting_data.get('meeting_id', 'N/A')
            transcript = meeting_data.get('transcript', [])
            evidence = meeting_data.get('evidence', [])
            criminal_records = meeting_data.get('criminal_records', [])
            chat_history = meeting_data.get('chat_history', [])
            judge_statement = meeting_data.get('judge_statement', '')
            participants = meeting_data.get('participants', [])
            start_time = meeting_data.get('start_time', datetime.now().isoformat())
            duration = meeting_data.get('duration', 'N/A')
            
            # Generate AI summary
            summary = self._generate_ai_summary(transcript, evidence, criminal_records, chat_history)
            
            # Format report
            report = {
                'header': self._format_header(meeting_id, start_time, duration, participants),
                'participants': self._format_participants(participants),
                'criminal_records': self._format_criminal_records(criminal_records),
                'transcript': self._format_transcript(transcript),
                'evidence': self._format_evidence(evidence),
                'ai_analysis': summary,
                'judge_statement': judge_statement,
                'footer': self._format_footer()
            }
            
            return report
            
        except Exception as e:
            print(f"Error generating report: {e}")
            return None
    
    def _generate_ai_summary(self, transcript, evidence, criminal_records, chat_history):
        """Use dedicated AI agent to generate comprehensive court report summary"""
        try:
            # Prepare context
            transcript_text = "\n".join([f"[{entry.get('timestamp', 'N/A')}] {entry.get('speaker', 'Unknown')} ({entry.get('role', 'Unknown')}): {entry.get('text', '')}" 
                                        for entry in transcript])
            
            evidence_text = "\n".join([f"• Document: {ev.get('name', 'Unknown')}\n  Type: {ev.get('type', 'Unknown')}\n  Analysis: {ev.get('analysis', 'No analysis available')}" 
                                       for ev in evidence])
            
            records_text = "\n".join([f"• {rec.get('name', 'Unknown')}\n  Status: {rec.get('status', 'Unknown')}\n  Crime: {rec.get('crime', 'None')}\n  Year: {rec.get('year', 'N/A')}\n  Details: {rec.get('details', 'No details')}" 
                                     for rec in criminal_records])
            
            # System prompt for dedicated report generation agent
            system_prompt = """You are an expert Court Report Generation AI Agent. Your ONLY purpose is to create professional, factual, and comprehensive court proceeding reports.

Your responsibilities:
1. Analyze all provided information (transcript, evidence, criminal records)
2. Extract key legal points, arguments, and findings
3. Identify important testimonies and statements
4. Summarize evidence relevance and impact
5. Note any criminal background that affects the case
6. Create a clear, objective executive summary

Guidelines:
- Use formal legal language
- Be completely objective and factual
- Organize information logically
- Highlight critical moments in the proceeding
- Note any contradictions or important patterns
- Keep summary focused and professional
- Do NOT provide legal advice or opinions
- Do NOT make judgments about guilt or innocence
- ONLY summarize and organize the facts presented"""

            user_prompt = f"""Generate a comprehensive EXECUTIVE SUMMARY for this court proceeding report.

═══════════════════════════════════════════════════════════════
SESSION TRANSCRIPT:
═══════════════════════════════════════════════════════════════
{transcript_text[:4000] if transcript_text else "No transcript recorded."}

═══════════════════════════════════════════════════════════════
EVIDENCE DOCUMENTS PRESENTED:
═══════════════════════════════════════════════════════════════
{evidence_text if evidence_text else "No evidence documents were submitted."}

═══════════════════════════════════════════════════════════════
CRIMINAL RECORDS CHECKED:
═══════════════════════════════════════════════════════════════
{records_text if records_text else "No criminal background checks were performed."}

═══════════════════════════════════════════════════════════════

Based on the above information, generate a professional EXECUTIVE SUMMARY that includes:

1. CASE OVERVIEW (2-3 sentences describing the proceeding)
2. KEY PARTICIPANTS (Who spoke and their roles)
3. MAIN ARGUMENTS PRESENTED (Summary of primary points from each side)
4. EVIDENCE ANALYSIS (What evidence was presented and its relevance)
5. CRIMINAL BACKGROUND RELEVANCE (If applicable, how it relates to the case)
6. NOTABLE TESTIMONIES (Important statements or admissions)
7. PROCEDURAL NOTES (Any important procedural matters)
8. OUTSTANDING ISSUES (Unresolved questions or pending matters)

Keep the summary factual, objective, and professionally formatted. Use clear section headers. Maximum 800 words."""

            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.2,  # Lower temperature for more factual, consistent output
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating AI summary: {e}")
            import traceback
            traceback.print_exc()
            return "Executive summary generation failed due to technical error. Please review the full transcript and evidence sections below."
    
    def _format_header(self, meeting_id, start_time, duration, participants):
        """Format report header"""
        try:
            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            formatted_time = dt.strftime("%B %d, %Y at %I:%M %p")
            formatted_date = dt.strftime("%B %d, %Y")
        except:
            formatted_time = start_time
            formatted_date = "Date Unknown"
            
        return f"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              OFFICIAL COURT PROCEEDING REPORT                 ║
║                                                               ║
║                    Generated by Nyaya-Sahayak                 ║
║                   AI-Powered Legal Assistant                  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝


═══════════════════════════════════════════════════════════════
                        CASE INFORMATION
═══════════════════════════════════════════════════════════════

Case Reference ID:     {meeting_id}
Proceeding Date:       {formatted_date}
Session Time:          {formatted_time}
Session Duration:      {duration}
Number of Participants: {len(participants)}
Report Generated:      {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
"""
    
    def _format_participants(self, participants):
        """Format participants section"""
        section = "\n═══════════════════════════════════════════════════════════════\n"
        section += "                    PARTICIPANTS PRESENT\n"
        section += "═══════════════════════════════════════════════════════════════\n\n"
        
        # Group by role
        roles = {}
        for p in participants:
            role = p.get('role', 'Observer')
            name = p.get('name', 'Unknown')
            if role not in roles:
                roles[role] = []
            roles[role].append(name)
        
        # Format by role
        for role, names in sorted(roles.items()):
            section += f"{role}{'s' if len(names) > 1 else ''}:\n"
            for name in names:
                section += f"  • {name}\n"
            section += "\n"
        
        return section
    
    def _format_criminal_records(self, records):
        """Format criminal records section"""
        if not records:
            return "\nCRIMINAL RECORDS CHECKED\n═══════════════════════════════════════════════════════════════\nNo criminal records were checked during this session.\n"
        
        section = "\nCRIMINAL RECORDS CHECKED\n"
        section += "═══════════════════════════════════════════════════════════════\n"
        
        for rec in records:
            name = rec.get('name', 'Unknown')
            status = rec.get('status', 'Unknown')
            crime = rec.get('crime', 'None')
            year = rec.get('year', 'N/A')
            details = rec.get('details', 'No details')
            
            section += f"\n• Name: {name}\n"
            section += f"  Status: {status}\n"
            section += f"  Crime: {crime}\n"
            section += f"  Year: {year}\n"
            section += f"  Details: {details}\n"
        
        return section
    
    def _format_transcript(self, transcript):
        """Format transcript section"""
        if not transcript:
            return "\n═══════════════════════════════════════════════════════════════\n                     SESSION TRANSCRIPT\n═══════════════════════════════════════════════════════════════\n\nNo transcript was recorded during this session.\n"
        
        section = "\n═══════════════════════════════════════════════════════════════\n"
        section += "                     SESSION TRANSCRIPT\n"
        section += "═══════════════════════════════════════════════════════════════\n"
        section += f"\n[Full verbatim transcript of proceedings - {len(transcript)} statements recorded]\n\n"
        
        for i, entry in enumerate(transcript, 1):
            timestamp = entry.get('timestamp', 'N/A')
            speaker = entry.get('speaker', 'Unknown')
            role = entry.get('role', 'Unknown')
            text = entry.get('text', '')
            
            section += f"[{i}] [{timestamp}] {speaker} ({role}):\n"
            section += f"    {text}\n\n"
        
        return section
    
    def _format_evidence(self, evidence):
        """Format evidence section"""
        if not evidence:
            return "\n═══════════════════════════════════════════════════════════════\n                    EVIDENCE PRESENTED\n═══════════════════════════════════════════════════════════════\n\nNo documentary evidence was submitted during this session.\n"
        
        section = "\n═══════════════════════════════════════════════════════════════\n"
        section += "                    EVIDENCE PRESENTED\n"
        section += "═══════════════════════════════════════════════════════════════\n\n"
        section += f"Total Evidence Documents Submitted: {len(evidence)}\n\n"
        
        for i, ev in enumerate(evidence, 1):
            name = ev.get('name', 'Unknown')
            file_type = ev.get('type', 'Unknown')
            analysis = ev.get('analysis', 'No AI analysis available for this document.')
            
            section += f"EXHIBIT {i}:\n"
            section += f"  Document Name: {name}\n"
            section += f"  File Type: {file_type}\n"
            section += f"  AI Analysis Summary:\n"
            section += f"  {analysis}\n\n"
            section += "  " + "─" * 60 + "\n\n"
        
        return section
    
    def _format_footer(self):
        """Format report footer"""
        generated_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        return f"""

═══════════════════════════════════════════════════════════════
                    AUTHENTICATION & SIGNATURES
═══════════════════════════════════════════════════════════════

I hereby certify that this is a true and accurate record of the
proceedings held on the date mentioned above.


Presiding Judge:

Signature: _________________________  Date: _______________

Name: ______________________________


Court Clerk/Reporter:

Signature: _________________________  Date: _______________

Name: ______________________________


═══════════════════════════════════════════════════════════════
                         CERTIFICATION
═══════════════════════════════════════════════════════════════

This report was automatically generated using Nyaya-Sahayak, an
AI-powered legal documentation system. The content is based on
audio transcription, submitted evidence, and criminal background
verification data collected during the proceeding.

Generated By: Nyaya-Sahayak AI Report Generation Agent
Generated On: {generated_time}
System Version: 1.0.0

IMPORTANT NOTICE: This AI-generated report should be reviewed
and verified by authorized court personnel before being filed
as an official court document.


═══════════════════════════════════════════════════════════════
                      END OF REPORT
═══════════════════════════════════════════════════════════════
"""

# Global instance
report_generator = ReportGenerator()
