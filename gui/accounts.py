from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
                             QInputDialog, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from core.account_manager import AccountManager
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
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(profile_dir.absolute()),
                    channel="msedge",
                    headless=False
                )
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
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)
        
        # Tools bar
        tools_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add New Account")
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5; color: white; border: none; padding: 10px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #4338CA; }
        """)
        self.btn_add.clicked.connect(self.add_account)
        
        self.btn_remove = QPushButton("Remove Selected")
        self.btn_remove.setStyleSheet("""
            QPushButton { background-color: #DC2626; color: white; border: none; padding: 10px; border-radius: 4px; }
            QPushButton:hover { background-color: #B91C1C; }
        """)
        self.btn_remove.clicked.connect(self.remove_selected)
        
        # Helper label for manual login note
        lbl_help = QLabel("Note: When adding, an Edge window will open. Login to Instagram manually, then close it.")
        lbl_help.setStyleSheet("color: #a3a3a3; font-style: italic;")
        
        tools_layout.addWidget(self.btn_add)
        tools_layout.addWidget(self.btn_remove)
        tools_layout.addWidget(lbl_help)
        tools_layout.addStretch()
        
        layout.addLayout(tools_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Status", "Sent Today", "Daily Limit"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Dark theme table styles
        self.table.setStyleSheet("""
            QTableWidget { background-color: #1e1e1e; color: #fff; gridline-color: #333; }
            QHeaderView::section { background-color: #2b2b2b; color: #fff; padding: 4px; }
            QTableWidget::item:selected { background-color: #4F46E5; }
        """)
        
        layout.addWidget(self.table)
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
        text, ok = QInputDialog.getText(self, 'Add Account', 'Enter exact Instagram Username:')
        if ok and text:
            success, result = self.account_manager.add_account(text)
            if success:
                QMessageBox.information(self, "Manual Login Required", 
                    f"Account added. A browser will now open. Please login to {text} and close the browser when done. The app will be usable while it's open.")
                
                # Launch playwright in a background thread to prevent UI freeze
                self.login_worker = LoginWorker(result)
                self.login_worker.finished_signal.connect(self.on_login_finished)
                self.login_worker.start()
                
            else:
                QMessageBox.warning(self, "Error", result)
                self.refresh_table()

    def on_login_finished(self, success, error_msg):
        if not success:
            QMessageBox.warning(self, "Browser Error", f"Failed to launch browser: {error_msg}")
        self.refresh_table()

    def remove_selected(self):
        selected = self.table.selectedItems()
        if not selected:
            return
            
        row = selected[0].row()
        acc_id = int(self.table.item(row, 0).text())
        confirm = QMessageBox.question(self, "Remove Account", "Are you sure? This will delete the session data too.",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.account_manager.remove_account(acc_id)
            self.refresh_table()
