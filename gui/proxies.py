from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QLineEdit
)
from PyQt6.QtCore import Qt
from core.account_manager import AccountManager
from gui.dialogs import dark_warning, dark_question


class ProxyDialog(QDialog):
    """Custom dark-themed proxy input dialog."""

    def __init__(self, parent, username, current_proxy=''):
        super().__init__(parent)
        self.setWindowTitle(f"Set Proxy — {username}")
        self.setFixedWidth(480)
        self.setStyleSheet("""
            QDialog {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 8px;
            }
            QLabel { color: #C9D1D9; font-size: 13px; background: transparent; }
            QLabel#title { color: #FFFFFF; font-size: 15px; font-weight: 600; }
            QLabel#note  { color: #8B949E; font-size: 12px; }
            QLineEdit {
                background-color: #0D1117;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 8px 12px;
                color: #C9D1D9;
                font-size: 13px;
                font-family: 'Consolas', monospace;
            }
            QLineEdit:focus { border: 1px solid #58A6FF; }
            QPushButton {
                background-color: #21262D;
                color: #C9D1D9;
                border: 1px solid rgba(240,246,252,0.1);
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #30363D; border-color: #8B949E; }
            QPushButton#btnSave {
                background-color: #238636;
                color: #FFFFFF;
                border-color: rgba(240,246,252,0.1);
            }
            QPushButton#btnSave:hover { background-color: #2EA043; }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 20)
        root.setSpacing(14)

        title = QLabel(f"Proxy for  {username}")
        title.setObjectName("title")
        root.addWidget(title)

        # Format hints as mini-cards
        hint_frame = QFrame()
        hint_frame.setStyleSheet("background:#0D1117; border:1px solid #30363D; border-radius:6px;")
        hint_layout = QVBoxLayout(hint_frame)
        hint_layout.setContentsMargins(14, 10, 14, 10)
        hint_layout.setSpacing(4)
        hint_lbl = QLabel("Accepted formats:")
        hint_lbl.setStyleSheet("color:#8B949E; font-size:12px; font-weight:600;")
        hint_layout.addWidget(hint_lbl)
        for fmt in [
            "192.168.1.1:8080",
            "http://192.168.1.1:8080",
            "http://username:password@192.168.1.1:8080",
        ]:
            row_lbl = QLabel(f"  •  {fmt}")
            row_lbl.setStyleSheet("color:#58A6FF; font-family:'Consolas',monospace; font-size:12px;")
            hint_layout.addWidget(row_lbl)
        root.addWidget(hint_frame)

        input_lbl = QLabel("Proxy Address:")
        root.addWidget(input_lbl)

        self.txt_proxy = QLineEdit()
        self.txt_proxy.setPlaceholderText("e.g.  http://user:pass@203.0.113.5:8080")
        self.txt_proxy.setText(current_proxy)
        root.addWidget(self.txt_proxy)

        note = QLabel("Leave blank and click Save to clear the proxy from this account.")
        note.setObjectName("note")
        root.addWidget(note)

        root.addSpacing(4)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Save")
        btn_save.setObjectName("btnSave")
        btn_save.clicked.connect(self.accept)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        root.addLayout(btn_row)

    def get_proxy(self):
        return self.txt_proxy.text().strip()


class ProxiesPanel(QWidget):
    """
    Dedicated Proxy Management panel.

    What is a proxy?
    ----------------
    A proxy is an intermediate server that routes your browser traffic through
    a different IP address. When the engine uses a proxy, Instagram sees the
    proxy's IP — not your home IP. This is critical when running multiple
    accounts: each account should have a dedicated IP so Instagram cannot
    fingerprint them as belonging to the same machine.

    Recommended proxy types (cheapest → strongest stealth)
    -------------------------------------------------------
    1. Datacenter proxies  – cheap, fast, easily detected by Meta
    2. Residential proxies – real home IPs, much harder to detect
    3. 4G Mobile proxies   – highest trust score, best ban-protection
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.account_manager = AccountManager()
        self._init_ui()
        self.refresh_table()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header = QLabel("Proxy Management")
        header.setObjectName("headerTitle")
        layout.addWidget(header)

        # Info card
        info_card = QFrame()
        info_card.setObjectName("card")
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(20, 16, 20, 16)
        info_layout.setSpacing(6)

        info_title = QLabel("Why use a Proxy?")
        info_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #FFFFFF;")
        info_layout.addWidget(info_title)

        info_body = QLabel(
            "A proxy routes each account's browser traffic through a different IP address. "
            "Instagram sees the proxy's IP — not yours.\n"
            "Assign one dedicated proxy per account to prevent Instagram from detecting "
            "multiple accounts on the same machine.\n\n"
            "Recommended:  4G Mobile Proxy  >  Residential Proxy  >  Datacenter Proxy"
        )
        info_body.setObjectName("subHeader")
        info_body.setWordWrap(True)
        info_layout.addWidget(info_body)
        layout.addWidget(info_card)

        # Toolbar
        toolbar = QHBoxLayout()
        self.btn_set = QPushButton("Set / Update Proxy")
        self.btn_set.setObjectName("btnSuccess")
        self.btn_set.clicked.connect(self.set_proxy)

        self.btn_clear = QPushButton("Clear Proxy")
        self.btn_clear.setObjectName("btnDanger")
        self.btn_clear.clicked.connect(self.clear_proxy)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self.refresh_table)

        toolbar.addWidget(self.btn_set)
        toolbar.addWidget(self.btn_clear)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Account ID", "Username", "Proxy Address"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        # Double-click to edit
        self.table.doubleClicked.connect(self.set_proxy)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def refresh_table(self):
        accounts = self.account_manager.get_accounts()
        self.table.setRowCount(len(accounts))
        for row, acc in enumerate(accounts):
            self.table.setItem(row, 0, QTableWidgetItem(str(acc['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(acc['username']))
            proxy_val = acc.get('proxy', '') or ''
            proxy_item = QTableWidgetItem(proxy_val if proxy_val else '— not set —')
            if not proxy_val:
                proxy_item.setForeground(Qt.GlobalColor.darkGray)
            else:
                proxy_item.setForeground(Qt.GlobalColor.green)
            self.table.setItem(row, 2, proxy_item)

    def _selected_account(self):
        selected = self.table.selectedItems()
        if not selected:
            dark_warning(self, "No Selection", "Please select an account row first.")
            return None, None
        row = selected[0].row()
        acc_id = int(self.table.item(row, 0).text())
        username = self.table.item(row, 1).text()
        return acc_id, username

    def set_proxy(self):
        acc_id, username = self._selected_account()
        if acc_id is None:
            return
        current = self.table.item(self.table.currentRow(), 2).text()
        if current == '— not set —':
            current = ''

        dlg = ProxyDialog(self, username, current)
        if dlg.exec():
            self.account_manager.update_proxy(acc_id, dlg.get_proxy())
            self.refresh_table()

    def clear_proxy(self):
        acc_id, username = self._selected_account()
        if acc_id is None:
            return
        if dark_question(self, "Clear Proxy", f"Remove the proxy configuration from account '{username}'?"):
            self.account_manager.update_proxy(acc_id, '')
            self.refresh_table()
