from app import db
from datetime import datetime

class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    goal = db.Column(db.String(255), nullable=False)
    backstory = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"Agent(id={self.id}, name='{self.name}', role='{self.role}')"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "goal": self.goal,
            "backstory": self.backstory
        }

class ScheduledEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    recipients = db.Column(db.Text, nullable=False)  # Store as comma-separated emails
    scheduled_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"ScheduledEmail(id={self.id}, subject='{self.subject}', scheduled_time='{self.scheduled_time}')"

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    tags = db.Column(db.String(255))  # Comma-separated tags
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"Contact(id={self.id}, name='{self.name}', email='{self.email}')"
