from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QAbstractItemView, QLineEdit, QMenu, QWidgetAction
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from data.db import get_connection
from core.queue_manager import QueueManager
from gui.dialogs import dark_info, dark_warning, dark_question


# ── Helper ─────────────────────────────────────────────────────────────────────
def _make_card():
    f = QFrame()
    f.setObjectName("card")
    return f


def _section_title(text):
    lbl = QLabel(text)
    lbl.setStyleSheet("font-size: 13px; font-weight: 700; letter-spacing: 0.4px;")
    return lbl


class FollowupPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.conn = get_connection()
        self.queue_manager = QueueManager()
        self._init_ui()
        self.refresh_tables()

    # ── UI Build ───────────────────────────────────────────────────────────────

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # ── Page Header ────────────────────────────────────────────────────────
        hdr_row = QHBoxLayout()
        title = QLabel("Follow-up Campaign")
        title.setObjectName("headerTitle")
        hdr_row.addWidget(title)
        hdr_row.addStretch()
        btn_refresh = QPushButton("⟳  Refresh")
        btn_refresh.clicked.connect(self.refresh_tables)
        hdr_row.addWidget(btn_refresh)
        root.addLayout(hdr_row)

        # ── Stats bar ──────────────────────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self.stat_sent   = self._stat_card("Total Sent", "0",   "#3B82F6")
        self.stat_queued = self._stat_card("In FU Queue", "0",  "#F59E0B")
        self.stat_pending= self._stat_card("Pending FU", "0",   "#10B981")
        for card in (self.stat_sent, self.stat_queued, self.stat_pending):
            stats_row.addWidget(card)
        root.addLayout(stats_row)

        # ── Workflow hint ──────────────────────────────────────────────────────
        hint = QLabel(
            "① Select users from the Sent DM history  →  "
            "② Add them to the Follow-up Queue  →  "
            "③ Click  Queue for Engine  when you're ready to send the follow-up"
        )
        hint.setObjectName("subHeader")
        hint.setWordWrap(True)
        root.addWidget(hint)

        # ── Main splitter ──────────────────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setChildrenCollapsible(False)

        # ─ LEFT: Sent DM History ──────────────────────────────────────────────
        left = _make_card()
        left_vbox = QVBoxLayout(left)
        left_vbox.setContentsMargins(16, 14, 16, 14)
        left_vbox.setSpacing(8)

        # Header row
        left_hdr = QHBoxLayout()
        lbl_step1 = QLabel("① Sent DM History")
        lbl_step1.setStyleSheet("font-size: 14px; font-weight: 700;")
        self.lbl_sent_count = QLabel("0 records")
        self.lbl_sent_count.setObjectName("subHeader")
        left_hdr.addWidget(lbl_step1)
        left_hdr.addStretch()
        left_hdr.addWidget(self.lbl_sent_count)
        left_vbox.addLayout(left_hdr)

        # Selection toolbar (2 rows to prevent squishing)
        sel_row1 = QHBoxLayout()
        sel_row1.setSpacing(6)
        
        self.search_sent = QLineEdit()
        self.search_sent.setPlaceholderText("🔍 Search...")
        self.search_sent.setMinimumHeight(28)
        self.search_sent.textChanged.connect(self.filter_sent_table)

        self._dm_filter_value = None   # None = show all
        self.btn_dm_filter = QPushButton("All Users")
        self.btn_dm_filter.setObjectName("btnSecondary")
        self.btn_dm_filter.setMinimumHeight(28)
        self.btn_dm_filter.clicked.connect(self._show_dm_filter_menu)

        sel_row1.addWidget(self.search_sent)
        sel_row1.addWidget(self.btn_dm_filter)
        
        sel_row2 = QHBoxLayout()
        sel_row2.setSpacing(6)
        
        btn_sel_all   = QPushButton("Select All")
        btn_sel_none  = QPushButton("Select None")
        btn_sel_all.setObjectName("btnSecondary")
        btn_sel_none.setObjectName("btnSecondary")
        btn_sel_all.clicked.connect(self._select_all_sent)
        btn_sel_none.clicked.connect(self._select_none_sent)
        
        sel_row2.addWidget(btn_sel_all)
        sel_row2.addWidget(btn_sel_none)
        sel_row2.addStretch()
        self.lbl_sent_sel = QLabel("0 selected")
        self.lbl_sent_sel.setObjectName("subHeader")
        sel_row2.addWidget(self.lbl_sent_sel)
        
        left_vbox.addLayout(sel_row1)
        left_vbox.addLayout(sel_row2)

        # Table
        self.sent_table = self._build_table(
            ["Username", "Last Sent", "DMs"],
            stretch_col=0, multi=True
        )
        self.sent_table.itemSelectionChanged.connect(self._update_sent_sel_label)
        left_vbox.addWidget(self.sent_table)

        # Action button
        btn_add_fu = QPushButton("  ②  Add Selected  →  Follow-up Queue")
        btn_add_fu.setObjectName("btnSuccess")
        btn_add_fu.setMinimumHeight(36)
        btn_add_fu.clicked.connect(self.add_to_followup)
        left_vbox.addWidget(btn_add_fu)

        splitter.addWidget(left)

        # ─ RIGHT: Follow-up Queue ─────────────────────────────────────────────
        right = _make_card()
        right_vbox = QVBoxLayout(right)
        right_vbox.setContentsMargins(16, 14, 16, 14)
        right_vbox.setSpacing(8)

        # Header row
        right_hdr = QHBoxLayout()
        lbl_step2 = QLabel("② Follow-up Queue")
        lbl_step2.setStyleSheet("font-size: 14px; font-weight: 700;")
        self.lbl_fu_count = QLabel("0 records")
        self.lbl_fu_count.setObjectName("subHeader")
        right_hdr.addWidget(lbl_step2)
        right_hdr.addStretch()
        right_hdr.addWidget(self.lbl_fu_count)
        right_vbox.addLayout(right_hdr)

        # Selection toolbar (2 rows)
        fu_row1 = QHBoxLayout()
        fu_row1.setSpacing(6)
        self.search_fu = QLineEdit()
        self.search_fu.setPlaceholderText("🔍 Search...")
        self.search_fu.setMinimumHeight(28)
        self.search_fu.textChanged.connect(self.filter_fu_table)
        fu_row1.addWidget(self.search_fu)
        
        fu_row2 = QHBoxLayout()
        fu_row2.setSpacing(6)
        btn_fu_all  = QPushButton("Select All")
        btn_fu_none = QPushButton("Select None")
        btn_fu_all.setObjectName("btnSecondary")
        btn_fu_none.setObjectName("btnSecondary")
        btn_fu_all.clicked.connect(self._select_all_fu)
        btn_fu_none.clicked.connect(self._select_none_fu)
        btn_fu_remove = QPushButton("🗑  Remove Selected")
        btn_fu_remove.setObjectName("btnDanger")
        btn_fu_remove.clicked.connect(self.remove_from_followup)
        
        fu_row2.addWidget(btn_fu_all)
        fu_row2.addWidget(btn_fu_none)
        fu_row2.addStretch()
        fu_row2.addWidget(btn_fu_remove)
        
        right_vbox.addLayout(fu_row1)
        right_vbox.addLayout(fu_row2)

        # Table
        self.fu_table = self._build_table(
            ["Username", "Queued At", "Status"],
            stretch_col=0, multi=True
        )
        self.fu_table.setColumnWidth(2, 90)
        right_vbox.addWidget(self.fu_table)

        splitter.addWidget(right)
        splitter.setSizes([560, 440])
        root.addWidget(splitter, 1)

        # ── Bottom action bar ──────────────────────────────────────────────────
        action_card = _make_card()
        action_card.setStyleSheet(
            "QFrame#card { padding: 12px 16px; }"
        )
        action_layout = QHBoxLayout(action_card)
        action_layout.setContentsMargins(16, 12, 16, 12)

        self.lbl_action_hint = QLabel(
            "Select users on the left and add them to the queue, "
            "then queue them for the engine below."
        )
        self.lbl_action_hint.setObjectName("subHeader")
        self.lbl_action_hint.setWordWrap(True)
        action_layout.addWidget(self.lbl_action_hint, 1)

        btn_queue = QPushButton("③  Queue All Pending for Engine  →")
        btn_queue.setObjectName("btnStart")
        btn_queue.setMinimumHeight(40)
        btn_queue.setMinimumWidth(260)
        btn_queue.clicked.connect(self.queue_for_engine)
        action_layout.addWidget(btn_queue)
        root.addWidget(action_card)

    # ── Widget Factories ───────────────────────────────────────────────────────

    def _stat_card(self, label, value, color):
        card = _make_card()
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(18, 12, 18, 12)
        vbox.setSpacing(4)

        lbl_title = QLabel(label.upper())
        lbl_title.setStyleSheet(
            f"font-size: 10px; font-weight: 700; letter-spacing: 1px; color: {color};"
        )
        lbl_val = QLabel(value)
        lbl_val.setStyleSheet(
            f"font-size: 28px; font-weight: 900; color: {color};"
        )
        vbox.addWidget(lbl_title)
        vbox.addWidget(lbl_val)

        # store ref to update later
        card._val_lbl = lbl_val
        return card

    def _build_table(self, headers, stretch_col=0, multi=False):
        t = QTableWidget()
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.horizontalHeader().setSectionResizeMode(
            stretch_col, QHeaderView.ResizeMode.Stretch
        )
        t.verticalHeader().setVisible(False)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        if multi:
            t.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        return t

    # ── Selection Helpers ──────────────────────────────────────────────────────

    def _select_all_sent(self):
        self.sent_table.selectAll()

    def _select_none_sent(self):
        self.sent_table.clearSelection()

    def _select_all_fu(self):
        self.fu_table.selectAll()

    def _select_none_fu(self):
        self.fu_table.clearSelection()

    def _update_sent_sel_label(self):
        rows = len(set(i.row() for i in self.sent_table.selectedItems()))
        self.lbl_sent_sel.setText(f"{rows} selected")
        
    def filter_sent_table(self, text):
        search_term = text.lower()
        filter_data = self._dm_filter_value   # None = all
        
        for row in range(self.sent_table.rowCount()):
            item_user = self.sent_table.item(row, 0)
            item_dms = self.sent_table.item(row, 2)
            
            if item_user and item_dms:
                u_text = item_user.text().lower()
                d_text = item_dms.text()
                
                match_search = search_term in u_text
                match_combo = (filter_data is None) or (d_text == filter_data)
                
                self.sent_table.setRowHidden(row, not (match_search and match_combo))

    def _show_dm_filter_menu(self):
        """Show a fully-styled QMenu for the DM count filter."""
        menu = QMenu(self)
        menu.setObjectName("dmFilterMenu")

        # Build options from current table data
        import collections
        dm_counts = collections.defaultdict(int)
        for row in range(self.sent_table.rowCount()):
            item = self.sent_table.item(row, 2)
            if item:
                try:
                    dm_counts[int(item.text())] += 1
                except ValueError:
                    pass

        total = sum(dm_counts.values())

        def _pick(value, label):
            self._dm_filter_value = value
            self.btn_dm_filter.setText(label)
            self.filter_sent_table(self.search_sent.text())

        a_all = menu.addAction(f"All Users ({total})")
        a_all.triggered.connect(lambda: _pick(None, "All Users"))
        menu.addSeparator()
        for k in sorted(dm_counts.keys()):
            label = f"{k} DM(s)  ·  {dm_counts[k]} users"
            a = menu.addAction(label)
            a.triggered.connect(lambda checked, v=str(k), l=f"{k} DM(s)": _pick(v, l))

        menu.exec(self.btn_dm_filter.mapToGlobal(
            self.btn_dm_filter.rect().bottomLeft()
        ))
                
    def filter_fu_table(self, text):
        search_term = text.lower()
        for row in range(self.fu_table.rowCount()):
            item = self.fu_table.item(row, 0) # Username column
            if item:
                self.fu_table.setRowHidden(row, search_term not in item.text().lower())

    # ── Data ───────────────────────────────────────────────────────────────────

    def refresh_tables(self):
        # ── Sent DM history ────────────────────────────────────────────────────
        c = self.conn.cursor()
        c.execute("""
            SELECT sl.username, MAX(sl.sent_at) as sent_at, COUNT(sl.id) as dm_count 
            FROM sent_log sl
            WHERE sl.username NOT IN (SELECT username FROM followup_queue WHERE status = 'Pending')
            GROUP BY sl.username
            ORDER BY MAX(sl.sent_at) DESC 
            LIMIT 500
        """)
        rows = c.fetchall()
        
        # Update button label to reflect current data
        import collections
        dm_counts = collections.defaultdict(int)
        for r in rows:
            dm_counts[r['dm_count']] += 1
        total_users = sum(dm_counts.values())
        # Reset filter if previously selected bucket no longer exists
        if self._dm_filter_value is not None and int(self._dm_filter_value) not in dm_counts:
            self._dm_filter_value = None
            self.btn_dm_filter.setText("All Users")
        elif self._dm_filter_value is None:
            self.btn_dm_filter.setText("All Users")

        self.sent_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            u = QTableWidgetItem(row['username'])
            ts_raw = row['sent_at'] or ''
            ts = ts_raw.split('.')[0].replace('T', ' ')
            t = QTableWidgetItem(ts)
            
            # Highlight multi-DMs with green so users know
            dm_count = row['dm_count']
            count_item = QTableWidgetItem(str(dm_count))
            if dm_count > 1:
                count_item.setForeground(QColor('#3FB950'))
                count_item.setFont(QFont("Segoe UI", -1, QFont.Weight.Bold))
                
            for item in (u, t, count_item):
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
            self.sent_table.setItem(r, 0, u)
            self.sent_table.setItem(r, 1, t)
            self.sent_table.setItem(r, 2, count_item)

        self.lbl_sent_count.setText(f"{len(rows)} users")
        self.stat_sent._val_lbl.setText(str(len(rows)))
        self._update_sent_sel_label()
        
        self.filter_sent_table(self.search_sent.text())

        # ── Follow-up queue ────────────────────────────────────────────────────
        fu_rows = self.queue_manager.get_followup_queue()
        self.fu_table.setRowCount(len(fu_rows))
        pending = 0
        for r, row in enumerate(fu_rows):
            u = QTableWidgetItem(row['username'])
            queued_raw = row['queued_at'] or ''
            queued = queued_raw.split('.')[0].replace('T', ' ')
            t = QTableWidgetItem(queued)
            status = row['status']
            s = QTableWidgetItem(f"  {status}")

            if status == 'Pending':
                s.setForeground(QColor('#F59E0B'))
                pending += 1
            else:
                s.setForeground(QColor('#10B981'))

            for item in (u, t, s):
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
            self.fu_table.setItem(r, 0, u)
            self.fu_table.setItem(r, 1, t)
            self.fu_table.setItem(r, 2, s)

        self.lbl_fu_count.setText(f"{len(fu_rows)} in queue")
        self.stat_queued._val_lbl.setText(str(len(fu_rows)))
        self.stat_pending._val_lbl.setText(str(pending))

        hint = (
            f"{pending} pending follow-up(s) ready to queue for the engine."
            if pending else
            "Add users from the Sent DM history on the left to begin."
        )
        self.lbl_action_hint.setText(hint)
        
        self.filter_fu_table(self.search_fu.text())

    # ── Actions ────────────────────────────────────────────────────────────────

    def add_to_followup(self):
        selected_rows = set(i.row() for i in self.sent_table.selectedItems())
        if not selected_rows:
            dark_warning(self, "Nothing Selected",
                         "Please select at least one row from the Sent DM History.\n"
                         "Use  Select All  to grab the full list at once.")
            return

        added = skipped = 0
        for row in selected_rows:
            username = self.sent_table.item(row, 0).text()
            if self.queue_manager.add_to_followup(username):
                added += 1
            else:
                skipped += 1

        self.refresh_tables()
        msg = f"✅  {added} user(s) added to the Follow-up Queue."
        if skipped:
            msg += f"\n⚠  {skipped} user(s) were already in the queue (skipped)."
        dark_info(self, "Queue Updated", msg)

    def remove_from_followup(self):
        selected_rows = set(i.row() for i in self.fu_table.selectedItems())
        if not selected_rows:
            dark_warning(self, "Nothing Selected",
                         "Select one or more rows from the Follow-up Queue to remove.")
            return
        for row in selected_rows:
            username = self.fu_table.item(row, 0).text()
            self.queue_manager.remove_from_followup(username)
        self.refresh_tables()

    def queue_for_engine(self):
        pending = self.queue_manager.get_pending_followups()
        if not pending:
            dark_warning(self, "Nothing to Queue",
                         "There are no Pending users in the Follow-up Queue.\n"
                         "Add users from the Sent DM history first.")
            return

        if not dark_question(
            self, "Confirm — Send Follow-ups",
            f"This will re-add  {len(pending)}  user(s) to the main engine queue.\n"
            f"They will bypass the 'already messaged' filter.\n\n"
            f"💡 Make sure your Message Pool contains your follow-up message "
            f"before starting the engine.\n\nContinue?"
        ):
            return

        queued = 0
        for username in pending:
            ok, _ = self.queue_manager.force_add_single(username)
            if ok:
                queued += 1

        dark_info(
            self, "Follow-ups Queued ✅",
            f"{queued} user(s) added to the main engine queue.\n\n"
            f"Go to  Dashboard → Start Engine  to send the follow-up messages."
        )
        self.main_window.nav_list.setCurrentRow(0)
        self.refresh_tables()
