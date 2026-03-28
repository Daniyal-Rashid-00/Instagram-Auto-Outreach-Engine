import time
import random
import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime

from PyQt6.QtCore import QThread, pyqtSignal
from playwright.sync_api import sync_playwright, TimeoutError

from core.account_manager import AccountManager
from core.queue_manager import QueueManager
from core.message_builder import get_random_message

class DMEngine(QThread):
    log_signal = pyqtSignal(str, str) # type, msg
    progress_signal = pyqtSignal(int, int) # sent_count, failed_count
    status_signal = pyqtSignal(str) # Engine status message
    account_switched_signal = pyqtSignal(str) # Username
    finished_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.is_paused = False
        
        self.account_manager = AccountManager()
        self.queue_manager = QueueManager()
        
        self._load_settings()
        
    def _load_settings(self):
        settings_path = Path('config/settings.json')
        if settings_path.exists():
            with open(settings_path, 'r') as f:
                self.settings = json.load(f)
        else:
            self.settings = {"delay_min": 45, "delay_max": 120}
            
    def stop(self):
        self.is_running = False
        self.log_signal.emit("WARN", "Stopping engine...")
        
    def pause(self):
        self.is_paused = True
        self.log_signal.emit("INFO", "Engine paused")
        
    def resume(self):
        self.is_paused = False
        self.log_signal.emit("INFO", "Engine resumed")
        
    def _random_sleep(self, min_s=None, max_s=None):
        if min_s is None: min_s = self.settings.get("delay_min", 45)
        if max_s is None: max_s = self.settings.get("delay_max", 120)
        
        delay = random.uniform(min_s, max_s)
        self.log_signal.emit("INFO", f"Waiting {delay:.1f}s before next action...")
        
        # Non-blocking sleep for QThread
        slept = 0
        while slept < delay and self.is_running:
            while self.is_paused and self.is_running:
                time.sleep(1) # check pause state every second
            time.sleep(0.5)
            slept += 0.5

    def _check_anti_ban(self, page):
        # Extremely basic anti-ban checks (Instagram specific)
        try:
            url = page.url
            if "challenge" in url or "suspended" in url:
                return "Account Suspended or Challenge Required"
            
            # Look for action-block toast or text
            if page.locator("text='Try Again Later'").count() > 0 or \
               page.locator("text='Action Blocked'").count() > 0 or \
               page.locator("text='We restrict certain activity'").count() > 0:
                return "Action Blocked by Instagram"
                
        except Exception:
            pass
            
        return None

    def _setup_browser(self, p, account_id):
        # Ensure profile folder exists
        profile_dir = Path(f'data/profiles/account_{account_id}')
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir.absolute()),
            channel="msedge", # Use Edge as specified in PRD
            headless=False,
            viewport={'width': 1280, 'height': 800},
            ignore_default_args=['--enable-automation'],
            args=[
                '--disable-blink-features=AutomationControlled',
                '--test-type'
            ]
        )
        page = context.pages[0] if context.pages else context.new_page()
        return context, page

    def run(self):
        self.is_running = True
        self._load_settings()
        
        sent_count = 0
        failed_count = 0
        
        try:
            with sync_playwright() as p:
                current_account = self.account_manager.get_next_available()
                if not current_account:
                    self.log_signal.emit("ERROR", "No active accounts available with remaining daily limit.")
                    self.status_signal.emit("Failed: No accounts")
                    return
                    
                self.log_signal.emit("INFO", f"Starting engine with account: {current_account['username']}")
                self.account_switched_signal.emit(current_account['username'])
                
                context, page = self._setup_browser(p, current_account['id'])
                
                # Verify login
                page.goto("https://www.instagram.com/", timeout=60000)
                if "login" in page.url or page.locator("input[name='username']").count() > 0:
                    self.log_signal.emit("ERROR", f"Account {current_account['username']} is not logged in! Please login manually first.")
                    self.account_manager.update_status(current_account['id'], "Blocked")
                    context.close()
                    return
                
                queue = self.queue_manager.get_pending()
                if self.settings.get('send_order') == 'random':
                    random.shuffle(queue)
                    
                self.log_signal.emit("INFO", f"Found {len(queue)} pending targets in queue.")
                
                for task in queue:
                    if not self.is_running:
                        break
                    while self.is_paused:
                        time.sleep(1)
                        if not self.is_running: break
                        
                    target_username = task['username']
                    task_id = task['id']
                    
                    self.log_signal.emit("INFO", f"Processing: {target_username}")
                    
                    try:
                        # 1. Navigate to Target Profile
                        page.goto(f"https://www.instagram.com/{target_username}/", timeout=30000)
                        self._random_sleep(3, 6) # wait for page load fully organically
                        
                        # Anti-ban check
                        ban_reason = self._check_anti_ban(page)
                        if ban_reason:
                            raise Exception(ban_reason)
                            
                        # Human simulation: scroll target profile briefly before DM
                        page.evaluate("window.scrollBy(0, 500)")
                        self._random_sleep(1, 3)
                        
                        # 2. Like a random post
                        try:
                            posts = page.locator("a[href*='/p/'], a[href*='/reel/']")
                            # wait for posts to load briefly, if any
                            page.wait_for_selector("a[href*='/p/'], a[href*='/reel/']", timeout=3000)
                            if posts.count() > 0:
                                post_count = min(posts.count(), 6)
                                idx = random.randint(0, post_count - 1)
                                posts.nth(idx).click()
                                self._random_sleep(2, 4)
                                
                                # Click the Like button (only if not already liked)
                                like_btn = page.locator("svg[aria-label='Like']").first
                                if like_btn.count() > 0:
                                    # Force click the SVG itself directly
                                    like_btn.click(force=True)
                                    self.log_signal.emit("INFO", "Liked a recent post")
                                self._random_sleep(1, 3)
                                
                                # Close the post modal (Escape key always works for Instagram modals)
                                page.keyboard.press("Escape")
                                self._random_sleep(1, 2)
                        except Exception as e:
                            pass # If they have no posts or liking fails, just skip naturally
                        
                        # 3. Click 'Message' button
                        # Instagram desktop uses divs with role="button" for these
                        msg_btn = page.locator("div[role='button']:has-text('Message'), button:has-text('Message')").first
                        if msg_btn.count() == 0:
                             # Fallback to direct text search
                             msg_btn = page.locator("text='Message'").first
                             
                        if msg_btn.count() == 0:
                             raise Exception("Message button not found on profile (Private account, you must follow them, or Instagram hid the button)")
                             
                        msg_btn.click()
                        self._random_sleep(4, 8)
                        
                        # Dismiss potential "Turn on Notifications" modal if it pops up
                        not_now = page.locator("button:has-text('Not Now')").first
                        if not_now.count() > 0:
                            not_now.click()
                            self._random_sleep(1, 2)
                        
                        # 5. Type and send message
                        # Wait for the chat DM interface to load
                        page.wait_for_selector("div[role='textbox']", timeout=15000)
                        
                        # There might be multiple textboxes (like search). The actual message box is typically the last visible one.
                        messagebox = page.locator("div[role='textbox']").last
                        
                        msg = get_random_message(target_username)
                        if not msg:
                             raise Exception("Message pool is empty")
                             
                        messagebox.click()
                        
                        # Paste instantly instead of slow typing, as requested
                        page.keyboard.insert_text(msg)
                        self._random_sleep(1, 3)
                        
                        # Actually send
                        page.keyboard.press("Enter")
                        
                        # 6. Success logic
                        self.log_signal.emit("SUCCESS", f"Sent DM to {target_username}")
                        self.queue_manager.update_status(task_id, "Sent")
                        self.queue_manager.log_sent(target_username, current_account['id'], msg)
                        self.account_manager.increment_dm_count(current_account['id'])
                        
                        sent_count += 1
                        self.progress_signal.emit(sent_count, failed_count)
                        
                        # 7. Check account rotation
                        current_account = self.account_manager.get_account_by_id(current_account['id'])
                        if current_account['dms_sent_today'] >= current_account['daily_limit']:
                            self.log_signal.emit("WARN", f"Daily limit reached for {current_account['username']}")
                            context.close()
                            
                            next_acc = self.account_manager.get_next_available()
                            if not next_acc:
                                self.log_signal.emit("WARN", "No more active accounts available.")
                                break
                                
                            current_account = next_acc
                            self.log_signal.emit("INFO", f"Switching to account {current_account['username']}")
                            self.account_switched_signal.emit(current_account['username'])
                            context, page = self._setup_browser(p, current_account['id'])
                        
                    except Exception as e:
                        err_str = str(e)
                        if "Private account" in err_str:
                             self.log_signal.emit("WARN", f"Skipped {target_username}: Account private or messages off")
                             self.queue_manager.update_status(task_id, "Skipped", "Private/No Msg Button")
                             self._random_sleep(1, 2)
                             continue
                             
                        self.log_signal.emit("ERROR", f"Failed targeting {target_username}: {err_str}")
                        self.queue_manager.update_status(task_id, "Failed", err_str)
                        failed_count += 1
                        self.progress_signal.emit(sent_count, failed_count)
                        
                        # If action block, block account and rotate immediately
                        if "Action Blocked" in err_str or "Suspended" in err_str:
                            self.account_manager.update_status(current_account['id'], "Blocked")
                            context.close()
                            
                            next_acc = self.account_manager.get_next_available()
                            if not next_acc:
                                self.log_signal.emit("WARN", "All accounts blocked or exhausted.")
                                break
                            current_account = next_acc
                            context, page = self._setup_browser(p, current_account['id'])
                            
                    # Delay before next user
                    self._random_sleep()

        except Exception as e:
            self.log_signal.emit("ERROR", f"Engine crash: {str(e)}")
            
        finally:
            self.is_running = False
            self.status_signal.emit("Engine stopped")
            self.finished_signal.emit()
            self.log_signal.emit("INFO", f"Session ended. Sent: {sent_count}, Failed: {failed_count}")
