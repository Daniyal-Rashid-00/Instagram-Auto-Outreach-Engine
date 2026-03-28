from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
                             QLineEdit, QFileDialog, QMessageBox, QMenu)
from PyQt6.QtCore import Qt
from core.queue_manager import QueueManager

class QueuePanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.queue_manager = QueueManager()
        self._init_ui()
        self.refresh_table()
        
    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        header = QLabel("Target Queue")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)
        
        # Tools layout
        tools_layout = QHBoxLayout()
        
        self.btn_import = QPushButton("Import TXT File")
        self.btn_import.setStyleSheet("background-color: #4F46E5; color: white; border: none; padding: 10px; border-radius: 4px;")
        self.btn_import.clicked.connect(self.import_txt)
        
        self.btn_clear = QPushButton("Clear Queue")
        self.btn_clear.setStyleSheet("background-color: #DC2626; color: white; border: none; padding: 10px; border-radius: 4px;")
        self.btn_clear.clicked.connect(self.clear_queue)
        
        tools_layout.addWidget(self.btn_import)
        tools_layout.addWidget(self.btn_clear)
        tools_layout.addStretch()
        
        # Manual Add layout
        add_layout = QHBoxLayout()
        self.txt_manual = QLineEdit()
        self.txt_manual.setPlaceholderText("Enter single Instagram username...")
        self.txt_manual.setStyleSheet("padding: 10px; background-color: #2b2b2b; color: white; border-radius: 4px;")
        
        self.btn_add_manual = QPushButton("Add to Queue")
        self.btn_add_manual.setStyleSheet("background-color: #059669; color: white; border: none; padding: 10px; border-radius: 4px;")
        self.btn_add_manual.clicked.connect(self.add_manual)
        
        add_layout.addWidget(self.txt_manual)
        add_layout.addWidget(self.btn_add_manual)
        
        layout.addLayout(tools_layout)
        layout.addLayout(add_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Status", "Timestamp"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Dark theme table styles
        self.table.setStyleSheet("""
            QTableWidget { background-color: #1e1e1e; color: #fff; gridline-color: #333; }
            QHeaderView::section { background-color: #2b2b2b; color: #fff; padding: 4px; }
            QTableWidget::item:selected { background-color: #4F46E5; }
        """)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
        
    def refresh_table(self):
        queue = self.queue_manager.get_queue()
        self.table.setRowCount(len(queue))
        
        for row, item in enumerate(queue):
            id_col = QTableWidgetItem(str(item['id']))
            user_col = QTableWidgetItem(item['username'])
            status_col = QTableWidgetItem(item['status'])
            time_col = QTableWidgetItem(item['timestamp'].split('T')[0] if item['timestamp'] else "")
            
            # Color code status
            if item['status'] == 'Sent':
                status_col.setForeground(Qt.GlobalColor.green)
            elif item['status'] == 'Pending':
                status_col.setForeground(Qt.GlobalColor.yellow)
            elif item['status'] == 'Failed':
                status_col.setForeground(Qt.GlobalColor.red)
            elif item['status'] == 'Skipped':
                status_col.setForeground(Qt.GlobalColor.gray)
                
            self.table.setItem(row, 0, id_col)
            self.table.setItem(row, 1, user_col)
            self.table.setItem(row, 2, status_col)
            self.table.setItem(row, 3, time_col)

    def import_txt(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open TXT File", "", "Text Files (*.txt);;All Files (*)")
        if file_name:
            added, dups, filtered = self.queue_manager.import_txt(file_name)
            QMessageBox.information(self, "Import Complete", 
                f"Import Results:\n- Added: {added}\n- Duplicates removed: {dups}\n- Skipped (Blacklist/Already Sent): {filtered}")
            self.refresh_table()
            
    def clear_queue(self):
        confirm = QMessageBox.question(self, "Clear Queue", "Are you sure you want to delete the ENTIRE queue?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            self.queue_manager.clear()
            self.refresh_table()
            
    def add_manual(self):
        username = self.txt_manual.text()
        success, msg = self.queue_manager.add_single(username)
        if success:
            self.txt_manual.clear()
            self.refresh_table()
        else:
            QMessageBox.warning(self, "Error", msg)

    def show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if item is None:
            return
            
        menu = QMenu()
        remove_action = menu.addAction("Remove from Queue")
        skip_action = menu.addAction("Mark as Skipped")
        blacklist_action = menu.addAction("Add to Blacklist")
        
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        
        row = item.row()
        q_id = int(self.table.item(row, 0).text())
        q_user = self.table.item(row, 1).text()
        
        if action == remove_action:
            self.queue_manager.remove(q_id)
        elif action == skip_action:
            self.queue_manager.update_status(q_id, "Skipped")
        elif action == blacklist_action:
            self.queue_manager.add_to_blacklist(q_user)
            self.queue_manager.update_status(q_id, "Skipped", "Blacklisted by user")
            
        if action:
            self.refresh_table()
