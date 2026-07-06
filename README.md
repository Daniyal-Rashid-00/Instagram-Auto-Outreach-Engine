# CyberSolu DM Engine

*Private Repository - Internal Use Only*

The engine behind CyberSolu's automated outreach and direct messaging campaigns.

## Overview
- **Tech Stack:** Python, Playwright/Selenium (UI Automation), SQLite/Postgres.
- **Purpose:** Automating targeted direct messaging, tracking outreach KPIs, and running "Follow-up Only" campaigns.

## Local Development
1. Activate virtual environment: `venv\Scripts\activate` (Windows)
2. Install dependencies: `pip install -r requirements.txt`
3. Run the engine: `python core/dm_engine.py` (or main execution script)

## Data & Config
- Database definitions and ORM models are in `/data/db.py`.
- Ensure `messages.json` is configured correctly before starting a campaign run.

## Notes & TODOs
- Make sure PDF attachments for follow-ups are correctly sized and linked.
- Monitor for UI glitches or bot-detection constraints when automating.
- Keep the Analytics dashboard updated with the latest parsed metrics.
