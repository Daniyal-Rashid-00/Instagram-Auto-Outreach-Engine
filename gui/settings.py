from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QSpinBox, QCheckBox, QTimeEdit, QMessageBox, QGroupBox, QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt, QTime
import json
from pathlib import Path

class SettingsPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.settings = {}
        self._init_ui()
        self.load_settings()
        
    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(25)
        
        header = QLabel("Engine Settings")
        header.setObjectName("headerTitle")
        main_layout.addWidget(header)
        
        # Delay Group
        delay_group = QGroupBox("Anti-Ban Delays")
        delay_layout = QVBoxLayout()
        
        help_lbl = QLabel("Random delay injected between each DM to simulate human behavior.")
        help_lbl.setObjectName("subHeader")
        delay_layout.addWidget(help_lbl)
        
        min_layout = QHBoxLayout()
        min_layout.addWidget(QLabel("Minimum Delay (seconds):"))
        self.spin_min = QSpinBox()
        self.spin_min.setRange(10, 600)
        min_layout.addWidget(self.spin_min)
        min_layout.addStretch()
        
        max_layout = QHBoxLayout()
        max_layout.addWidget(QLabel("Maximum Delay (seconds):"))
        self.spin_max = QSpinBox()
        self.spin_max.setRange(10, 1200)
        max_layout.addWidget(self.spin_max)
        max_layout.addStretch()
        
        delay_layout.addLayout(min_layout)
        delay_layout.addLayout(max_layout)
        delay_group.setLayout(delay_layout)
        main_layout.addWidget(delay_group)
        
        # Account Group
        acc_group = QGroupBox("Account Limits")
        acc_layout = QHBoxLayout()
        acc_layout.addWidget(QLabel("Daily DM Limit per account:"))
        self.spin_limit = QSpinBox()
        self.spin_limit.setRange(5, 500)
        acc_layout.addWidget(self.spin_limit)
        acc_layout.addStretch()
        acc_group.setLayout(acc_layout)
        main_layout.addWidget(acc_group)
        
        # Order Group
        order_group = QGroupBox("Queue Processing Order")
        order_layout = QHBoxLayout()
        self.radio_seq = QRadioButton("Sequential (Top to Bottom)")
        self.radio_rand = QRadioButton("Randomized")
        self.order_group = QButtonGroup()
        self.order_group.addButton(self.radio_seq, 1)
        self.order_group.addButton(self.radio_rand, 2)
        order_layout.addWidget(self.radio_seq)
        order_layout.addWidget(self.radio_rand)
        order_layout.addStretch()
        order_group.setLayout(order_layout)
        main_layout.addWidget(order_group)
        
        # Scheduling Group
        sched_group = QGroupBox("Scheduling Windows")
        sched_layout = QVBoxLayout()
        
        self.chk_schedule = QCheckBox("Enable Scheduling")
        sched_layout.addWidget(self.chk_schedule)
        
        times_layout = QHBoxLayout()
        times_layout.addWidget(QLabel("Start Time:"))
        self.time_start = QTimeEdit()
        self.time_start.setDisplayFormat("HH:mm")
        times_layout.addWidget(self.time_start)
        
        times_layout.addWidget(QLabel("End Time:"))
        self.time_end = QTimeEdit()
        self.time_end.setDisplayFormat("HH:mm")
        times_layout.addWidget(self.time_end)
        times_layout.addStretch()
        
        sched_layout.addLayout(times_layout)
        sched_group.setLayout(sched_layout)
        main_layout.addWidget(sched_group)
        
        # Save Button
        self.btn_save = QPushButton("Save Settings")
        self.btn_save.setObjectName("btnSuccess")
        self.btn_save.clicked.connect(self.save_settings)
        main_layout.addWidget(self.btn_save)
        
        main_layout.addStretch()
        self.setLayout(main_layout)

    def load_settings(self):
        settings_path = Path('config/settings.json')
        if settings_path.exists():
            with open(settings_path, 'r') as f:
                self.settings = json.load(f)
        else:
            self.settings = {
                "delay_min": 45, "delay_max": 60, "daily_limit": 50,
                "send_order": "sequential", "schedule_enabled": False,
                "schedule_start": "20:00", "schedule_end": "23:00"
            }
            
        self.spin_min.setValue(self.settings.get("delay_min", 45))
        self.spin_max.setValue(self.settings.get("delay_max", 60))
        self.spin_limit.setValue(self.settings.get("daily_limit", 50))
        
        if self.settings.get("send_order", "sequential") == "sequential":
            self.radio_seq.setChecked(True)
        else:
            self.radio_rand.setChecked(True)
            
        self.chk_schedule.setChecked(self.settings.get("schedule_enabled", False))
        
        start_t = QTime.fromString(self.settings.get("schedule_start", "20:00"), "HH:mm")
        end_t = QTime.fromString(self.settings.get("schedule_end", "23:00"), "HH:mm")
        self.time_start.setTime(start_t)
        self.time_end.setTime(end_t)

    def save_settings(self):
        min_v = self.spin_min.value()
        max_v = self.spin_max.value()
        
        if min_v >= max_v:
             QMessageBox.warning(self, "Invalid Delay", "Minimum delay must be less than maximum delay.")
             return
             
        self.settings = {
            "delay_min": min_v,
            "delay_max": max_v,
            "daily_limit": self.spin_limit.value(),
            "send_order": "sequential" if self.radio_seq.isChecked() else "random",
            "schedule_enabled": self.chk_schedule.isChecked(),
            "schedule_start": self.time_start.time().toString("HH:mm"),
            "schedule_end": self.time_end.time().toString("HH:mm")
        }
        
        Path('config').mkdir(exist_ok=True)
        with open('config/settings.json', 'w') as f:
            json.dump(self.settings, f, indent=2)
            
        QMessageBox.information(self, "Settings Saved", "Preferences updated successfully. Changes will take effect on the next session.")
