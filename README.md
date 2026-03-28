<div align="center">
  <h1>CyberSolu DM Engine</h1>
  <p><strong>An enterprise-grade, multi-threaded desktop application for scalable and organic social media outreach.</strong></p>
  
  ![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
  ![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green?logo=qt&logoColor=white)
  ![Playwright](https://img.shields.io/badge/Automation-Playwright-orange?logo=playwright&logoColor=white)
  ![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey?logo=sqlite&logoColor=white)
</div>

## 📌 Executive Summary

**CyberSolu DM Engine** was developed to solve the complex problem of scaling targeted B2B/B2C outreach on Instagram without triggering algorithmic spam filters. Traditional API-based bots are quickly flagged and banned. This software takes a completely different approach: it leverages **Playwright** to drive a genuine Chromium (Microsoft Edge) browser, mimicking exact human interaction patterns. 

This project demonstrates expertise in **desktop application architecture, concurrent programming (multi-threading), web scraping/automation, and local database management.**

## ✨ Technical Highlights

- **Multi-Threaded Architecture:** Built using `PyQt6`, the architecture rigidly separates the front-end GUI loop from the heavy back-end browser automation tasks. The core engine runs inside a dedicated `QThread`, ensuring the interface remains buttery-smooth and responsive during long automated rendering tasks.
- **Human Behavior Simulation Engine:** To bypass algorithmic detection, the software doesn't just send messages. It dynamically navigates to user profiles, scrolls through their feed organically, identifies and "likes" recent posts (both static images and Reels), and integrates randomized delays between actions.
- **Persistent Session Management:** Implements Playwright's persistent browser contexts to securely save encrypted session cookies locally. This allows users to manage multiple accounts simultaneously without ever needing to re-authenticate manually after the first login.
- **Robust DOM Traversal & Fallbacks:** Built to withstand the constantly shifting React-based DOM of modern social media sites. Employs advanced locator strategies, dynamic waiting mechanisms (abandoning unreliable `networkidle` states in favor of explicit element polling), and graceful exceptions for edge-cases like Private Accounts.
- **Concurrency-Safe Local Database:** Utilizes a completely local **SQLite** database configured with **WAL (Write-Ahead Logging)** mode and autocommits. This ensures the background worker thread, the live logging panel, and the queue management GUI can all read/write seamlessly in real-time without encountering database locks.

## 🏗️ System Architecture

The codebase is modularly designed with strict separation of concerns:

- `/gui` - Contains all PyQt6 UI components, panels (`Dashboard`, `Accounts`, `Queue`, `Settings`), and event listeners.
- `/core` - Houses the business logic, including `dm_engine.py` (the Playwright background worker), variable interpolators for dynamic messaging, and queue managers.
- `/data` - Manages the SQLite schema, initialization, and local storage state.
- `/config` - Handles stateful configurations via JSON payloads (user limits, delay variables).

## 🚀 Key Features Include:
* **Target Queue System:** Bulk import `.txt` targets with automatic deduplication against historical SQLite records (never message the same person twice).
* **Multi-Account Rotation:** Supports adding up to 5 individual account profiles and routing through them sequentially.
* **Intelligent Message Spintax:** Users define a pool of up to 10 unique messages using `{username}` variables, which the engine rotates randomly to avoid shadow-bans.
* **Instant Skip Logic:** Automatically detects if an account is set to Private or has DMs disabled, instantly bypassing the wait-cycle to maintain maximum efficiency.
* **Real-time Analytics:** Live-tracking of Sent, Failed, and Skipped targets, with full `.CSV` export capabilities for external CRM tracking.

## 👨‍💻 Installation & Usage

*(Note: This project is configured to be compiled into a standalone Windows executable `.exe` via PyInstaller for end-users.)*

**Prerequisites:** Python 3.11+, Microsoft Edge
```bash
# 1. Install required packages
pip install -r requirements.txt

# 2. Install Playwright browser binaries
playwright install msedge

# 3. Launch the application
python main.py
```

<hr>
<p align="center"><em>Designed and Developed by <strong>Daniyal Rashid</strong></em></p>
