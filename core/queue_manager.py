import os
import re
from data.db import get_connection
from datetime import datetime

class QueueManager:
    def __init__(self):
        self.conn = get_connection()

    def import_txt(self, filepath):
        if not os.path.exists(filepath):
            return 0, 0, 0 # added, duplicates, blacklisted/sent
            
        added_count = 0
        duplicate_count = 0
        filtered_count = 0
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        c = self.conn.cursor()
        c.execute('BEGIN IMMEDIATE')
        
        for line in lines:
            username = line.strip()
            # Basic validation of instagram username
            if not username or not re.match(r'^[a-zA-Z0-9_\.]+$', username):
                continue
                
            # Check blacklist
            c.execute("SELECT 1 FROM blacklist WHERE username = ?", (username,))
            if c.fetchone():
                filtered_count += 1
                continue
                
            # Check sent log
            c.execute("SELECT 1 FROM sent_log WHERE username = ?", (username,))
            if c.fetchone():
                filtered_count += 1
                continue
                
            # Insert into queue
            try:
                c.execute(
                    "INSERT INTO queue (username, status, timestamp) VALUES (?, 'Pending', ?)",
                    (username, datetime.now().isoformat())
                )
                added_count += 1
            except Exception as e:
                if 'UNIQUE constraint failed' in str(e):
                    duplicate_count += 1
                    
        self.conn.commit()
        return added_count, duplicate_count, filtered_count

    def add_single(self, username):
        username = username.strip()
        if not username or not re.match(r'^[a-zA-Z0-9_\.]+$', username):
            return False, "Invalid username format"
            
        c = self.conn.cursor()
        c.execute("SELECT 1 FROM blacklist WHERE username = ?", (username,))
        if c.fetchone():
            return False, "Username is blacklisted"
            
        c.execute("SELECT 1 FROM sent_log WHERE username = ?", (username,))
        if c.fetchone():
            return False, "Username already messaged"
            
        try:
            c.execute(
                "INSERT INTO queue (username, status, timestamp) VALUES (?, 'Pending', ?)",
                (username, datetime.now().isoformat())
            )
            self.conn.commit()
            return True, "Added successfully"
        except Exception as e:
            if 'UNIQUE constraint failed' in str(e):
                return False, "Already in queue"
            return False, str(e)

    def get_queue(self):
        c = self.conn.cursor()
        c.execute("SELECT id, username, status, timestamp FROM queue ORDER BY id DESC")
        return [dict(row) for row in c.fetchall()]
        
    def get_pending(self):
        c = self.conn.cursor()
        c.execute("SELECT id, username FROM queue WHERE status = 'Pending' ORDER BY id ASC")
        return [dict(row) for row in c.fetchall()]

    def update_status(self, queue_id, status, error_msg=""):
        c = self.conn.cursor()
        c.execute("UPDATE queue SET status = ?, error_msg = ? WHERE id = ?", (status, error_msg, queue_id))
        self.conn.commit()

    def update_username(self, queue_id, new_username):
        c = self.conn.cursor()
        c.execute("UPDATE queue SET username = ? WHERE id = ?", (new_username, queue_id))
        self.conn.commit()
        
    def log_sent(self, username, account_id, message):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO sent_log (username, account_id, sent_at, message_hash) VALUES (?, ?, ?, ?)",
            (username, account_id, datetime.now().isoformat(), str(hash(message)))
        )
        self.conn.commit()

    def remove(self, queue_id):
        c = self.conn.cursor()
        c.execute("DELETE FROM queue WHERE id = ?", (queue_id,))
        self.conn.commit()
        
    def add_to_blacklist(self, username):
        c = self.conn.cursor()
        try:
            c.execute("INSERT INTO blacklist (username) VALUES (?)", (username,))
            self.conn.commit()
        except:
            pass # ignore duplicates

    def clear(self):
        c = self.conn.cursor()
        c.execute("DELETE FROM queue")
        self.conn.commit()
