import pandas as pd
import os
import logging
from models import Agent

def parse_tags(tag_string):
    """
    Parse a comma-separated tag string into a list of tags.
    
    Args:
        tag_string (str): Comma-separated tags
        
    Returns:
        list: List of individual tag strings
    """
    if not tag_string:
        return []
    return [tag.strip() for tag in tag_string.split(',')]

def filter_contacts_by_tags(tags, contacts):
    """
    Filter a list of contacts by matching tags.
    
    Args:
        tags (list): List of tags to filter by
        contacts (list): List of Contact objects
        
    Returns:
        list: Filtered list of contacts containing any of the specified tags
    """
    if not tags:
        return contacts
    
    filtered_contacts = []
    for contact in contacts:
        contact_tags = parse_tags(contact.tags or '')
        if any(tag in contact_tags for tag in tags):
            filtered_contacts.append(contact)
    
    return filtered_contacts

def load_agent_by_id(agent_id):
    """
    Load an agent from the database by ID.
    
    Args:
        agent_id (int): The agent's ID
        
    Returns:
        Agent or None: The agent object if found, None otherwise
    """
    if not agent_id:
        return None
    
    from models import Agent
    return Agent.query.get(agent_id)

def csv_to_contacts(csv_file):
    """
    Parse a CSV file and return a list of contact dictionaries.
    
    Args:
        csv_file: CSV file object
        
    Returns:
        list: List of dictionaries with contact information
    """
    try:
        df = pd.read_csv(csv_file)
        
        # Ensure required columns exist
        required_columns = ['name', 'email']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Convert DataFrame to list of dictionaries
        contacts = []
        for _, row in df.iterrows():
            contact = {
                'name': row['name'],
                'email': row['email'],
                'tags': row.get('tags', '')
            }
            contacts.append(contact)
        
        return contacts
    except Exception as e:
        logging.error(f"Error parsing CSV file: {str(e)}")
        raise

def get_agent_system_prompt(agent_id=None):
    """
    Get the system prompt for a specific agent.
    
    Args:
        agent_id (int, optional): The agent's ID
        
    Returns:
        str: The system prompt tailored to the agent
    """
    # Default system prompt for email generation
    default_prompt = """You are a professional email assistant. Generate a concise email based on the user's request.
    Include a subject line, proper greeting, body content, and closing.
    Keep the email professional and to the point."""
    
    if not agent_id:
        return default_prompt
    
    agent = load_agent_by_id(agent_id)
    if not agent:
        return default_prompt
    
    # Customize the prompt based on the agent's characteristics
    if agent.role.lower() == "formal agent" or "formal" in agent.name.lower():
        return f"""You are {agent.name}, a {agent.role}. {agent.backstory}
        Your goal is to {agent.goal}
        Generate a formal, professional email with appropriate business etiquette.
        Include a clear subject line, formal greeting, concise body content, and professional closing.
        Maintain a respectful tone throughout."""
    
    elif agent.role.lower() == "informal agent" or "informal" in agent.name.lower():
        return f"""You are {agent.name}, a {agent.role}. {agent.backstory}
        Your goal is to {agent.goal}
        Generate a friendly, casual email with a conversational tone.
        Include an engaging subject line, casual greeting, personal body content, and friendly closing.
        Use contractions and a relaxed writing style."""
    
    elif agent.role.lower() == "semi-formal agent" or "semi" in agent.name.lower():
        return f"""You are {agent.name}, a {agent.role}. {agent.backstory}
        Your goal is to {agent.goal}
        Generate a balanced email that is professional but approachable.
        Include a clear subject line, appropriate greeting, informative but friendly body content, and polite closing.
        Strike a balance between formal and casual language."""
    
    else:
        # Custom agent prompt based on their characteristics
        return f"""You are {agent.name}, a {agent.role}. {agent.backstory}
        Your goal is to {agent.goal}
        Generate an email that reflects your unique characteristics.
        Include a suitable subject line, appropriate greeting, body content that achieves your goal, and fitting closing.
        Adapt your tone and style to match your role and purpose."""
