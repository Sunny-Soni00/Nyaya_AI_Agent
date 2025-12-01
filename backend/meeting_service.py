import uuid
import random
import string
from datetime import datetime
from typing import Dict, List, Optional

class User:
    def __init__(self, user_id: str, name: str, role: str = "Observer", meeting_id: str = None):
        self.user_id = user_id
        self.name = name
        self.role = role
        self.meeting_id = meeting_id
        self.joined_at = datetime.now()
        self.is_speaking = False
        
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "role": self.role,
            "meeting_id": self.meeting_id,
            "joined_at": self.joined_at.isoformat(),
            "is_speaking": self.is_speaking
        }


class Meeting:
    def __init__(self, meeting_id: str, host_user: User):
        self.meeting_id = meeting_id
        self.host_id = host_user.user_id
        self.host_name = host_user.name
        self.participants: Dict[str, User] = {host_user.user_id: host_user}
        self.transcript = []
        self.created_at = datetime.now()
        self.is_active = True
        
    def add_participant(self, user: User):
        self.participants[user.user_id] = user
        print(f"👤 {user.name} joined meeting {self.meeting_id}")
        
    def remove_participant(self, user_id: str):
        if user_id in self.participants:
            user_name = self.participants[user_id].name
            del self.participants[user_id]
            print(f"👋 {user_name} left meeting {self.meeting_id}")
            
    def add_transcript_entry(self, entry: dict):
        """Add a transcript entry to the meeting"""
        self.transcript.append(entry)
        return entry
        
    def get_participant_list(self):
        return [user.to_dict() for user in self.participants.values()]
        
    def to_dict(self):
        return {
            "meeting_id": self.meeting_id,
            "host_id": self.host_id,
            "host_name": self.host_name,
            "participants": self.get_participant_list(),
            "transcript_count": len(self.transcript),
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active
        }


class MeetingManager:
    def __init__(self):
        self.meetings: Dict[str, Meeting] = {}
        self.users: Dict[str, User] = {}
        
    def generate_meeting_id(self) -> str:
        """Generate a random 6-character meeting ID"""
        while True:
            meeting_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if meeting_id not in self.meetings:
                return meeting_id
                
    def create_user(self, name: str, role: str = "Observer") -> User:
        """Create a new user"""
        user_id = str(uuid.uuid4())
        user = User(user_id, name, role)
        self.users[user_id] = user
        print(f"✅ User created: {name} ({role}) ({user_id})")
        return user
        
    def create_meeting(self, host_user: User) -> Meeting:
        """Create a new meeting"""
        meeting_id = self.generate_meeting_id()
        meeting = Meeting(meeting_id, host_user)
        self.meetings[meeting_id] = meeting
        host_user.meeting_id = meeting_id
        print(f"🎯 Meeting created: {meeting_id} by {host_user.name}")
        return meeting
        
    def join_meeting(self, meeting_id: str, user: User) -> Optional[Meeting]:
        """Join an existing meeting"""
        meeting = self.meetings.get(meeting_id)
        if not meeting:
            print(f"❌ Meeting not found: {meeting_id}")
            return None
            
        if not meeting.is_active:
            print(f"❌ Meeting is not active: {meeting_id}")
            return None
            
        meeting.add_participant(user)
        user.meeting_id = meeting_id
        return meeting
        
    def leave_meeting(self, user_id: str):
        """Remove user from their meeting"""
        user = self.users.get(user_id)
        if not user or not user.meeting_id:
            return
            
        meeting = self.meetings.get(user.meeting_id)
        if meeting:
            meeting.remove_participant(user_id)
            
            # End meeting if host leaves or no participants
            if user_id == meeting.host_id or len(meeting.participants) == 0:
                meeting.is_active = False
                print(f"🔴 Meeting ended: {meeting.meeting_id}")
                
    def get_meeting(self, meeting_id: str) -> Optional[Meeting]:
        """Get meeting by ID"""
        return self.meetings.get(meeting_id)
        
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)
        
    def get_active_meetings(self) -> List[Meeting]:
        """Get all active meetings"""
        return [m for m in self.meetings.values() if m.is_active]
        
    def cleanup_inactive_meetings(self):
        """Remove inactive meetings (for memory management)"""
        inactive = [mid for mid, m in self.meetings.items() if not m.is_active]
        for mid in inactive:
            del self.meetings[mid]
        if inactive:
            print(f"🧹 Cleaned up {len(inactive)} inactive meetings")
