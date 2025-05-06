import os
import pandas as pd
import io
import logging
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime
from app import app, db
from models import Agent, ScheduledEmail, Contact
from utils import parse_tags, filter_contacts_by_tags
from email_utils import generate_email_content, create_and_send_email, schedule_email
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    agents = Agent.query.all()
    scheduled_emails = ScheduledEmail.query.filter_by(sent=False).order_by(ScheduledEmail.scheduled_time).all()
    contacts_count = Contact.query.count()
    return render_template('dashboard.html', 
                          agents=agents, 
                          scheduled_emails=scheduled_emails, 
                          contacts_count=contacts_count)

@app.route('/create_agent', methods=['GET', 'POST'])
def create_agent():
    if request.method == 'POST':
        name = request.form.get('name')
        role = request.form.get('role')
        goal = request.form.get('goal')
        backstory = request.form.get('backstory')
        
        if not all([name, role, goal, backstory]):
            flash('All fields are required!', 'error')
            return redirect(url_for('create_agent'))
        
        new_agent = Agent(name=name, role=role, goal=goal, backstory=backstory)
        db.session.add(new_agent)
        db.session.commit()
        
        flash('Agent created successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('create_agent.html')

@app.route('/agents')
def list_agents():
    agents = Agent.query.all()
    return render_template('agents.html', agents=agents)

@app.route('/generate_email', methods=['GET', 'POST'])
def generate_email():
    agents = Agent.query.all()
    
    if request.method == 'POST':
        prompt = request.form.get('prompt')
        agent_id = request.form.get('agent_id')
        
        # Generate email based on the prompt
        try:
            subject, body = generate_email_content(prompt, agent_id)
            session['email_subject'] = subject
            session['email_body'] = body
            
            return redirect(url_for('email_preview'))
        except Exception as e:
            logging.error(f"Error generating email: {str(e)}")
            flash(f'Error generating email: {str(e)}', 'error')
            return redirect(url_for('generate_email'))
    
    return render_template('generate_email.html', agents=agents)

@app.route('/email_preview')
def email_preview():
    subject = session.get('email_subject', '')
    body = session.get('email_body', '')
    
    if not subject or not body:
        flash('No email content found. Please generate an email first.', 'error')
        return redirect(url_for('generate_email'))
    
    # Get all tags from contacts for the filter dropdown
    contacts = Contact.query.all()
    all_tags = set()
    for contact in contacts:
        if contact.tags:
            all_tags.update([tag.strip() for tag in contact.tags.split(',')])
    
    return render_template('email_preview.html', subject=subject, body=body, all_tags=sorted(all_tags))

@app.route('/upload_contacts', methods=['POST'])
def upload_contacts():
    if 'contact_file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.referrer)
    
    file = request.files['contact_file']
    
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.referrer)
    
    if file:
        try:
            # Read CSV file
            stream = io.StringIO(file.stream.read().decode("utf-8"))
            df = pd.read_csv(stream)
            
            # Validate columns
            required_columns = ['name', 'email']
            if not all(col in df.columns for col in required_columns):
                flash('CSV file must contain at least "name" and "email" columns', 'error')
                return redirect(request.referrer)
            
            # Process contacts
            count = 0
            for _, row in df.iterrows():
                # Check if contact already exists
                existing_contact = Contact.query.filter_by(email=row['email']).first()
                
                if existing_contact:
                    # Update existing contact
                    existing_contact.name = row['name']
                    existing_contact.tags = row.get('tags', '')
                else:
                    # Create new contact
                    new_contact = Contact(
                        name=row['name'],
                        email=row['email'],
                        tags=row.get('tags', '')
                    )
                    db.session.add(new_contact)
                
                count += 1
            
            db.session.commit()
            flash(f'Successfully processed {count} contacts', 'success')
            
        except Exception as e:
            flash(f'Error processing CSV file: {str(e)}', 'error')
    
    return redirect(request.referrer)

@app.route('/get_filtered_contacts', methods=['POST'])
def get_filtered_contacts():
    tags = request.form.get('tags', '')
    tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
    
    contacts = Contact.query.all()
    filtered_contacts = []
    
    if tag_list:
        for contact in contacts:
            contact_tags = parse_tags(contact.tags or '')
            if any(tag in contact_tags for tag in tag_list):
                filtered_contacts.append({
                    'id': contact.id,
                    'name': contact.name,
                    'email': contact.email,
                    'tags': contact.tags
                })
    else:
        # If no tags specified, return all contacts
        filtered_contacts = [{
            'id': contact.id,
            'name': contact.name,
            'email': contact.email,
            'tags': contact.tags
        } for contact in contacts]
    
    return jsonify({'contacts': filtered_contacts})

@app.route('/send_email', methods=['POST'])
def send_email():
    subject = session.get('email_subject', '')
    body = session.get('email_body', '')
    
    if not subject or not body:
        flash('No email content found. Please generate an email first.', 'error')
        return redirect(url_for('generate_email'))
    
    recipient_ids = request.form.getlist('contact_ids')
    
    if not recipient_ids:
        flash('No recipients selected', 'error')
        return redirect(url_for('email_preview'))
    
    recipients = Contact.query.filter(Contact.id.in_(recipient_ids)).all()
    
    if not recipients:
        flash('No valid recipients found', 'error')
        return redirect(url_for('email_preview'))
    
    try:
        # Send email to all recipients
        for recipient in recipients:
            create_and_send_email(recipient.email, subject, body)
        
        flash(f'Email sent to {len(recipients)} recipients successfully!', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'Error sending email: {str(e)}', 'error')
        return redirect(url_for('email_preview'))

@app.route('/schedule_email', methods=['POST'])
def schedule_email_route():
    subject = session.get('email_subject', '')
    body = session.get('email_body', '')
    
    if not subject or not body:
        flash('No email content found. Please generate an email first.', 'error')
        return redirect(url_for('generate_email'))
    
    recipient_ids = request.form.getlist('contact_ids')
    
    if not recipient_ids:
        flash('No recipients selected', 'error')
        return redirect(url_for('email_preview'))
    
    recipients = Contact.query.filter(Contact.id.in_(recipient_ids)).all()
    
    if not recipients:
        flash('No valid recipients found', 'error')
        return redirect(url_for('email_preview'))
    
    schedule_date = request.form.get('schedule_date')
    schedule_time = request.form.get('schedule_time')
    
    if not schedule_date or not schedule_time:
        flash('Schedule date and time are required', 'error')
        return redirect(url_for('email_preview'))
    
    try:
        # Parse schedule datetime
        schedule_datetime = datetime.strptime(f"{schedule_date} {schedule_time}", "%Y-%m-%d %H:%M")
        
        # Create a comma-separated list of recipient emails
        recipient_emails = ','.join([recipient.email for recipient in recipients])
        
        # Save scheduled email to database
        scheduled_email = ScheduledEmail(
            subject=subject,
            body=body,
            recipients=recipient_emails,
            scheduled_time=schedule_datetime,
            sent=False
        )
        
        db.session.add(scheduled_email)
        db.session.commit()
        
        # Add job to scheduler
        schedule_email(scheduled_email.id, subject, body, recipient_emails, schedule_datetime)
        
        flash(f'Email scheduled for {schedule_datetime} with {len(recipients)} recipients!', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        logging.error(f"Error scheduling email: {str(e)}")
        flash(f'Error scheduling email: {str(e)}', 'error')
        return redirect(url_for('email_preview'))

@app.route('/contacts', methods=['GET'])
def list_contacts():
    contacts = Contact.query.all()
    return render_template('contacts.html', contacts=contacts)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500
