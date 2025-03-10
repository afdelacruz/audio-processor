# Audio Processor Backend

This directory contains the Flask backend server for the Audio Processor project.

## Setup

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the development server
python app.py
```

## Structure

- `app.py` - Main application entry point
- `config.py` - Configuration settings
- `api/` - API endpoints
- `auth/` - Authentication logic
- `storage/` - File storage management
- `processors/` - Audio processing functions
- `models/` - Database models
- `utils/` - Utility functions
- `tests/` - Unit and integration tests