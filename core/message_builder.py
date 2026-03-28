import json
import random
import os

from pathlib import Path

CONFIG_DIR = Path('config')
MESSAGES_PATH = CONFIG_DIR / 'messages.json'

def load_messages():
    if not MESSAGES_PATH.exists():
        return []
        
    try:
        with open(MESSAGES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('messages', [])
    except Exception as e:
        print(f"Error loading messages: {e}")
        return []

def save_messages(messages):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(MESSAGES_PATH, 'w', encoding='utf-8') as f:
            json.dump({"messages": messages}, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving messages: {e}")
        return False

def get_random_message(username):
    messages = load_messages()
    if not messages:
        return None
        
    msg = random.choice(messages)
    
    # Replace variables
    msg = msg.replace("{username}", username)
    msg = msg.replace("@{username}", f"@{username}")
    
    # Ensure it's under 1000 chars as per PRD
    if len(msg) > 1000:
        msg = msg[:997] + "..."
        
    return msg
