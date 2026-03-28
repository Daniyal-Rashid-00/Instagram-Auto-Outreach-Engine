from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QStackedWidget, QLabel, QListWidgetItem
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont

from gui.dashboard import DashboardPanel
from gui.accounts import AccountsPanel
from gui.queue_panel import QueuePanel
from gui.messages import MessagesPanel
from gui.settings import SettingsPanel
from gui.logs import LogsPanel
from core.dm_engine import DMEngine

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CyberSolu DM Engine — by Daniyal Rashid")
        self.setMinimumSize(1000, 700)
        
        # Engine Thread
        self.engine = DMEngine()
        self.engine.log_signal.connect(self.on_engine_log)
        self.engine.progress_signal.connect(self.on_engine_progress)
        self.engine.status_signal.connect(self.on_engine_status)
        self.engine.account_switched_signal.connect(self.on_account_switched)
        self.engine.finished_signal.connect(self.on_engine_finished)
        
        self._init_ui()
        
    def _init_ui(self):
        # Apply dark theme stylesheet globally
        self.setStyleSheet("""
            QMainWindow, QWidget#main_content { background-color: #121212; color: #f3f4f6; font-family: 'Segoe UI', Arial, sans-serif; }
            QListWidget { background-color: #1e1e1e; border: none; padding-top: 20px; outline: 0; }
            QListWidget::item { padding: 15px 20px; color: #a3a3a3; font-size: 16px; font-weight: bold; border-left: 4px solid transparent; }
            QListWidget::item:selected { background-color: #2b2b2b; color: #fff; border-left: 4px solid #4F46E5; }
            QListWidget::item:hover:!selected { background-color: #222; color: #e5e7eb; }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar Layer
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("background-color: #1e1e1e; border-right: 1px solid #333;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # CyberSolu Logo/Brand Header
        brand_lbl = QLabel("CyberSolu\nDM Engine")
        brand_lbl.setStyleSheet("color: #4F46E5; font-size: 24px; font-weight: 900; padding: 25px 20px; background-color: #1e1e1e;")
        brand_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(brand_lbl)
        
        # Navigation List
        self.nav_list = QListWidget()
        nav_items = ["Dashboard", "Accounts", "Queue", "Message Pool", "Settings", "Logs"]
        for it in nav_items:
            list_item = QListWidgetItem(it)
            self.nav_list.addItem(list_item)
            
        self.nav_list.currentRowChanged.connect(self.change_page)
        sidebar_layout.addWidget(self.nav_list)
        
        # Bottom brand/author
        author_lbl = QLabel("v1.0\nMade by Daniyal Rashid")
        author_lbl.setStyleSheet("color: #6b7280; font-size: 12px; padding: 20px; text-align: center; background-color: #1e1e1e;")
        author_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(author_lbl)
        
        main_layout.addWidget(sidebar)
        
        # Content Layer
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("main_content")
        
        # Initialize panels
        self.panel_dashboard = DashboardPanel(self)
        self.panel_accounts = AccountsPanel(self)
        self.panel_queue = QueuePanel(self)
        self.panel_messages = MessagesPanel(self)
        self.panel_settings = SettingsPanel(self)
        self.panel_logs = LogsPanel(self)
        
        self.content_stack.addWidget(self.panel_dashboard)
        self.content_stack.addWidget(self.panel_accounts)
        self.content_stack.addWidget(self.panel_queue)
        self.content_stack.addWidget(self.panel_messages)
        self.content_stack.addWidget(self.panel_settings)
        self.content_stack.addWidget(self.panel_logs)
        
        main_layout.addWidget(self.content_stack)
        
        self.nav_list.setCurrentRow(0)

    def change_page(self, index):
        self.content_stack.setCurrentIndex(index)
        
        # Refresh specific panes when navigated to
        if index == 1: self.panel_accounts.refresh_table()
        if index == 2: self.panel_queue.refresh_table()
        if index == 5: self.panel_logs.refresh_table()

    # --- Engine Control Wrappers ---
    def start_engine(self):
        if not self.engine.is_running:
            self.panel_dashboard.update_status("Starting...")
            self.engine.start()
        elif self.engine.is_paused:
            self.engine.resume()
            self.panel_dashboard.update_status("Running")
            
    def pause_engine(self):
        if self.engine.is_running and not self.engine.is_paused:
            self.engine.pause()
            self.panel_dashboard.update_status("Paused by User")
            
    def stop_engine(self):
        if self.engine.is_running:
            self.engine.stop()
            self.panel_dashboard.update_status("Stopping...")

    # --- Engine Callbacks ---
    def on_engine_log(self, type_str, msg):
        self.panel_dashboard.lbl_status.setText(f"Engine Log: {type_str} - {msg[:50]}...")
        self.panel_logs.append_log(type_str, msg)
        
    def on_engine_progress(self, sent, failed):
        self.panel_dashboard.update_stats(sent, failed)
        
    def on_engine_status(self, text):
        self.panel_dashboard.update_status(text)
        
    def on_account_switched(self, username):
        self.panel_dashboard.update_account(username)
        
    def on_engine_finished(self):
        self.panel_dashboard.update_status("Session Completed / Stopped")
        self.panel_accounts.refresh_table()
        self.panel_queue.refresh_table()
        self.panel_logs.refresh_table()

    def closeEvent(self, event):
        if self.engine.is_running:
            self.engine.stop()
            self.engine.wait()
        event.accept()
