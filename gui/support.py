from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGridLayout, QSpacerItem, QSizePolicy, QPushButton
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

class SupportPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        header = QLabel("Support & Info")
        header.setObjectName("headerTitle")
        main_layout.addWidget(header)
        
        # Card 1: About the Engine
        about_card = QFrame()
        about_card.setObjectName("card")
        about_layout = QVBoxLayout(about_card)
        about_layout.setContentsMargins(20, 20, 20, 20)
        about_layout.setSpacing(10)
        
        about_title = QLabel("About CyberSolu DM Engine")
        about_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #FFFFFF;")
        
        about_desc = QLabel(
            "Version 2.0 (Corporate Edition V4 UI)\n\n"
            "A precision Instagram direct message outward engine optimized for stability\n"
            "and headless profile scaling. Architected and developed by Daniyal Rashid."
        )
        about_desc.setObjectName("subHeader")
        
        about_layout.addWidget(about_title)
        about_layout.addWidget(about_desc)
        main_layout.addWidget(about_card)
        
        # Card 2: Contact
        contact_card = QFrame()
        contact_card.setObjectName("card")
        contact_layout = QVBoxLayout(contact_card)
        contact_layout.setContentsMargins(20, 20, 20, 20)
        contact_layout.setSpacing(15)
        
        contact_title = QLabel("Contact & Developer")
        contact_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #FFFFFF;")
        contact_layout.addWidget(contact_title)
        
        # Info grid
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        grid.setHorizontalSpacing(30)
        
        # Email
        lbl_email = QLabel("Email:")
        lbl_email.setObjectName("subHeader")
        val_email = QLabel("the.daniyal.rashid@gmail.com")
        val_email.setStyleSheet("color: #FFFFFF; font-weight: 500;")
        val_email.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        # Phone
        lbl_phone = QLabel("Phone:")
        lbl_phone.setObjectName("subHeader")
        val_phone = QLabel("+92-313-7840038")
        val_phone.setStyleSheet("color: #FFFFFF; font-weight: 500;")
        val_phone.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        # Location
        lbl_loc = QLabel("Location:")
        lbl_loc.setObjectName("subHeader")
        val_loc = QLabel("Gujranwala, Punjab, Pakistan")
        val_loc.setStyleSheet("color: #FFFFFF; font-weight: 500;")
        
        grid.addWidget(lbl_email, 0, 0)
        grid.addWidget(val_email, 0, 1)
        grid.addWidget(lbl_phone, 1, 0)
        grid.addWidget(val_phone, 1, 1)
        grid.addWidget(lbl_loc, 2, 0)
        grid.addWidget(val_loc, 2, 1)
        
        contact_layout.addLayout(grid)
        
        # Divider or spacing
        contact_layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        btn_github = QPushButton("GitHub Portfolio")
        btn_github.setObjectName("btnWarning") # Ghost dark aesthetics
        btn_github.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/Daniyal-Rashid-00")))
        
        btn_linkedin = QPushButton("LinkedIn Profile")
        btn_linkedin.setObjectName("btnWarning")
        btn_linkedin.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.linkedin.com/in/the-daniyal-rashid/")))
        
        btn_layout.addWidget(btn_github)
        btn_layout.addWidget(btn_linkedin)
        btn_layout.addStretch()
        
        contact_layout.addLayout(btn_layout)
        main_layout.addWidget(contact_card)
        
        # Add Stretch at the bottom to push everything up
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        self.setLayout(main_layout)
