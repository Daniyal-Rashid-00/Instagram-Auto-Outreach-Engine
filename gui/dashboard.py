from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor
from datetime import datetime, date
from data.db import get_connection


class DashboardPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.conn = get_connection()
        self._fu_only = False
        self._init_ui()
        self.refresh_stats()

    # ── UI Build ───────────────────────────────────────────────────────────────

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # ── Header ──────────────────────────────────────────────────────────
        hdr_row = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setObjectName("headerTitle")
        hdr_row.addWidget(title)
        hdr_row.addStretch()
        btn_refresh = QPushButton("⟳  Refresh Stats")
        btn_refresh.clicked.connect(self.refresh_stats)
        hdr_row.addWidget(btn_refresh)
        root.addLayout(hdr_row)

        # ── Engine Controls Card ─────────────────────────────────────────────
        controls_card = QFrame()
        controls_card.setObjectName("card")
        ctrl_layout = QHBoxLayout(controls_card)
        ctrl_layout.setContentsMargins(16, 14, 16, 14)
        ctrl_layout.setSpacing(10)

        self.btn_start = QPushButton("▶  Start Engine")
        self.btn_start.setObjectName("btnStart")
        self.btn_start.setMinimumHeight(38)
        self.btn_start.clicked.connect(self.main_window.start_engine)

        self.btn_pause = QPushButton("⏸  Pause")
        self.btn_pause.setObjectName("btnWarning")
        self.btn_pause.setMinimumHeight(38)
        self.btn_pause.clicked.connect(self.main_window.pause_engine)

        self.btn_stop = QPushButton("⏹  Stop")
        self.btn_stop.setObjectName("btnDanger")
        self.btn_stop.setMinimumHeight(38)
        self.btn_stop.clicked.connect(self.main_window.stop_engine)

        # Follow-up Only toggle
        self.btn_fu_toggle = QPushButton("↩  Follow-up Only: OFF")
        self.btn_fu_toggle.setObjectName("btnSecondary")
        self.btn_fu_toggle.setMinimumHeight(38)
        self.btn_fu_toggle.setCheckable(True)
        self.btn_fu_toggle.toggled.connect(self._on_fu_toggle)

        ctrl_layout.addWidget(self.btn_start)
        ctrl_layout.addWidget(self.btn_pause)
        ctrl_layout.addWidget(self.btn_stop)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.btn_fu_toggle)
        root.addWidget(controls_card)

        # ── Restriction Alert Banner ─────────────────────────────────────────
        self.restriction_banner = QFrame()
        self.restriction_banner.setStyleSheet(
            "background-color: #3D1A1A; border: 1px solid #DA3633; border-radius: 6px;"
        )
        banner_row = QHBoxLayout(self.restriction_banner)
        banner_row.setContentsMargins(14, 10, 14, 10)
        banner_row.setSpacing(12)
        banner_icon = QLabel("🛑")
        banner_icon.setStyleSheet("font-size: 20px; background: transparent;")
        banner_row.addWidget(banner_icon)
        self.banner_text = QLabel("Restriction detected")
        self.banner_text.setStyleSheet(
            "color: #FF7B72; font-size: 13px; font-weight: 600; background: transparent;"
        )
        self.banner_text.setWordWrap(True)
        banner_row.addWidget(self.banner_text, 1)
        btn_dismiss = QPushButton("Dismiss")
        btn_dismiss.setObjectName("btnDanger")
        btn_dismiss.setFixedWidth(90)
        btn_dismiss.clicked.connect(self.clear_restriction_alert)
        banner_row.addWidget(btn_dismiss)
        self.restriction_banner.hide()
        root.addWidget(self.restriction_banner)

        # ── KPI Row 1: All-time metrics ──────────────────────────────────────
        kpi1_layout = QHBoxLayout()
        kpi1_layout.setSpacing(12)
        self.kpi_total_sent   = self._kpi_card("Total DMs Sent",  "0",   "#3B82F6")
        self.kpi_success_rate = self._kpi_card("Success Rate",    "N/A", "#10B981")
        self.kpi_total_failed = self._kpi_card("Total Failed",    "0",   "#EF4444")
        for c in (self.kpi_total_sent, self.kpi_success_rate, self.kpi_total_failed):
            kpi1_layout.addWidget(c)
        root.addLayout(kpi1_layout)

        # ── KPI Row 2: Queue metrics ─────────────────────────────────────────
        kpi2_layout = QHBoxLayout()
        kpi2_layout.setSpacing(12)
        self.kpi_in_queue    = self._kpi_card("In Queue",           "0", "#F59E0B")
        self.kpi_pending_fu  = self._kpi_card("Pending Follow-ups", "0", "#8B5CF6")
        self.kpi_active_accs = self._kpi_card("Active Accounts",    "0", "#06B6D4")
        for c in (self.kpi_in_queue, self.kpi_pending_fu, self.kpi_active_accs):
            kpi2_layout.addWidget(c)
        root.addLayout(kpi2_layout)

        # ── Bottom: Session Activity  |  Live Log ────────────────────────────
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)

        # Left — Session Activity card
        act_card = QFrame()
        act_card.setObjectName("card")
        act_vbox = QVBoxLayout(act_card)
        act_vbox.setContentsMargins(18, 14, 18, 14)
        act_vbox.setSpacing(10)

        act_title = QLabel("Session Activity")
        act_title.setStyleSheet("font-size: 13px; font-weight: 700; letter-spacing: 0.5px;")
        act_vbox.addWidget(act_title)

        # Status pill
        status_pill_row = QHBoxLayout()
        self._status_dot = QLabel("●")
        self.lbl_status_text = QLabel("Stopped")
        self._status_dot.setStyleSheet("font-size: 18px;")
        self.lbl_status_text.setStyleSheet("font-size: 13px; font-weight: 700;")
        self._set_status_color("Stopped")
        status_pill_row.addWidget(self._status_dot)
        status_pill_row.addWidget(self.lbl_status_text)
        status_pill_row.addStretch()
        act_vbox.addLayout(status_pill_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("separator")
        act_vbox.addWidget(sep)

        # Mini stats
        self._lbl_active_account = self._mini_row(act_vbox, "Active Account", "None")
        self._lbl_sent_today      = self._mini_row(act_vbox, "Sent Today",     "0")
        self._lbl_session_sent    = self._mini_row(act_vbox, "Session Sent",   "0")
        self._lbl_session_failed  = self._mini_row(act_vbox, "Session Failed", "0")

        act_vbox.addStretch()
        bottom_row.addWidget(act_card, 1)

        # Right — Live Log card
        log_card = QFrame()
        log_card.setObjectName("card")
        log_vbox = QVBoxLayout(log_card)
        log_vbox.setContentsMargins(16, 14, 16, 14)
        log_vbox.setSpacing(8)

        log_title = QLabel("Live Engine Log")
        log_title.setStyleSheet("font-size: 13px; font-weight: 700; letter-spacing: 0.5px;")
        log_vbox.addWidget(log_title)

        self.live_log = QTextEdit()
        self.live_log.setReadOnly(True)
        self.live_log.setStyleSheet("font-family: Consolas, monospace; font-size: 12px;")
        log_vbox.addWidget(self.live_log)

        bottom_row.addWidget(log_card, 2)

        root.addLayout(bottom_row, 1)

    # ── Widget Factories ───────────────────────────────────────────────────────

    def _kpi_card(self, label, value, color):
        card = QFrame()
        card.setObjectName("card")
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(18, 14, 18, 14)
        vbox.setSpacing(4)

        lbl_title = QLabel(label.upper())
        lbl_title.setStyleSheet(
            f"font-size: 10px; font-weight: 700; letter-spacing: 1.2px; color: {color};"
        )
        lbl_val = QLabel(value)
        lbl_val.setStyleSheet(f"font-size: 30px; font-weight: 900; color: {color};")

        vbox.addWidget(lbl_title)
        vbox.addWidget(lbl_val)

        card._val_lbl = lbl_val
        return card

    def _mini_row(self, parent_layout, label, value):
        """Add a label:value row to parent_layout and return the value QLabel."""
        row = QHBoxLayout()
        row.setSpacing(6)
        lbl = QLabel(label + ":")
        lbl.setObjectName("subHeader")
        lbl.setFixedWidth(130)
        val = QLabel(value)
        val.setStyleSheet("font-weight: 700;")
        row.addWidget(lbl)
        row.addWidget(val)
        row.addStretch()
        parent_layout.addLayout(row)
        return val

    # ── Follow-up Only Toggle ──────────────────────────────────────────────────

    def _on_fu_toggle(self, checked):
        self._fu_only = checked
        if checked:
            self.btn_fu_toggle.setText("↩  Follow-up Only: ON")
            self.btn_fu_toggle.setStyleSheet(
                "background-color: #6D28D9; color: #FFFFFF; "
                "border: 1px solid #7C3AED; border-radius: 6px;"
            )
        else:
            self.btn_fu_toggle.setText("↩  Follow-up Only: OFF")
            self.btn_fu_toggle.setStyleSheet("")  # revert to global stylesheet

    @property
    def followup_only(self):
        return self._fu_only

    # ── Status Helper ──────────────────────────────────────────────────────────

    def _set_status_color(self, text):
        mapping = {
            "running":   "#10B981",
            "paused":    "#F59E0B",
            "starting":  "#3B82F6",
            "stopped":   "#8B949E",
            "completed": "#10B981",
            "failed":    "#EF4444",
        }
        lower = text.lower()
        color = next((v for k, v in mapping.items() if k in lower), "#8B949E")
        self._status_dot.setStyleSheet(
            f"font-size: 18px; color: {color}; background: transparent;"
        )
        self.lbl_status_text.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {color};"
        )

    # ── Data Refresh ───────────────────────────────────────────────────────────

    def refresh_stats(self):
        try:
            c = self.conn.cursor()
            today = date.today().isoformat()

            # Total DMs sent (all time)
            c.execute("SELECT COUNT(*) as n FROM sent_log")
            self.kpi_total_sent._val_lbl.setText(str(c.fetchone()['n']))

            # Sent today
            c.execute(
                "SELECT COUNT(*) as n FROM sent_log WHERE date(sent_at) = ?", (today,)
            )
            self._lbl_sent_today.setText(str(c.fetchone()['n']))

            # Success rate + Failed (from queue history)
            c.execute("SELECT status, COUNT(*) as n FROM queue GROUP BY status")
            counts = {row['status']: row['n'] for row in c.fetchall()}
            sent_q   = counts.get('Sent', 0)
            failed_q = counts.get('Failed', 0)
            total_q  = sent_q + failed_q
            rate = f"{int(sent_q / total_q * 100)}%" if total_q else "N/A"
            self.kpi_success_rate._val_lbl.setText(rate)
            self.kpi_total_failed._val_lbl.setText(str(failed_q))

            # In queue (Pending only, not follow-up)
            pending = counts.get('Pending', 0)
            self.kpi_in_queue._val_lbl.setText(str(pending))

            # Pending follow-ups
            c.execute("SELECT COUNT(*) as n FROM followup_queue WHERE status = 'Pending'")
            self.kpi_pending_fu._val_lbl.setText(str(c.fetchone()['n']))

            # Active accounts
            c.execute("SELECT COUNT(*) as n FROM accounts WHERE status = 'Active'")
            self.kpi_active_accs._val_lbl.setText(str(c.fetchone()['n']))

        except Exception as e:
            pass  # silently ignore if DB not ready yet

    # ── Engine Signal Receivers ────────────────────────────────────────────────

    def update_stats(self, sent, failed):
        self._lbl_session_sent.setText(str(sent))
        self._lbl_session_failed.setText(str(failed))
        self.refresh_stats()

    def update_account(self, username):
        self._lbl_active_account.setText(f"@{username}")

    def update_status(self, text):
        self.lbl_status_text.setText(text)
        self._set_status_color(text)

    def show_restriction_alert(self, account, reason):
        self.banner_text.setText(
            f"⚠  Account @{account} may be restricted — {reason}"
        )
        self.restriction_banner.show()

    def clear_restriction_alert(self):
        self.restriction_banner.hide()

    def append_log(self, msg_type, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "ERROR":   "#EF4444",
            "SUCCESS": "#10B981",
            "INFO":    "#3B82F6",
            "WARN":    "#F59E0B",
        }
        color = colors.get(msg_type, "#a3a3a3")
        html = (
            f'<span style="color:{color}">[{timestamp}] '
            f'[{msg_type}] {message}</span><br>'
        )
        cursor = self.live_log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.live_log.setTextCursor(cursor)
        self.live_log.insertHtml(html)
        self.live_log.verticalScrollBar().setValue(
            self.live_log.verticalScrollBar().maximum()
        )

    # ── Legacy compat (main_window uses these by name) ─────────────────────────

    @property
    def lbl_active_account(self):
        """Compat shim — main_window.on_account_switched → update_account()."""
        class _Shim:
            def __init__(self, panel):
                self.panel = panel
            @property
            def value_label(self):
                return self.panel._lbl_active_account
        return _Shim(self)

    @property
    def lbl_sent_today(self):
        class _Shim:
            def __init__(self, panel):
                self.panel = panel
            @property
            def value_label(self):
                return self.panel._lbl_session_sent
        return _Shim(self)

    @property
    def lbl_failed(self):
        class _Shim:
            def __init__(self, panel):
                self.panel = panel
            @property
            def value_label(self):
                return self.panel._lbl_session_failed
        return _Shim(self)

    @property
    def lbl_status(self):
        """Compat shim: main_window.on_engine_log writes to lbl_status.setText()."""
        return self.lbl_status_text
