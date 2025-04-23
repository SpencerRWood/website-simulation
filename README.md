# Marketing Simulation Framework

This repository provides a simulation framework for analyzing how marketing activities (email, display, direct traffic) influence user behavior and conversions on a theoretical website. It supports seasonality modeling, customizable site structure, and persistent user tracking via a local SQLite database.

---
1. Create virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
```
2. Install required packaged
```bash
pip install -r requirements.txt
```
3. Before running the simulation, run db_setup.py to set up required databases
```bash
python db_setup.py
```
4. Edit config.js to make changes to simulation

5. Run simulation
```bash
python main.py
```