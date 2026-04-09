from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from core.account_manager import AccountManager
from gui.dialogs import dark_info, dark_warning, dark_question, dark_input
import subprocess
from pathlib import Path

class LoginWorker(QThread):
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, account_id):
        super().__init__()
        self.account_id = account_id
        
    def run(self):
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                profile_dir = Path(f'data/profiles/account_{self.account_id}')
                profile_dir.mkdir(parents=True, exist_ok=True)
                
                # Add heavy anti-detect features so Meta doesn't block the manual login
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(profile_dir.absolute()),
                    channel="msedge",
                    headless=False,
                    no_viewport=True,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
                    ignore_default_args=["--enable-automation"],
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-infobars",
                        "--window-size=1280,800"
                    ]
                )
                
                # Inject stealth script to remove webdriver flag
                context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
                
                page = context.pages[0] if context.pages else context.new_page()
                page.goto("https://www.instagram.com/")
                
                # Block here in the worker thread until user closes the window
                try:
                    page.wait_for_event("close", timeout=0)
                except:
                    pass
                context.close()
            self.finished_signal.emit(True, "")
        except Exception as e:
            self.finished_signal.emit(False, str(e))

class AccountsPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.account_manager = AccountManager()
        self._init_ui()
        self.refresh_table()
        
    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        header = QLabel("Instagram Accounts")
        header.setObjectName("headerTitle")
        layout.addWidget(header)
        
        # Tools bar
        tools_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add New Account")
        self.btn_add.clicked.connect(self.add_account)

        self.btn_remove = QPushButton("Remove Selected")
        self.btn_remove.setObjectName("btnDanger")
        self.btn_remove.clicked.connect(self.remove_selected)

        self.btn_set_limit = QPushButton("📊  Set Daily Limit")
        self.btn_set_limit.setObjectName("btnWarning")
        self.btn_set_limit.clicked.connect(self.set_daily_limit)

        tools_layout.addWidget(self.btn_add)
        tools_layout.addWidget(self.btn_remove)
        tools_layout.addWidget(self.btn_set_limit)
        tools_layout.addStretch()
        
        layout.addLayout(tools_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Status", "Sent Today", "Daily Limit"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.table)
        
        # Info note card at the bottom
        note_card = QFrame()
        note_card.setObjectName("card")
        note_layout = QHBoxLayout(note_card)
        note_layout.setContentsMargins(16, 12, 16, 12)
        note_icon = QLabel("ℹ")
        note_icon.setStyleSheet("color: #58A6FF; font-size: 16px; font-weight: bold;")
        note_icon.setFixedWidth(20)
        note_text = QLabel(
            "When you click Add New Account, a secured browser window will open automatically. "
            "Log into your Instagram account inside that window, then close it. "
            "The session will be saved and the engine can use that account from now on."
        )
        note_text.setObjectName("subHeader")
        note_text.setWordWrap(True)
        note_layout.addWidget(note_icon)
        note_layout.addWidget(note_text)
        layout.addWidget(note_card)
        
        self.setLayout(layout)
        
    def refresh_table(self):
        accounts = self.account_manager.get_accounts()
        self.table.setRowCount(len(accounts))
        
        for row, acc in enumerate(accounts):
            
            id_item = QTableWidgetItem(str(acc['id']))
            user_item = QTableWidgetItem(acc['username'])
            status_item = QTableWidgetItem(acc['status'])
            sent_item = QTableWidgetItem(str(acc['dms_sent_today']))
            limit_item = QTableWidgetItem(str(acc['daily_limit']))
            
            # Color code status
            if acc['status'] == 'Active':
                status_item.setForeground(Qt.GlobalColor.green)
            elif acc['status'] == 'Blocked':
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.yellow)

            self.table.setItem(row, 0, id_item)
            self.table.setItem(row, 1, user_item)
            self.table.setItem(row, 2, status_item)
            self.table.setItem(row, 3, sent_item)
            self.table.setItem(row, 4, limit_item)

    def add_account(self):
        text, ok = dark_input(self, 'Add Account', 'Enter exact Instagram Username:', placeholder='e.g. john_doe_official')
        if ok and text:
            success, result = self.account_manager.add_account(text)
            if success:
                dark_info(self, "Manual Login Required",
                    f"Account added. A browser will now open.\nPlease log into '{text}' and close the browser when done.\nThe app remains usable while it's open.")
                self.login_worker = LoginWorker(result)
                self.login_worker.finished_signal.connect(self.on_login_finished)
                self.login_worker.start()
            else:
                dark_warning(self, "Error", result)
                self.refresh_table()

    def on_login_finished(self, success, error_msg):
        if not success:
            dark_warning(self, "Browser Error", f"Failed to launch browser:\n{error_msg}")
        self.refresh_table()

    def remove_selected(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        acc_id = int(self.table.item(row, 0).text())
        if dark_question(self, "Remove Account", "Are you sure? This will permanently delete the session data for this account."):
            self.account_manager.remove_account(acc_id)
            self.refresh_table()

    def set_daily_limit(self):
        selected = self.table.selectedItems()
        if not selected:
            dark_warning(self, "No Selection", "Please select an account row first.")
            return
        row = selected[0].row()
        acc_id    = int(self.table.item(row, 0).text())
        username  = self.table.item(row, 1).text()
        cur_limit = self.table.item(row, 4).text()

        text, ok = dark_input(
            self, 'Set Daily DM Limit',
            f'New daily DM limit for @{username}:',
            placeholder='e.g. 30',
            text=cur_limit
        )
        if ok and text:
            try:
                limit = int(text)
                if not (1 <= limit <= 500):
                    dark_warning(self, "Invalid", "Limit must be between 1 and 500.")
                    return
                self.account_manager.update_daily_limit(acc_id, limit)
                self.refresh_table()
                dark_info(self, "Updated", f"Daily limit for @{username} updated to {limit} DMs/day.")
            except ValueError:
                dark_warning(self, "Invalid Input", "Please enter a whole number.")
