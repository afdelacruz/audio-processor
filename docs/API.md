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