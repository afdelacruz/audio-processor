# API Documentation

## Authentication

### POST /api/auth/register
Register a new user.

### POST /api/auth/login
Authenticate a user and receive a token.

## Audio Files

### POST /api/audio/upload
Upload a new audio file.

### GET /api/audio/files
Get a list of user's audio files.

### GET /api/audio/file/:id
Get details of a specific audio file.

### DELETE /api/audio/file/:id
Delete an audio file.

## Processing

### POST /api/process/convert
Convert an audio file to a different format.

### POST /api/process/analyze
Analyze an audio file and return data.

### POST /api/process/filter
Apply filters to an audio file.

## Sheet Music Conversion

### POST /api/sheet-music/convert
Upload an audio file and convert it to sheet music.

**Request:**
- `file`: Audio file (multipart/form-data)
- `options`: JSON string with conversion options (optional)
  - `instrument_type`: Instrument type to help with pitch detection
  - `tempo_detection`: "auto" or specific BPM
  - `key_signature`: "auto" or specific key
  - `time_signature`: "auto" or specific time signature

**Response:**
```json
{
  "status": "success",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Conversion started"
}
```

### GET /api/sheet-music/status/:job_id
Check the status of a sheet music conversion job.

**Response:**
```json
{
  "status": "processing",
  "progress": 50,
  "error": null
}
```

### GET /api/sheet-music/download/:job_id
Download the generated sheet music.

**Query Parameters:**
- `format`: Output format (musicxml, pdf, midi, png, default: pdf)

**Response:**
- File download

### GET /api/sheet-music/preview/:job_id
Get a preview image of the sheet music.

**Response:**
- PNG image data