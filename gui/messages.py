from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTextEdit, QScrollArea, QTabWidget, QLineEdit,
                             QFileDialog, QFrame)
from PyQt6.QtCore import Qt
import json
from pathlib import Path
from gui.dialogs import dark_warning, dark_info

class MessagesPanel(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.text_boxes_initial = []
        self.text_boxes_followup = []
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
            "Add up to 10 messages per category. The engine will pick one randomly for each target.\n"
            "Use {username} to mention the target handle (e.g. @john_doe).\n"
            "Advanced (Spintax): Use {Option1|Option2} to randomize words (e.g. {Hey|Hi|Hello} there!)"
        )
        help_lbl.setObjectName("subHeader")
        main_layout.addWidget(help_lbl)
        
        # Tools layout
        tools_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add Message Slot +")
        self.btn_add.clicked.connect(self.add_slot)
        
        self.btn_spintax = QPushButton("Insert {Hey|Hi} Template")
        self.btn_spintax.setObjectName("btnWarning")
        self.btn_spintax.clicked.connect(self.insert_spintax_at_cursor)
        
        self.btn_save = QPushButton("Save All Messages")
        self.btn_save.setObjectName("btnSuccess")
        self.btn_save.clicked.connect(self.save_messages)
        
        tools_layout.addWidget(self.btn_add)
        tools_layout.addWidget(self.btn_spintax)
        tools_layout.addWidget(self.btn_save)
        tools_layout.addStretch()
        main_layout.addLayout(tools_layout)
        
        # Tabs for Initial vs Follow-up
        self.tabs = QTabWidget()
        
        self.tab_initial = QWidget()
        self.tab_initial_layout = QVBoxLayout(self.tab_initial)
        
        self.tab_followup = QWidget()
        self.tab_followup_layout = QVBoxLayout(self.tab_followup)
        
        # Setup Initial Tab Scroll
        self.scroll_initial = QScrollArea()
        self.scroll_initial.setWidgetResizable(True)
        self.messages_container_initial = QWidget()
        self.messages_layout_initial = QVBoxLayout(self.messages_container_initial)
        self.messages_layout_initial.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_initial.setWidget(self.messages_container_initial)
        self.tab_initial_layout.addWidget(self.scroll_initial)
        
        # Setup Follow-up Tab Scroll
        self.scroll_followup = QScrollArea()
        self.scroll_followup.setWidgetResizable(True)
        self.messages_container_followup = QWidget()
        self.messages_layout_followup = QVBoxLayout(self.messages_container_followup)
        self.messages_layout_followup.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_followup.setWidget(self.messages_container_followup)
        self.tab_followup_layout.addWidget(self.scroll_followup)

        # ── Attachment row (Follow-up only) ──────────────────────────────────
        attach_sep = QFrame()
        attach_sep.setFrameShape(QFrame.Shape.HLine)
        attach_sep.setObjectName("separator")
        self.tab_followup_layout.addWidget(attach_sep)

        attach_row = QHBoxLayout()
        attach_row.setSpacing(8)

        attach_lbl = QLabel("Attachment (optional, sent after text):")
        attach_lbl.setObjectName("subHeader")

        self.attach_path_edit = QLineEdit()
        self.attach_path_edit.setReadOnly(True)
        self.attach_path_edit.setPlaceholderText("No file selected — click Browse to attach a PDF or image")
        self.attach_path_edit.setMinimumHeight(30)

        btn_browse = QPushButton("Browse…")
        btn_browse.setObjectName("btnSecondary")
        btn_browse.clicked.connect(self._browse_attachment)

        btn_clear_attach = QPushButton("Clear")
        btn_clear_attach.setObjectName("btnDanger")
        btn_clear_attach.clicked.connect(self._clear_attachment)

        attach_row.addWidget(attach_lbl)
        attach_row.addWidget(self.attach_path_edit, 1)
        attach_row.addWidget(btn_browse)
        attach_row.addWidget(btn_clear_attach)
        self.tab_followup_layout.addLayout(attach_row)
        
        self.tabs.addTab(self.tab_initial, "Initial Outreach")
        self.tabs.addTab(self.tab_followup, "Follow-ups")
        
        main_layout.addWidget(self.tabs)
        
        # Preview panel
        preview_lbl = QLabel("Live Preview (using sample username 'john_doe'):")
        preview_lbl.setObjectName("subHeader")
        main_layout.addWidget(preview_lbl)
        
        self.preview_box = QLabel("...")
        self.preview_box.setObjectName("card")
        self.preview_box.setWordWrap(True)
        self.preview_box.setStyleSheet("padding: 15px;")
        main_layout.addWidget(self.preview_box)
        
        self.setLayout(main_layout)
        
        self.tabs.currentChanged.connect(self.update_preview)

    def _get_current_list_and_layout(self):
        if self.tabs.currentIndex() == 0:
            return self.text_boxes_initial, self.messages_layout_initial
        else:
            return self.text_boxes_followup, self.messages_layout_followup

    def add_slot(self, content=None, is_followup=False):
        if content is False or content is None:
            content = ""
            
        target_list, target_layout = self._get_current_list_and_layout()
        if is_followup:
            target_list = self.text_boxes_followup
            target_layout = self.messages_layout_followup
        
        if len(target_list) >= 10:
            dark_warning(self, "Limit Reached", "You can only have up to 10 message templates per section.")
            return
            
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        
        txt = QTextEdit()
        txt.setAcceptRichText(False)
        txt.setFixedHeight(80)
        txt.setText(content)
        txt.textChanged.connect(self.update_preview)
        
        btn_remove = QPushButton("X")
        btn_remove.setFixedSize(40, 40)
        btn_remove.setObjectName("btnDanger")
        btn_remove.clicked.connect(lambda: self.remove_slot(row_widget, txt, target_list))
        
        row_layout.addWidget(txt)
        row_layout.addWidget(btn_remove)
        
        target_layout.addWidget(row_widget)
        target_list.append(txt)
        
    def insert_spintax_at_cursor(self):
        """Insert a spintax greeting template at the cursor of the focused text box."""
        template = "{Hey|Hi|Hello} {username}, I noticed your profile and wanted to connect!"
        target_list, _ = self._get_current_list_and_layout()
        
        focused = None
        for txt in target_list:
            if txt.hasFocus():
                focused = txt
                break
        
        if focused is None and target_list:
            focused = target_list[-1]
        
        if focused is None:
            self.add_slot(template)
            return
        
        focused.insertPlainText(template)

    def remove_slot(self, widget, txt_obj, target_list):
        widget.deleteLater()
        if txt_obj in target_list:
            target_list.remove(txt_obj)
        self.update_preview()
            
    def update_preview(self):
        target_list, _ = self._get_current_list_and_layout()
        if target_list:
            from core.message_builder import process_spintax
            text = target_list[0].toPlainText()
            resolved = process_spintax(text)
            self.preview_box.setText(resolved.replace("{username}", "@john_doe"))
        else:
            self.preview_box.setText("...")
            
    def _browse_attachment(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Attachment", "",
            "Supported Files (*.pdf *.jpg *.jpeg *.png *.mp4 *.mov);;All Files (*)"
        )
        if path:
            self.attach_path_edit.setText(path)

    def _clear_attachment(self):
        self.attach_path_edit.clear()

    def load_messages(self):
        path = Path('config/messages.json')
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                msgs = data.get('messages', [])
                followups = data.get('followups', [])
                attach = data.get('followup_attachment', '')

                for m in msgs:
                    self.add_slot(m, is_followup=False)

                for m in followups:
                    self.add_slot(m, is_followup=True)

                if attach:
                    self.attach_path_edit.setText(attach)

        if not self.text_boxes_initial:
            self.add_slot("Hey {username}, love your profile!", is_followup=False)

        if not self.text_boxes_followup:
            self.add_slot("Hey {username}, following up on my previous message!", is_followup=True)

        self.update_preview()

    def save_messages(self):
        msgs_init   = [txt.toPlainText().strip() for txt in self.text_boxes_initial  if txt.toPlainText().strip()]
        msgs_follow = [txt.toPlainText().strip() for txt in self.text_boxes_followup if txt.toPlainText().strip()]

        if not msgs_init and not msgs_follow:
            dark_warning(self, "Validation Error", "You must have at least one valid message before saving.")
            return

        for list_msgs in [msgs_init, msgs_follow]:
            for m in list_msgs:
                if len(m) > 1000:
                    dark_warning(self, "Validation Error", "One of your messages exceeds the 1000 character limit.")
                    return

        attach_path = self.attach_path_edit.text().strip()

        Path('config').mkdir(exist_ok=True)
        payload = {
            "messages":            msgs_init,
            "followups":           msgs_follow,
            "followup_attachment": attach_path,
        }
        with open('config/messages.json', 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)

        attach_note = f" + attachment: {Path(attach_path).name}" if attach_path else ""
        dark_info(self, "Saved",
                  f"{len(msgs_init)} Initial and {len(msgs_follow)} Follow-up template(s) saved.{attach_note}")
