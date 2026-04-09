from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
                             QLineEdit, QFileDialog, QMenu)
from PyQt6.QtCore import Qt
from core.queue_manager import QueueManager
from gui.dialogs import dark_info, dark_warning, dark_question, dark_input

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
        header.setObjectName("headerTitle")
        layout.addWidget(header)
        
        # Tools layout
        tools_layout = QHBoxLayout()
        
        self.btn_import = QPushButton("Import TXT File")
        self.btn_import.clicked.connect(self.import_txt)
        
        self.btn_dedup = QPushButton("Remove Duplicates")
        self.btn_dedup.setObjectName("btnWarning")
        self.btn_dedup.clicked.connect(self.dedup_queue)
        
        self.btn_edit = QPushButton("Edit Selected")
        self.btn_edit.clicked.connect(self.edit_selected)
        
        self.btn_delete = QPushButton("Delete Selected")
        self.btn_delete.setObjectName("btnDanger")
        self.btn_delete.clicked.connect(self.delete_selected)
        
        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.setObjectName("btnDanger")
        self.btn_clear.clicked.connect(self.clear_queue)
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Search username...")
        self.txt_search.setFixedWidth(200)
        self.txt_search.textChanged.connect(self.filter_table)
        
        tools_layout.addWidget(self.btn_import)
        tools_layout.addWidget(self.btn_dedup)
        tools_layout.addWidget(self.btn_edit)
        tools_layout.addWidget(self.btn_delete)
        tools_layout.addWidget(self.btn_clear)
        tools_layout.addStretch()
        tools_layout.addWidget(self.txt_search)
        
        # Manual Add layout
        add_layout = QHBoxLayout()
        self.txt_manual = QLineEdit()
        self.txt_manual.setPlaceholderText("Enter single Instagram username...")
        
        self.btn_add_manual = QPushButton("Add to Queue")
        self.btn_add_manual.setObjectName("btnSuccess")
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
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
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
            
        # apply existing filter if any
        self.filter_table(self.txt_search.text())

    def filter_table(self, text):
        search_term = text.lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1) # Username column
            if item:
                self.table.setRowHidden(row, search_term not in item.text().lower())

    def dedup_queue(self):
        removed = self.queue_manager.remove_duplicates()
        if removed > 0:
            dark_info(self, "Duplicates Removed", f"Successfully found and removed {removed} duplicated username(s).")
            self.refresh_table()
        else:
            dark_info(self, "No Duplicates Found", "The queue is perfectly clean! No duplicates were found.")

    def import_txt(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open TXT File", "", "Text Files (*.txt);;All Files (*)")
        if file_name:
            added, dups, filtered = self.queue_manager.import_txt(file_name)
            dark_info(self, "Import Complete",
                f"Import Results:\n\n  Added:    {added}\n  Duplicates removed:    {dups}\n  Skipped (blacklist/sent):    {filtered}")
            self.refresh_table()
            
    def clear_queue(self):
        if dark_question(self, "Clear Queue", "Are you sure you want to permanently delete the entire queue?"):
            self.queue_manager.clear()
            self.refresh_table()
            
    def edit_selected(self):
        selected = self.table.selectedItems()
        if not selected:
            dark_warning(self, "No Selection", "Please select a row to edit.")
            return
        row = selected[0].row()
        q_id = int(self.table.item(row, 0).text())
        current_user = self.table.item(row, 1).text()
        
        new_user, ok = dark_input(self, 'Edit Username', f'Edit username for entry #{q_id}:', text=current_user)
        if ok and new_user.strip() and new_user.strip() != current_user:
            self.queue_manager.update_username(q_id, new_user.strip())
            self.refresh_table()

    def delete_selected(self):
        selected = self.table.selectedItems()
        if not selected:
            dark_warning(self, "No Selection", "Please select a row to delete.")
            return
        row = selected[0].row()
        q_id = int(self.table.item(row, 0).text())
        username = self.table.item(row, 1).text()
        if dark_question(self, "Delete Entry", f"Remove '{username}' from the queue?"):
            self.queue_manager.remove(q_id)
            self.refresh_table()

    def add_manual(self):
        username = self.txt_manual.text()
        success, msg = self.queue_manager.add_single(username)
        if success:
            self.txt_manual.clear()
            self.refresh_table()
        else:
            dark_warning(self, "Error", msg)

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
