import json
import random
import os
import re

from pathlib import Path

CONFIG_DIR = Path('config')
MESSAGES_PATH = CONFIG_DIR / 'messages.json'

def load_all_messages():
    if not MESSAGES_PATH.exists():
        return {"messages": [], "followups": []}
        
    try:
        with open(MESSAGES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {
                "messages": data.get('messages', []),
                "followups": data.get('followups', [])
            }
    except Exception as e:
        print(f"Error loading messages: {e}")
        return {"messages": [], "followups": []}

def save_messages(data_dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(MESSAGES_PATH, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving messages: {e}")
        return False

def process_spintax(text):
    """
    Resolves variations in format {option1|option2}.
    Specifically requires at least one '|' inside the brackets so it doesn't break {username}.
    """
    while True:
        match = re.search(r'\{([^{}]*\|[^{}]*)\}', text)
        if not match:
            break
        choices = match.group(1).split('|')
        text = text[:match.start()] + random.choice(choices) + text[match.end():]
    return text

def get_random_message(username, is_followup=False):
    all_msgs = load_all_messages()
    pool = all_msgs["followups"] if is_followup else all_msgs["messages"]
    
    if not pool:
        # Fallback to initial messages if no follow-ups exist
        pool = all_msgs["messages"]
        
    if not pool:
        return None
        
    msg = random.choice(pool)
    
    # Run spintax resolver first
    msg = process_spintax(msg)
    
    # Replace variables: use @username so that targets get notified
    msg = msg.replace("{username}", f"@{username}")
    # Address case where people might have manually typed @{username} already
    msg = msg.replace("@@{username}", f"@{username}") 
    msg = msg.replace("@@", "@") # Just in case it resulted in double @
    
    # Ensure it's under 1000 chars as per PRD
    if len(msg) > 1000:
        msg = msg[:997] + "..."
        
    return msg
