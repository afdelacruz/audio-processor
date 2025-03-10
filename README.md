# Audio Processor

A web application for uploading and processing audio files.

## Features

- Upload audio files in various formats (MP3, WAV, FLAC, etc.)
- Process audio files with various functions:
  - Format conversion
  - Audio analysis (frequency spectrum, waveform)
  - Audio filtering and effects
  - Metadata extraction and editing
- User authentication and file management
- Responsive web interface

## Project Structure

```
├── frontend/           # Frontend application
│   ├── public/         # Static files
│   └── src/            # Source code
├── backend/            # Flask backend server
│   ├── api/            # API endpoints
│   ├── auth/           # Authentication
│   ├── storage/        # File storage management
│   └── processors/     # Audio processing functions
└── docs/               # Documentation
```

## Technologies

### Frontend
- React.js
- Web Audio API
- Tailwind CSS

### Backend
- Python with Flask
- MongoDB with PyMongo
- Librosa and Pydub for audio processing

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js (v14+)
- MongoDB
- FFmpeg

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/afdelacruz/audio-processor.git
   cd audio-processor
   ```

2. Set up backend
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Install frontend dependencies
   ```bash
   cd ../frontend
   npm install
   ```

4. Set up environment variables
   - Create `.env` files in both frontend and backend directories
   - Configure database connection, storage paths, etc.

5. Start the development servers
   ```bash
   # In backend directory with venv activated
   python app.py
   
   # In frontend directory
   npm start
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.