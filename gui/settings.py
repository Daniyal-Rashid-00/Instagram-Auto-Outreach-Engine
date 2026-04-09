from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QSpinBox, QCheckBox, QTimeEdit,
                             QFrame, QRadioButton, QButtonGroup, QScrollArea)
from PyQt6.QtCore import Qt, QTime
import json
from pathlib import Path
from gui.dialogs import dark_warning, dark_info

# Absolute path to the project-level config dir, works regardless of cwd
_CONFIG_DIR  = Path(__file__).parent.parent / 'config'
_SETTINGS_FILE = _CONFIG_DIR / 'settings.json'


def _make_card():
    card = QFrame()
    card.setObjectName("card")
    return card


def _section_title(text):
    lbl = QLabel(text)
    lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #FFFFFF; margin-bottom: 6px;")
    return lbl


class SettingsPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.settings = {}
        self._init_ui()
        self.load_settings()

    def _init_ui(self):
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(20, 20, 20, 20)
        outer_layout.setSpacing(0)

        header = QLabel("Engine Settings")
        header.setObjectName("headerTitle")
        outer_layout.addWidget(header)
        outer_layout.addSpacing(16)

        # Scroll area so content never clips on small windows
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 12, 0)
        main_layout.setSpacing(16)

        # ── Card 1: Anti-Ban Delays ────────────────────────────────────────
        delay_card = _make_card()
        delay_layout = QVBoxLayout(delay_card)
        delay_layout.setContentsMargins(20, 16, 20, 16)
        delay_layout.setSpacing(12)
        delay_layout.addWidget(_section_title("Anti-Ban Delays"))

        desc = QLabel("Random delay injected between each DM to simulate human behaviour.")
        desc.setObjectName("subHeader")
        delay_layout.addWidget(desc)

        row1 = QHBoxLayout()
        row1.setSpacing(12)
        lbl_min = QLabel("Minimum Delay (seconds):")
        lbl_min.setFixedWidth(220)
        self.spin_min = QSpinBox()
        self.spin_min.setRange(10, 600)
        self.spin_min.setFixedWidth(100)
        row1.addWidget(lbl_min)
        row1.addWidget(self.spin_min)
        row1.addStretch()
        delay_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(12)
        lbl_max = QLabel("Maximum Delay (seconds):")
        lbl_max.setFixedWidth(220)
        self.spin_max = QSpinBox()
        self.spin_max.setRange(10, 1200)
        self.spin_max.setFixedWidth(100)
        row2.addWidget(lbl_max)
        row2.addWidget(self.spin_max)
        row2.addStretch()
        delay_layout.addLayout(row2)

        main_layout.addWidget(delay_card)

        # ── Card 2: Account Limits ─────────────────────────────────────────
        acc_card = _make_card()
        acc_layout = QVBoxLayout(acc_card)
        acc_layout.setContentsMargins(20, 16, 20, 16)
        acc_layout.setSpacing(12)
        acc_layout.addWidget(_section_title("Account Limits"))

        row3 = QHBoxLayout()
        row3.setSpacing(12)
        lbl_limit = QLabel("Daily DM Limit per account:")
        lbl_limit.setFixedWidth(220)
        self.spin_limit = QSpinBox()
        self.spin_limit.setRange(5, 500)
        self.spin_limit.setFixedWidth(100)
        row3.addWidget(lbl_limit)
        row3.addWidget(self.spin_limit)
        row3.addStretch()
        acc_layout.addLayout(row3)

        main_layout.addWidget(acc_card)

        # ── Card 3: Queue Processing Order ────────────────────────────────
        order_card = _make_card()
        order_layout = QVBoxLayout(order_card)
        order_layout.setContentsMargins(20, 16, 20, 16)
        order_layout.setSpacing(12)
        order_layout.addWidget(_section_title("Queue Processing Order"))

        self.radio_seq = QRadioButton("Sequential (Top to Bottom)")
        self.radio_rand = QRadioButton("Randomized")
        self.order_group = QButtonGroup()
        self.order_group.addButton(self.radio_seq, 1)
        self.order_group.addButton(self.radio_rand, 2)

        radio_row = QHBoxLayout()
        radio_row.addWidget(self.radio_seq)
        radio_row.addSpacing(30)
        radio_row.addWidget(self.radio_rand)
        radio_row.addStretch()
        order_layout.addLayout(radio_row)

        main_layout.addWidget(order_card)

        # ── Card 4: Advanced Delay Mode ───────────────────────────────────
        gaussian_card = _make_card()
        gaussian_layout = QVBoxLayout(gaussian_card)
        gaussian_layout.setContentsMargins(20, 16, 20, 16)
        gaussian_layout.setSpacing(8)
        gaussian_layout.addWidget(_section_title("Advanced Delay Mode"))

        self.chk_gaussian = QCheckBox("Enable Gaussian (Human-Curve) Delays")
        gaussian_layout.addWidget(self.chk_gaussian)

        gaussian_desc = QLabel(
            "When enabled, delays use a bell-curve distribution instead of a flat random range,\n"
            "making the timing pattern statistically indistinguishable from a real human."
        )
        gaussian_desc.setObjectName("subHeader")
        gaussian_layout.addWidget(gaussian_desc)

        main_layout.addWidget(gaussian_card)

        # ── Card 5: Scheduling Windows ────────────────────────────────────
        sched_card = _make_card()
        sched_layout = QVBoxLayout(sched_card)
        sched_layout.setContentsMargins(20, 16, 20, 16)
        sched_layout.setSpacing(12)
        sched_layout.addWidget(_section_title("Scheduling Windows"))

        self.chk_schedule = QCheckBox("Enable Scheduling")
        sched_layout.addWidget(self.chk_schedule)

        time_row = QHBoxLayout()
        time_row.setSpacing(12)
        time_row.addWidget(QLabel("Start Time:"))
        self.time_start = QTimeEdit()
        self.time_start.setDisplayFormat("HH:mm")
        self.time_start.setFixedWidth(90)
        time_row.addWidget(self.time_start)
        time_row.addSpacing(20)
        time_row.addWidget(QLabel("End Time:"))
        self.time_end = QTimeEdit()
        self.time_end.setDisplayFormat("HH:mm")
        self.time_end.setFixedWidth(90)
        time_row.addWidget(self.time_end)
        time_row.addStretch()
        sched_layout.addLayout(time_row)

        main_layout.addWidget(sched_card)

        # ── Card 6: Appearance ─────────────────────────────────────
        appear_card = _make_card()
        appear_layout = QVBoxLayout(appear_card)
        appear_layout.setContentsMargins(20, 16, 20, 16)
        appear_layout.setSpacing(12)
        appear_layout.addWidget(_section_title("Appearance"))

        appear_desc = QLabel(
            "Switch between GitHub Dark and GitHub Light themes. Applied immediately on Save."
        )
        appear_desc.setObjectName("subHeader")
        appear_desc.setWordWrap(True)
        appear_layout.addWidget(appear_desc)

        self.radio_dark  = QRadioButton("🌙  Dark Theme (GitHub Dark)")
        self.radio_light = QRadioButton("☀️  Light Theme (GitHub Light)")
        self.theme_group = QButtonGroup()
        self.theme_group.addButton(self.radio_dark,  1)
        self.theme_group.addButton(self.radio_light, 2)
        self.radio_dark.setChecked(True)  # default

        theme_row = QHBoxLayout()
        theme_row.addWidget(self.radio_dark)
        theme_row.addSpacing(30)
        theme_row.addWidget(self.radio_light)
        theme_row.addStretch()
        appear_layout.addLayout(theme_row)

        main_layout.addWidget(appear_card)
        main_layout.addStretch()

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

        # Save button pinned at the bottom, outside scroll
        outer_layout.addSpacing(12)
        self.btn_save = QPushButton("Save Settings")
        self.btn_save.setObjectName("btnSuccess")
        self.btn_save.clicked.connect(self.save_settings)
        outer_layout.addWidget(self.btn_save)

        self.setLayout(outer_layout)

    # ── Data ──────────────────────────────────────────────────────────────

    def load_settings(self):
        if _SETTINGS_FILE.exists():
            with open(_SETTINGS_FILE, 'r') as f:
                self.settings = json.load(f)
        else:
            self.settings = {
                "delay_min": 45, "delay_max": 60, "daily_limit": 50,
                "send_order": "sequential", "schedule_enabled": False,
                "schedule_start": "20:00", "schedule_end": "23:00",
                "use_gaussian_delays": False
            }

        self.spin_min.setValue(self.settings.get("delay_min", 45))
        self.spin_max.setValue(self.settings.get("delay_max", 60))
        self.spin_limit.setValue(self.settings.get("daily_limit", 50))

        if self.settings.get("send_order", "sequential") == "sequential":
            self.radio_seq.setChecked(True)
        else:
            self.radio_rand.setChecked(True)

        self.chk_schedule.setChecked(self.settings.get("schedule_enabled", False))
        self.chk_gaussian.setChecked(self.settings.get("use_gaussian_delays", False))

        if self.settings.get("theme", "dark") == "dark":
            self.radio_dark.setChecked(True)
        else:
            self.radio_light.setChecked(True)

        start_t = QTime.fromString(self.settings.get("schedule_start", "20:00"), "HH:mm")
        end_t = QTime.fromString(self.settings.get("schedule_end", "23:00"), "HH:mm")
        self.time_start.setTime(start_t)
        self.time_end.setTime(end_t)

    def save_settings(self):
        min_v = self.spin_min.value()
        max_v = self.spin_max.value()

        if min_v >= max_v:
            dark_warning(self, "Invalid Delay", "Minimum delay must be less than maximum delay.")
            return

        self.settings = {
            "delay_min": min_v,
            "delay_max": max_v,
            "daily_limit": self.spin_limit.value(),
            "send_order": "sequential" if self.radio_seq.isChecked() else "random",
            "schedule_enabled": self.chk_schedule.isChecked(),
            "schedule_start": self.time_start.time().toString("HH:mm"),
            "schedule_end": self.time_end.time().toString("HH:mm"),
            "use_gaussian_delays": self.chk_gaussian.isChecked(),
            "theme": "dark" if self.radio_dark.isChecked() else "light",
        }

        _CONFIG_DIR.mkdir(exist_ok=True)
        with open(_SETTINGS_FILE, 'w') as f:
            json.dump(self.settings, f, indent=2)

        # Apply theme immediately
        self.main_window.apply_theme(self.settings['theme'])

        dark_info(self, "Settings Saved", "Preferences updated successfully.\nChanges will take effect on the next engine session.")
