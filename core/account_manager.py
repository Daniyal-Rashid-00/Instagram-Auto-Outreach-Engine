from data.db import get_connection
from datetime import datetime
import json
from pathlib import Path

class AccountManager:
    def __init__(self):
        self.conn = get_connection()
        self.load_settings()
        
    def load_settings(self):
        settings_path = Path(__file__).parent.parent / 'config' / 'settings.json'
        if settings_path.exists():
            with open(settings_path, 'r') as f:
                self.settings = json.load(f)
        else:
            self.settings = {"daily_limit": 50}

    def get_accounts(self):
        self._check_resets()
        c = self.conn.cursor()
        c.execute("SELECT * FROM accounts")
        return [dict(row) for row in c.fetchall()]

    def add_account(self, username, proxy=''):
        c = self.conn.cursor()
        try:
            limit = self.settings.get('daily_limit', 50)
            c.execute(
                "INSERT INTO accounts (username, daily_limit, dms_sent_today, status, last_reset, proxy) VALUES (?, ?, 0, 'Active', ?, ?)",
                (username, limit, datetime.now().strftime("%Y-%m-%d"), proxy)
            )
            self.conn.commit()
            return True, c.lastrowid
        except Exception as e:
            if 'UNIQUE constraint failed' in str(e):
                return False, "Account already exists"
            return False, str(e)

    def update_proxy(self, account_id, proxy):
        c = self.conn.cursor()
        c.execute("UPDATE accounts SET proxy = ? WHERE id = ?", (proxy, account_id))
        self.conn.commit()

    def update_daily_limit(self, account_id, limit):
        c = self.conn.cursor()
        c.execute("UPDATE accounts SET daily_limit = ? WHERE id = ?", (limit, account_id))
        self.conn.commit()
            
    def remove_account(self, account_id):
        c = self.conn.cursor()
        c.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        self.conn.commit()

    def get_next_available(self):
        self._check_resets()
        c = self.conn.cursor()
        # Find active account that hasn't hit its limit yet
        c.execute("SELECT * FROM accounts WHERE status = 'Active' AND dms_sent_today < daily_limit ORDER BY id ASC LIMIT 1")
        row = c.fetchone()
        return dict(row) if row else None
        
    def get_account_by_id(self, account_id):
        self._check_resets()
        c = self.conn.cursor()
        c.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        row = c.fetchone()
        return dict(row) if row else None

    def update_status(self, account_id, status):
        c = self.conn.cursor()
        c.execute("UPDATE accounts SET status = ? WHERE id = ?", (status, account_id))
        self.conn.commit()

    def increment_dm_count(self, account_id):
        c = self.conn.cursor()
        c.execute("UPDATE accounts SET dms_sent_today = dms_sent_today + 1 WHERE id = ?", (account_id,))
        self.conn.commit()
        
    def _check_resets(self):
        # Reset counts if it's a new day
        today = datetime.now().strftime("%Y-%m-%d")
        c = self.conn.cursor()
        c.execute("UPDATE accounts SET dms_sent_today = 0, last_reset = ? WHERE last_reset != ? OR last_reset IS NULL", (today, today))
        if c.rowcount > 0:
            self.conn.commit()
