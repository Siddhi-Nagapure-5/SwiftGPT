import os
import smtplib
import logging
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from utils import get_agent_system_prompt, load_agent_by_id

# Email configuration
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "");

# Initialize scheduler for email scheduling
scheduler = BackgroundScheduler()
scheduler.start()

# Sample email templates for demonstration purposes
EMAIL_TEMPLATES = {
    "formal": {
        "greeting": ["Dear {recipient},", "To Whom It May Concern,", "Dear Sir/Madam,"],
        "closing": ["Sincerely,", "Best regards,", "Yours faithfully,"],
        "body_formats": [
            "I am writing to {purpose}. {details}. {call_to_action}.",
            "This email is regarding {purpose}. {details}. I would appreciate {call_to_action}.",
            "I hope this email finds you well. {purpose}. {details}. {call_to_action}."
        ]
    },
    "informal": {
        "greeting": ["Hi {recipient},", "Hello {recipient},", "Hey there,"],
        "closing": ["Cheers,", "Thanks,", "All the best,"],
        "body_formats": [
            "Just wanted to let you know about {purpose}. {details}. {call_to_action}.",
            "Hope you're doing well! {purpose}. {details}. {call_to_action}.",
            "Quick update: {purpose}. {details}. Let me know if {call_to_action}."
        ]
    },
    "semi_formal": {
        "greeting": ["Hello {recipient},", "Greetings {recipient},", "Good day,"],
        "closing": ["Kind regards,", "Warm regards,", "Thank you,"],
        "body_formats": [
            "I wanted to reach out about {purpose}. {details}. Would you please {call_to_action}?",
            "I hope you're doing well. Regarding {purpose}, {details}. Please {call_to_action}.",
            "I'm writing about {purpose}. {details}. I'd appreciate if you could {call_to_action}."
        ]
    }
}

def determine_email_style(agent_id=None):
    """
    Determine the email style based on agent characteristics.
    
    Args:
        agent_id (int, optional): ID of the agent to use for determining style
        
    Returns:
        str: Email style ('formal', 'informal', or 'semi_formal')
    """
    if not agent_id:
        return 'semi_formal'  # Default style
    
    agent = load_agent_by_id(agent_id)
    if not agent:
        return 'semi_formal'
    
    agent_name = agent.name.lower() if agent.name else ''
    agent_role = agent.role.lower() if agent.role else ''
    
    if 'formal' in agent_name or 'formal' in agent_role:
        if 'informal' in agent_name or 'informal' in agent_role or 'casual' in agent_name or 'casual' in agent_role:
            return 'semi_formal'
        return 'formal'
    elif 'informal' in agent_name or 'informal' in agent_role or 'casual' in agent_name or 'casual' in agent_role:
        return 'informal'
    else:
        return 'semi_formal'

def extract_email_components(prompt):
    """
    Extract key components from the email prompt.
    
    Args:
        prompt (str): User's email request
        
    Returns:
        dict: Components for email generation
    """
    # Basic heuristics to extract components from the prompt
    components = {
        'recipient': 'recipient',
        'purpose': '',
        'details': '',
        'call_to_action': 'let me know your thoughts'
    }
    
    # Extract purpose (typically at the beginning of the prompt)
    if 'regarding' in prompt.lower():
        purpose_parts = prompt.lower().split('regarding')
        components['purpose'] = 'discuss ' + purpose_parts[1].split('.')[0].strip()
    elif 'about' in prompt.lower():
        purpose_parts = prompt.lower().split('about')
        components['purpose'] = 'inform you about' + purpose_parts[1].split('.')[0].strip()
    else:
        # Default purpose based on first sentence
        first_sentence = prompt.split('.')[0]
        components['purpose'] = 'share information about ' + first_sentence[-30:] if len(first_sentence) > 30 else first_sentence
    
    # Try to identify details from the middle of the prompt
    sentences = prompt.split('.')
    if len(sentences) > 1:
        components['details'] = sentences[1].strip()
    else:
        components['details'] = 'I wanted to follow up on our previous conversation'
        
    # Try to find call to action in the last part
    if 'please' in prompt.lower():
        action_part = prompt.lower().split('please')[1].strip()
        components['call_to_action'] = 'please ' + action_part
    elif 'would you' in prompt.lower():
        action_part = prompt.lower().split('would you')[1].strip()
        components['call_to_action'] = 'would you ' + action_part
    elif 'can you' in prompt.lower():
        action_part = prompt.lower().split('can you')[1].strip()
        components['call_to_action'] = 'can you ' + action_part
    
    # Extract a potential subject from keywords in the prompt
    words = prompt.split()
    significant_words = [w for w in words if len(w) > 3 and w.lower() not in ['about', 'would', 'could', 'email', 'write', 'send', 'please']]
    if significant_words:
        subject_words = ' '.join(significant_words[:3])
        components['subject'] = subject_words.capitalize()
    else:
        components['subject'] = 'Important Information'
    
    return components

