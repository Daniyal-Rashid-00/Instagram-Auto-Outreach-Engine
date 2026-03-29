"""
Shared dark-themed dialog utilities for CyberSolu DM Engine.
Replaces all native QMessageBox / QInputDialog calls with custom dark UI.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt

# ── Shared stylesheet ─────────────────────────────────────────────────────────
_STYLE = """
QDialog {
    background-color: #161B22;
    border: 1px solid #30363D;
    border-radius: 8px;
}
QLabel {
    color: #C9D1D9;
    background: transparent;
    font-size: 13px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
}
QLabel#dlg_title {
    color: #FFFFFF;
    font-size: 15px;
    font-weight: 600;
}
QLabel#dlg_icon { font-size: 22px; }
QLineEdit {
    background-color: #0D1117;
    border: 1px solid #30363D;
    border-radius: 6px;
    padding: 8px 12px;
    color: #C9D1D9;
    font-size: 13px;
}
QLineEdit:focus { border: 1px solid #58A6FF; }
QPushButton {
    background-color: #21262D;
    color: #C9D1D9;
    border: 1px solid rgba(240,246,252,0.1);
    border-radius: 6px;
    padding: 7px 22px;
    font-size: 13px;
    font-weight: 500;
    min-width: 80px;
}
QPushButton:hover { background-color: #30363D; border-color: #8B949E; }
QPushButton:pressed { background-color: #282E33; }
QPushButton#btn_primary {
    background-color: #238636;
    color: #FFFFFF;
    border-color: rgba(240,246,252,0.1);
}
QPushButton#btn_primary:hover { background-color: #2EA043; }
QPushButton#btn_danger {
    background-color: #21262D;
    color: #F85149;
    border-color: rgba(240,246,252,0.1);
}
QPushButton#btn_danger:hover { background-color: #DA3633; color: #FFFFFF; }
"""

# ── Base dialog builder ───────────────────────────────────────────────────────
def _base_dialog(parent, width=400):
    dlg = QDialog(parent)
    dlg.setStyleSheet(_STYLE)
    dlg.setFixedWidth(width)
    dlg.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
    return dlg


def _divider():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet("background: #30363D; border: none; max-height: 1px;")
    return line


# ── Alert ─────────────────────────────────────────────────────────────────────
class _AlertDialog(QDialog):
    def __init__(self, parent, title, message, icon, icon_color):
        super().__init__(parent)
        self.setStyleSheet(_STYLE)
        self.setFixedWidth(420)
        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        # Icon + title row
        top = QHBoxLayout()
        top.setSpacing(12)
        icon_lbl = QLabel(icon)
        icon_lbl.setObjectName("dlg_icon")
        icon_lbl.setStyleSheet(f"font-size: 22px; color: {icon_color}; background: transparent;")
        icon_lbl.setFixedWidth(30)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("dlg_title")
        top.addWidget(icon_lbl)
        top.addWidget(title_lbl)
        root.addLayout(top)

        root.addWidget(_divider())

        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet("color: #C9D1D9; font-size: 13px; background: transparent;")
        root.addWidget(msg_lbl)

        root.addSpacing(4)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("btn_primary")
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)
        root.addLayout(btn_row)


# ── Confirm ───────────────────────────────────────────────────────────────────
class _ConfirmDialog(QDialog):
    def __init__(self, parent, title, message):
        super().__init__(parent)
        self.setStyleSheet(_STYLE)
        self.setFixedWidth(420)
        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        top = QHBoxLayout()
        icon_lbl = QLabel("⚠")
        icon_lbl.setStyleSheet("font-size: 22px; color: #D29922; background: transparent;")
        icon_lbl.setFixedWidth(30)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("dlg_title")
        top.addWidget(icon_lbl)
        top.addWidget(title_lbl)
        root.addLayout(top)

        root.addWidget(_divider())

        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet("color: #C9D1D9; font-size: 13px; background: transparent;")
        root.addWidget(msg_lbl)

        root.addSpacing(4)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        no_btn = QPushButton("Cancel")
        no_btn.clicked.connect(self.reject)
        yes_btn = QPushButton("Yes, continue")
        yes_btn.setObjectName("btn_danger")
        yes_btn.clicked.connect(self.accept)
        btn_row.addWidget(no_btn)
        btn_row.addWidget(yes_btn)
        root.addLayout(btn_row)


# ── Input ─────────────────────────────────────────────────────────────────────
class _InputDialog(QDialog):
    def __init__(self, parent, title, label, placeholder='', text=''):
        super().__init__(parent)
        self.setStyleSheet(_STYLE)
        self.setFixedWidth(420)
        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("dlg_title")
        root.addWidget(title_lbl)

        root.addWidget(_divider())

        if label:
            lbl = QLabel(label)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color: #C9D1D9; font-size: 13px; background: transparent;")
            root.addWidget(lbl)

        self.txt = QLineEdit()
        self.txt.setPlaceholderText(placeholder)
        self.txt.setText(text)
        root.addWidget(self.txt)

        root.addSpacing(4)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("btn_primary")
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        root.addLayout(btn_row)

        # Submit on Enter
        self.txt.returnPressed.connect(self.accept)

    def get_text(self):
        return self.txt.text()


# ── Public API ────────────────────────────────────────────────────────────────
def dark_info(parent, title, message):
    """Show a dark-themed info notification."""
    dlg = _AlertDialog(parent, title, message, icon="✓", icon_color="#3FB950")
    dlg.exec()


def dark_warning(parent, title, message):
    """Show a dark-themed warning / error notification."""
    dlg = _AlertDialog(parent, title, message, icon="⚠", icon_color="#D29922")
    dlg.exec()


def dark_error(parent, title, message):
    """Show a dark-themed error notification."""
    dlg = _AlertDialog(parent, title, message, icon="✕", icon_color="#F85149")
    dlg.exec()


def dark_question(parent, title, message):
    """Show a dark-themed yes/no confirmation. Returns True if user clicked Yes."""
    dlg = _ConfirmDialog(parent, title, message)
    return dlg.exec() == QDialog.DialogCode.Accepted


def dark_input(parent, title, label, placeholder='', text=''):
    """Show a dark-themed text input dialog. Returns (text, accepted)."""
    dlg = _InputDialog(parent, title, label, placeholder, text)
    accepted = dlg.exec() == QDialog.DialogCode.Accepted
    return dlg.get_text(), accepted
