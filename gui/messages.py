from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTextEdit, QScrollArea, QMessageBox)
from PyQt6.QtCore import Qt
import json
from pathlib import Path

class MessagesPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.text_boxes = []
        self._init_ui()
        self.load_messages()
        
    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        header = QLabel("Message Pool")
        header.setObjectName("headerTitle")
        main_layout.addWidget(header)
        
        help_lbl = QLabel(
            "Add up to 10 messages. The engine will pick one randomly for each DM to avoid spam filters.\n"
            "Use {username} in your message and it will be replaced with the exact target handle."
        )
        help_lbl.setObjectName("subHeader")
        main_layout.addWidget(help_lbl)
        
        # Tools layout
        tools_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add Message Slot +")
        self.btn_add.clicked.connect(self.add_slot)
        
        self.btn_save = QPushButton("Save All Messages")
        self.btn_save.setObjectName("btnSuccess")
        self.btn_save.clicked.connect(self.save_messages)
        
        tools_layout.addWidget(self.btn_add)
        tools_layout.addWidget(self.btn_save)
        tools_layout.addStretch()
        main_layout.addLayout(tools_layout)
        
        # Scroll area for messages
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.messages_container)
        
        main_layout.addWidget(self.scroll)
        
        # Preview panel
        preview_lbl = QLabel("Live Preview (using sample username 'john_doe'):")
        preview_lbl.setObjectName("subHeader")
        main_layout.addWidget(preview_lbl)
        
        self.preview_box = QLabel("...")
        self.preview_box.setObjectName("card")
        self.preview_box.setWordWrap(True)
        # Give it some padding explicitly since label padding in QSS can sometimes miss if not globally defined for labels
        self.preview_box.setStyleSheet("padding: 15px;")
        main_layout.addWidget(self.preview_box)
        
        self.setLayout(main_layout)

    def add_slot(self, content=None):
        if content is False or content is None:
            content = ""
        if len(self.text_boxes) >= 10:
            QMessageBox.warning(self, "Limit Reached", "You can only have up to 10 message templates.")
            return
            
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        
        txt = QTextEdit()
        txt.setFixedHeight(80)
        txt.setText(content)
        txt.textChanged.connect(self.update_preview)
        
        btn_remove = QPushButton("X")
        btn_remove.setFixedSize(40, 40)
        btn_remove.setObjectName("btnDanger")
        btn_remove.clicked.connect(lambda: self.remove_slot(row_widget, txt))
        
        row_layout.addWidget(txt)
        row_layout.addWidget(btn_remove)
        
        self.messages_layout.addWidget(row_widget)
        self.text_boxes.append(txt)
        
    def remove_slot(self, widget, txt_obj):
        widget.deleteLater()
        if txt_obj in self.text_boxes:
            self.text_boxes.remove(txt_obj)
        self.update_preview()
            
    def update_preview(self):
        if self.text_boxes:
            # Just preview the first one for simplicity
            text = self.text_boxes[0].toPlainText()
            self.preview_box.setText(text.replace("{username}", "john_doe"))
        else:
            self.preview_box.setText("...")
            
    def load_messages(self):
        path = Path('config/messages.json')
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                msgs = data.get('messages', [])
                for m in msgs:
                    self.add_slot(m)
        
        if not self.text_boxes:
            self.add_slot("Hey {username}, love your profile!")
            
        self.update_preview()

    def save_messages(self):
        msgs = [txt.toPlainText().strip() for txt in self.text_boxes if txt.toPlainText().strip()]
        if not msgs:
             QMessageBox.warning(self, "Error", "You must have at least one valid message.")
             return
             
        for m in msgs:
            if len(m) > 1000:
                QMessageBox.warning(self, "Error", "One of your messages exceeds the 1000 character limit.")
                return
                
        # Save to json
        Path('config').mkdir(exist_ok=True)
        with open('config/messages.json', 'w', encoding='utf-8') as f:
            json.dump({"messages": msgs}, f, indent=2)
            
        QMessageBox.information(self, "Success", "Messages saved successfully!")