def generate_email_content(prompt, agent_id=None, max_length=200, timeout=30):
    """
    Generate email content based on the given prompt.
    
    Args:
        prompt (str): User's email request
        agent_id (int, optional): ID of the agent to use for generation
        max_length (int, optional): Maximum length of generated text (unused in template version)
        timeout (int, optional): Timeout for generation in seconds (unused in template version)
        
    Returns:
        tuple: (subject, body) of the generated email
    """
    try:
        # Determine the email style based on agent
        style = determine_email_style(agent_id)
        template = EMAIL_TEMPLATES[style]
        
        # Extract components from the prompt
        components = extract_email_components(prompt)
        
        # Create subject
        subject = components['subject']
        
        # Select random components for the email
        greeting = random.choice(template['greeting']).format(recipient=components['recipient'])
        body_format = random.choice(template['body_formats'])
        closing = random.choice(template['closing'])
        
        # Format the body
        content = body_format.format(
            purpose=components['purpose'],
            details=components['details'],
            call_to_action=components['call_to_action']
        )
        
        # Construct the full email body
        body = f"{greeting}\n\n{content}\n\n{closing}"
        
        return subject, body
    except Exception as e:
        logging.error(f"Error in email generation: {e}")
        return "Email Generation", f"Unable to generate email content at this time. Please try again later."

def create_and_send_email(recipient_email, subject, body):
    """
    Create and send an email to the specified recipient.
    
    Args:
        recipient_email (str): Recipient's email address
        subject (str): Email subject
        body (str): Email body
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Create message
        message = MIMEMultipart()
        message["From"] = EMAIL_ADDRESS
        message["To"] = recipient_email
        message["Subject"] = subject
        
        # Attach body
        message.attach(MIMEText(body, "plain"))
        
        # Connect to server and send
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(message)
        
        logging.info(f"Email sent to {recipient_email}")
        return True
    except Exception as e:
        logging.error(f"Error sending email: {str(e)}")
        raise

def schedule_email(email_id, subject, body, recipients, scheduled_time):
    """
    Schedule an email to be sent at a specified time.
    
    Args:
        email_id (int): ID of the scheduled email in the database
        subject (str): Email subject
        body (str): Email body
        recipients (str): Comma-separated list of recipient emails
        scheduled_time (datetime): When to send the email
        
    Returns:
        None
    """
    from app import db
    from models import ScheduledEmail
    
    def send_scheduled_email(email_id, subject, body, recipients):
        try:
            # Send to each recipient
            recipient_list = [email.strip() for email in recipients.split(',')]
            for recipient in recipient_list:
                create_and_send_email(recipient, subject, body)
            
            # Update database record
            with db.app.app_context():
                email = ScheduledEmail.query.get(email_id)
                if email:
                    email.sent = True
                    db.session.commit()
            
            logging.info(f"Scheduled email {email_id} sent successfully")
        except Exception as e:
            logging.error(f"Error sending scheduled email {email_id}: {str(e)}")
    
    # Add the job to the scheduler
    scheduler.add_job(
        send_scheduled_email,
        'date',
        run_date=scheduled_time,
        args=[email_id, subject, body, recipients],
        id=f"email_{email_id}",
        replace_existing=True
    )
    
    logging.info(f"Email {email_id} scheduled for {scheduled_time}")
