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
        self.text_boxes_followup_2 = []
        self._init_ui()
        self.load_messages()
        
    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)
        
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
        
        self.btn_save = QPushButton("Save Messages")
        self.btn_save.setObjectName("btnSuccess")
        self.btn_save.clicked.connect(self.save_messages)
        
        tools_layout.addWidget(self.btn_add)
        tools_layout.addWidget(self.btn_spintax)
        tools_layout.addWidget(self.btn_save)
        tools_layout.addStretch()
        main_layout.addLayout(tools_layout)
        
        # Tabs for Initial vs Follow-up 1 vs Follow-up 2
        self.tabs = QTabWidget()
        
        self.tab_initial = QWidget()
        self.tab_initial_layout = QVBoxLayout(self.tab_initial)
        
        self.tab_followup = QWidget()
        self.tab_followup_layout = QVBoxLayout(self.tab_followup)

        self.tab_followup_2 = QWidget()
        self.tab_followup_2_layout = QVBoxLayout(self.tab_followup_2)
        
        # Setup Initial Tab Scroll
        self.scroll_initial = QScrollArea()
        self.scroll_initial.setWidgetResizable(True)
        self.messages_container_initial = QWidget()
        self.messages_layout_initial = QVBoxLayout(self.messages_container_initial)
        self.messages_layout_initial.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_initial.setWidget(self.messages_container_initial)
        self.tab_initial_layout.addWidget(self.scroll_initial)
        
        # Setup Follow-up 1 Tab Scroll
        self.scroll_followup = QScrollArea()
        self.scroll_followup.setWidgetResizable(True)
        self.messages_container_followup = QWidget()
        self.messages_layout_followup = QVBoxLayout(self.messages_container_followup)
        self.messages_layout_followup.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_followup.setWidget(self.messages_container_followup)
        self.tab_followup_layout.addWidget(self.scroll_followup)

        # Setup Follow-up 2 Tab Scroll
        self.scroll_followup_2 = QScrollArea()
        self.scroll_followup_2.setWidgetResizable(True)
        self.messages_container_followup_2 = QWidget()
        self.messages_layout_followup_2 = QVBoxLayout(self.messages_container_followup_2)
        self.messages_layout_followup_2.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_followup_2.setWidget(self.messages_container_followup_2)
        self.tab_followup_2_layout.addWidget(self.scroll_followup_2)

        # ── Attachment row (Follow-up 1 only) ──────────────────────────────────
        attach_sep = QFrame()
        attach_sep.setFrameShape(QFrame.Shape.HLine)
        attach_sep.setObjectName("separator")
        self.tab_followup_layout.addWidget(attach_sep)
        
        attach_row = QHBoxLayout()
        attach_row.setSpacing(8)
        attach_lbl = QLabel("Attachment:")
        attach_lbl.setObjectName("subHeader")
        
        self.attach_path_edit = QLineEdit()
        self.attach_path_edit.setReadOnly(True)
        self.attach_path_edit.setPlaceholderText("No file selected — click Browse to attach a PDF or image")
        self.attach_path_edit.setMinimumHeight(28)
        
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

        # ── Attachment row (Follow-up 2 only) ──────────────────────────────────
        attach_sep_2 = QFrame()
        attach_sep_2.setFrameShape(QFrame.Shape.HLine)
        attach_sep_2.setObjectName("separator")
        self.tab_followup_2_layout.addWidget(attach_sep_2)
        
        attach_row_2 = QHBoxLayout()
        attach_row_2.setSpacing(8)
        attach_lbl_2 = QLabel("Attachment:")
        attach_lbl_2.setObjectName("subHeader")
        
        self.attach_path_edit_2 = QLineEdit()
        self.attach_path_edit_2.setReadOnly(True)
        self.attach_path_edit_2.setPlaceholderText("No file selected — click Browse to attach a PDF or image")
        self.attach_path_edit_2.setMinimumHeight(28)
        
        btn_browse_2 = QPushButton("Browse…")
        btn_browse_2.setObjectName("btnSecondary")
        btn_browse_2.clicked.connect(self._browse_attachment_2)
        
        btn_clear_attach_2 = QPushButton("Clear")
        btn_clear_attach_2.setObjectName("btnDanger")
        btn_clear_attach_2.clicked.connect(self._clear_attachment_2)
        
        attach_row_2.addWidget(attach_lbl_2)
        attach_row_2.addWidget(self.attach_path_edit_2, 1)
        attach_row_2.addWidget(btn_browse_2)
        attach_row_2.addWidget(btn_clear_attach_2)
        self.tab_followup_2_layout.addLayout(attach_row_2)
        
        self.tabs.addTab(self.tab_initial, "Initial Outreach")
        self.tabs.addTab(self.tab_followup, "Follow-up 1")
        self.tabs.addTab(self.tab_followup_2, "Follow-up 2")
        
        main_layout.addWidget(self.tabs)
        
        # Preview panel (Downsized)
        preview_lbl = QLabel("Live Preview (using sample username '@cybersolu.agency'):")
        preview_lbl.setObjectName("subHeader")
        preview_lbl.setStyleSheet("font-size: 11px; margin-top: 2px;")
        main_layout.addWidget(preview_lbl)
        
        self.preview_box = QLabel("...")
        self.preview_box.setObjectName("card")
        self.preview_box.setWordWrap(True)
        self.preview_box.setStyleSheet("padding: 8px 12px; font-size: 12px; line-height: 1.4;")
        main_layout.addWidget(self.preview_box)
        
        self.setLayout(main_layout)
        
        self.tabs.currentChanged.connect(self.update_preview)

    def _get_current_list_and_layout(self):
        idx = self.tabs.currentIndex()
        if idx == 0:
            return self.text_boxes_initial, self.messages_layout_initial
        elif idx == 1:
            return self.text_boxes_followup, self.messages_layout_followup
        else:
            return self.text_boxes_followup_2, self.messages_layout_followup_2

    def add_slot(self, content=None, is_followup=0):
        """
        is_followup:
          0  = use whichever tab is currently active (button click path)
          1  = force Followup 1 list (load_messages path)
          2  = force Followup 2 list (load_messages path)
        """
        if content is False or content is None:
            content = ""
            
        # Default: use whatever tab is active
        target_list, target_layout = self._get_current_list_and_layout()
        # Override only when called programmatically with an explicit level
        if is_followup == 1:
            target_list = self.text_boxes_followup
            target_layout = self.messages_layout_followup
        elif is_followup == 2:
            target_list = self.text_boxes_followup_2
            target_layout = self.messages_layout_followup_2
        
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
            self.preview_box.setText(resolved.replace("{username}", "@cybersolu.agency"))
        else:
            self.preview_box.setText("...")
            
    def _browse_attachment(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Attachment 1", "",
            "Supported Files (*.pdf *.jpg *.jpeg *.png *.mp4 *.mov);;All Files (*)"
        )
        if path:
            self.attach_path_edit.setText(path)

    def _clear_attachment(self):
        self.attach_path_edit.clear()

    def _browse_attachment_2(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Attachment 2", "",
            "Supported Files (*.pdf *.jpg *.jpeg *.png *.mp4 *.mov);;All Files (*)"
        )
        if path:
            self.attach_path_edit_2.setText(path)

    def _clear_attachment_2(self):
        self.attach_path_edit_2.clear()

    def load_messages(self):
        path = Path('config/messages.json')
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                msgs = data.get('messages', [])
                followups = data.get('followups', [])
                followups_2 = data.get('followups_2', [])
                attach = data.get('followup_attachment', '')
                attach_2 = data.get('followup_2_attachment', '')

                for m in msgs:
                    self.add_slot(m, is_followup=0)

                for m in followups:
                    self.add_slot(m, is_followup=1)

                for m in followups_2:
                    self.add_slot(m, is_followup=2)

                if attach:
                    self.attach_path_edit.setText(attach)
                if attach_2:
                    self.attach_path_edit_2.setText(attach_2)

        if not self.text_boxes_initial:
            self.add_slot("Hey {username}, love your profile!", is_followup=0)

        if not self.text_boxes_followup:
            self.add_slot("Hey {username}, following up on my previous message!", is_followup=1)

        if not self.text_boxes_followup_2:
            self.add_slot("Hey {username}, this is a second follow-up message!", is_followup=2)

        self.update_preview()

    def save_messages(self):
        msgs_init   = [txt.toPlainText().strip() for txt in self.text_boxes_initial if txt.toPlainText().strip()]
        msgs_follow = [txt.toPlainText().strip() for txt in self.text_boxes_followup if txt.toPlainText().strip()]
        msgs_follow_2 = [txt.toPlainText().strip() for txt in self.text_boxes_followup_2 if txt.toPlainText().strip()]

        if not msgs_init and not msgs_follow and not msgs_follow_2:
            dark_warning(self, "Validation Error", "You must have at least one valid message before saving.")
            return

        for list_msgs in [msgs_init, msgs_follow, msgs_follow_2]:
            for m in list_msgs:
                if len(m) > 1000:
                    dark_warning(self, "Validation Error", "One of your messages exceeds the 1000 character limit.")
                    return

        attach_path = self.attach_path_edit.text().strip()
        attach_path_2 = self.attach_path_edit_2.text().strip()

        Path('config').mkdir(exist_ok=True)
        payload = {
            "messages":            msgs_init,
            "followups":           msgs_follow,
            "followups_2":         msgs_follow_2,
            "followup_attachment": attach_path,
            "followup_2_attachment": attach_path_2
        }
        with open('config/messages.json', 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)

        attach_note = ""
        if attach_path:
            attach_note += f" + attach 1: {Path(attach_path).name}"
        if attach_path_2:
            attach_note += f" + attach 2: {Path(attach_path_2).name}"
            
        dark_info(self, "Saved",
                  f"{len(msgs_init)} Initial, {len(msgs_follow)} Follow-up 1, and {len(msgs_follow_2)} Follow-up 2 template(s) saved.{attach_note}")
