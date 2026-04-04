from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTextEdit, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor
from datetime import datetime
from data.db import get_connection
from gui.dialogs import dark_info, dark_warning

class LogsPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.conn = get_connection()
        self._init_ui()
        
    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        header = QLabel("Engine Session Logs")
        header.setObjectName("headerTitle")
        main_layout.addWidget(header)
        
        tools_layout = QHBoxLayout()
        self.btn_export = QPushButton("Export Log to CSV")
        self.btn_export.setObjectName("btnSuccess")
        self.btn_export.clicked.connect(self.export_csv)
        self.btn_clear = QPushButton("Clear Live Log")
        self.btn_clear.clicked.connect(lambda: self.log_box.clear())
        tools_layout.addWidget(self.btn_export)
        tools_layout.addWidget(self.btn_clear)
        tools_layout.addStretch()
        main_layout.addLayout(tools_layout)
        
        # Live log box
        lbl_live = QLabel("Active Session Live Log")
        lbl_live.setObjectName("subHeader")
        main_layout.addWidget(lbl_live)
        
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet("font-family: Consolas, monospace;")
        main_layout.addWidget(self.log_box)
        
        # Sent DB Log Table
        lbl_history = QLabel("Sent Messages History")
        lbl_history.setObjectName("subHeader")
        main_layout.addWidget(lbl_history)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Target Username", "Account ID Used"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        main_layout.addWidget(self.table)
        
        self.setLayout(main_layout)
        self.refresh_table()
        
    def append_log(self, msg_type, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = "#a3a3a3"  # default grey

        if msg_type == "ERROR":   color = "#EF4444"  # red
        elif msg_type == "SUCCESS": color = "#10B981"  # green
        elif msg_type == "INFO":  color = "#3B82F6"  # blue
        elif msg_type == "WARN":  color = "#F59E0B"  # yellow

        formatted = f'<span style="color: {color}">[{timestamp}] [{msg_type}] {message}</span><br>'

        # ── CRITICAL: always move to the absolute end before inserting ──────────
        # insertHtml() writes at the *current cursor position*. If the user has
        # ever clicked inside the log box the cursor is somewhere in the middle,
        # so new log entries would appear there (or get swallowed). Forcing the
        # cursor to End every time guarantees all entries append correctly.
        cursor = self.log_box.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_box.setTextCursor(cursor)
        self.log_box.insertHtml(formatted)

        # Scroll to bottom
        scrollbar = self.log_box.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def refresh_table(self):
        c = self.conn.cursor()
        c.execute("SELECT sent_at, username, account_id FROM sent_log ORDER BY id DESC LIMIT 100")
        rows = c.fetchall()
        
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(row['sent_at'].split('.')[0].replace('T', ' ')))
            self.table.setItem(r, 1, QTableWidgetItem(row['username']))
            self.table.setItem(r, 2, QTableWidgetItem(str(row['account_id'])))

    def export_csv(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save CSV Data", "", "CSV Files (*.csv)")
        if not file_name: return
            
        c = self.conn.cursor()
        c.execute("SELECT sent_at, username, account_id FROM sent_log ORDER BY id DESC")
        rows = c.fetchall()
        
        import csv
        try:
            with open(file_name, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Username", "Account ID"])
                for row in rows:
                    writer.writerow([row['sent_at'], row['username'], row['account_id']])
            dark_info(self, "Export Complete", f"Successfully exported {len(rows)} records to CSV.")
        except Exception as e:
            dark_warning(self, "Export Failed", str(e))
