import json
from typing import List, Dict, Optional

class CriminalRecordsManager:
    def __init__(self):
        self.records = [
            {
                "name": "Vikram Singh",
                "status": "Flagged",
                "crime": "Assault (Section 323)",
                "year": "2021",
                "details": "History of aggressive behavior in court."
            },
            {
                "name": "Amit Verma",
                "status": "Clean",
                "crime": "None",
                "year": "N/A",
                "details": "No prior criminal record found."
            },
            {
                "name": "Rajesh Kumar",
                "status": "Flagged",
                "crime": "Theft (Section 379)",
                "year": "2019",
                "details": "Multiple theft cases, currently on bail."
            },
            {
                "name": "Priya Sharma",
                "status": "Clean",
                "crime": "None",
                "year": "N/A",
                "details": "No prior criminal record found."
            },
            {
                "name": "Suresh Patel",
                "status": "Flagged",
                "crime": "Fraud (Section 420)",
                "year": "2020",
                "details": "Convicted of financial fraud, served 6 months."
            }
        ]
    
    def search_by_name(self, name: str) -> Optional[Dict]:
        """Search for a criminal record by name (case-insensitive)"""
        name_lower = name.lower()
        for record in self.records:
            if name_lower in record["name"].lower():
                return record
        return None
    
    def get_all_records(self) -> List[Dict]:
        """Get all criminal records"""
        return self.records
    
    def get_flagged_records(self) -> List[Dict]:
        """Get only flagged records"""
        return [r for r in self.records if r["status"] == "Flagged"]
    
    def get_clean_records(self) -> List[Dict]:
        """Get only clean records"""
        return [r for r in self.records if r["status"] == "Clean"]
    
    def add_record(self, record: Dict) -> bool:
        """Add a new criminal record"""
        required_fields = ["name", "status", "crime", "year", "details"]
        if all(field in record for field in required_fields):
            self.records.append(record)
            return True
        return False
    
    def format_record_for_llm(self, record: Dict) -> str:
        """Format a record for LLM context"""
        return f"""
Criminal Record:
- Name: {record['name']}
- Status: {record['status']}
- Crime: {record['crime']}
- Year: {record['year']}
- Details: {record['details']}
"""
    
    def get_all_records_text(self) -> str:
        """Get all records formatted as text for LLM context"""
        text = "Criminal Records Database:\n\n"
        for record in self.records:
            text += self.format_record_for_llm(record) + "\n"
        return text

# Global instance
criminal_records_manager = CriminalRecordsManager()
