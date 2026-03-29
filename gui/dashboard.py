from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
from PyQt6.QtCore import Qt

class DashboardPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window # Reference to main window to control engine
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Dashboard")
        header.setObjectName("headerTitle")
        layout.addWidget(header)
        
        # Controls Group
        controls_frame = QFrame()
        controls_frame.setObjectName("card")
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(20, 20, 20, 20)
        
        self.btn_start = QPushButton("Start Engine")
        self.btn_start.setObjectName("btnStart")
        self.btn_start.clicked.connect(self.main_window.start_engine)
        
        self.btn_pause = QPushButton("Pause Engine")
        self.btn_pause.setObjectName("btnWarning")
        self.btn_pause.clicked.connect(self.main_window.pause_engine)
        
        self.btn_stop = QPushButton("Stop Engine")
        self.btn_stop.setObjectName("btnDanger")
        self.btn_stop.clicked.connect(self.main_window.stop_engine)
        
        controls_layout.addWidget(self.btn_start)
        controls_layout.addWidget(self.btn_pause)
        controls_layout.addWidget(self.btn_stop)
        
        layout.addWidget(controls_frame)
        
        # Stats Group
        stats_layout = QHBoxLayout()
        self.lbl_active_account = self._create_stat_card("Active Account", "None")
        self.lbl_sent_today = self._create_stat_card("Session Sent", "0")
        self.lbl_failed = self._create_stat_card("Session Failed", "0")
        
        stats_layout.addWidget(self.lbl_active_account)
        stats_layout.addWidget(self.lbl_sent_today)
        stats_layout.addWidget(self.lbl_failed)
        
        layout.addLayout(stats_layout)
        
        # Status Log summary
        self.lbl_status = QLabel("Engine Status: Stopped")
        self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #818CF8; padding: 15px; background: #1E293B; border-radius: 8px; border: 1px solid #334155;")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_status)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def _create_stat_card(self, title, initial_value):
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_title = QLabel(title)
        lbl_title.setObjectName("subHeader")
        
        lbl_value = QLabel(initial_value)
        lbl_value.setStyleSheet("color: white; font-size: 32px; font-weight: 900;")
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # We attach the label widget itself to the frame as a property so we can update it
        frame.value_label = lbl_value
        return frame
        
    def update_stats(self, sent, failed):
        self.lbl_sent_today.value_label.setText(str(sent))
        self.lbl_failed.value_label.setText(str(failed))
        
    def update_account(self, username):
        self.lbl_active_account.value_label.setText(username)
        
    def update_status(self, text):
        self.lbl_status.setText(f"Engine Status: {text}")
