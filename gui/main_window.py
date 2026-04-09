from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QStackedWidget, QLabel, QListWidgetItem
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont

from gui.dashboard import DashboardPanel
from gui.accounts import AccountsPanel
from gui.queue_panel import QueuePanel
from gui.messages import MessagesPanel
from gui.followup import FollowupPanel
from gui.settings import SettingsPanel
from gui.logs import LogsPanel
from gui.support import SupportPanel
from gui.proxies import ProxiesPanel
from gui.dialogs import dark_info
from core.dm_engine import DMEngine

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CyberSolu DM Engine")
        self.setWindowIcon(QIcon("icon.ico"))
        self.setMinimumSize(1050, 750)
        
        # Engine Thread
        self.engine = DMEngine()
        self.engine.log_signal.connect(self.on_engine_log)
        self.engine.progress_signal.connect(self.on_engine_progress)
        self.engine.status_signal.connect(self.on_engine_status)
        self.engine.account_switched_signal.connect(self.on_account_switched)
        self.engine.finished_signal.connect(self.on_engine_finished)
        self.engine.restriction_signal.connect(self.on_restriction_detected)
        self.engine.queue_completed_signal.connect(self.on_queue_completed)
        
        self._init_ui()
        
    def _init_ui(self):
        # Apply theme from saved settings (or default dark)
        import json
        from pathlib import Path as _Path
        _settings_file = _Path(__file__).parent.parent / 'config' / 'settings.json'
        _theme = 'dark'
        if _settings_file.exists():
            try:
                with open(_settings_file) as f:
                    _theme = json.load(f).get('theme', 'dark')
            except Exception:
                pass
        self.apply_theme(_theme)
            
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar Layer
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(260)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 30, 0, 20)
        sidebar_layout.setSpacing(10)
        
        # CyberSolu Logo UI
        logo_lbl = QLabel()
        from PyQt6.QtGui import QPixmap
        pixmap = QPixmap("icon.ico")
        if not pixmap.isNull():
            logo_lbl.setPixmap(pixmap.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(logo_lbl)
        
        brand_lbl = QLabel("CyberSolu")
        brand_lbl.setObjectName("brandName")
        brand_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(brand_lbl)
        
        subtitle_lbl = QLabel("DM ENGINE v2.0")
        subtitle_lbl.setObjectName("subHeader")
        subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(subtitle_lbl)
        
        sidebar_layout.addSpacing(30)
        
        # Navigation List
        self.nav_list = QListWidget()
        nav_items = [
            "Dashboard", "Accounts", "Proxies", "Queue",
            "Message Pool", "Follow-ups", "Settings", "Logs", "Support"
        ]
        for it in nav_items:
            list_item = QListWidgetItem(it)
            self.nav_list.addItem(list_item)
            
        self.nav_list.currentRowChanged.connect(self.change_page)
        sidebar_layout.addWidget(self.nav_list)
        
        # Bottom brand/author
        author_lbl = QLabel("Built by Daniyal Rashid")
        author_lbl.setObjectName("authorLabel")
        author_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(author_lbl)
        
        main_layout.addWidget(sidebar)
        
        # Content Layer
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("main_content")
        
        # Initialize panels
        self.panel_dashboard = DashboardPanel(self)
        self.panel_accounts  = AccountsPanel(self)
        self.panel_proxies   = ProxiesPanel(self)
        self.panel_queue     = QueuePanel(self)
        self.panel_messages  = MessagesPanel(self)
        self.panel_followup  = FollowupPanel(self)
        self.panel_settings  = SettingsPanel(self)
        self.panel_logs      = LogsPanel(self)
        self.panel_support   = SupportPanel(self)

        self.content_stack.addWidget(self.panel_dashboard)  # 0
        self.content_stack.addWidget(self.panel_accounts)   # 1
        self.content_stack.addWidget(self.panel_proxies)    # 2
        self.content_stack.addWidget(self.panel_queue)      # 3
        self.content_stack.addWidget(self.panel_messages)   # 4
        self.content_stack.addWidget(self.panel_followup)   # 5
        self.content_stack.addWidget(self.panel_settings)   # 6
        self.content_stack.addWidget(self.panel_logs)       # 7
        self.content_stack.addWidget(self.panel_support)    # 8
        
        main_layout.addWidget(self.content_stack)
        
        self.nav_list.setCurrentRow(0)

    def change_page(self, index):
        self.content_stack.setCurrentIndex(index)
        # 0=Dashboard, 1=Accounts, 2=Proxies, 3=Queue, 4=Messages
        # 5=Follow-ups, 6=Settings, 7=Logs, 8=Support
        if index == 1: self.panel_accounts.refresh_table()
        if index == 2: self.panel_proxies.refresh_table()
        if index == 3: self.panel_queue.refresh_table()
        if index == 5: self.panel_followup.refresh_tables()
        if index == 7: self.panel_logs.refresh_table()

    # --- Engine Control Wrappers ---
    def start_engine(self):
        if not self.engine.is_running:
            # Read the Follow-up Only toggle from the dashboard before launch
            self.engine.set_followup_only(self.panel_dashboard.followup_only)
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
        self.panel_dashboard.lbl_status.setText(f"[{type_str}] {msg[:70]}")
        self.panel_dashboard.append_log(type_str, msg)   # mirror to dashboard live feed
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
        self.panel_proxies.refresh_table()
        self.panel_queue.refresh_table()
        self.panel_logs.refresh_table()
        self.panel_followup.refresh_tables()

    def on_queue_completed(self, sent, failed):
        """Called when the engine exhausts the queue naturally."""
        dark_info(
            self, "Campaign Complete! 🎉",
            f"All queued DMs have been processed.\n"
            f"✅ Sent: {sent}    ❌ Failed: {failed}\n\n"
            f"Check the Logs panel for the full session report."
        )
        self.nav_list.setCurrentRow(0)

    def on_restriction_detected(self, account, reason):
        """Called when the engine fires restriction_signal."""
        self.panel_dashboard.show_restriction_alert(account, reason)
        # Also switch to dashboard so user sees it immediately
        self.nav_list.setCurrentRow(0)

    def apply_theme(self, theme='dark'):
        """Swap the global stylesheet between dark and light."""
        from pathlib import Path as _Path
        qss_file = 'style.qss' if theme == 'dark' else 'style_light.qss'
        qss_path = _Path(__file__).parent / qss_file
        try:
            with open(qss_path, 'r') as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Could not load {theme} stylesheet: {e}")

    def closeEvent(self, event):
        if self.engine.is_running:
            self.engine.stop()
            self.engine.wait()
        event.accept()
