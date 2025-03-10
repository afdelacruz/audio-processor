"""
Sheet Music Conversion Tests

This module contains tests for the sheet music conversion functionality.
"""

import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock

from processors.sheet_music import (
    preprocess_audio,
    detect_pitches,
    detect_rhythm,
    convert_to_notation,
    generate_sheet_music
)


@pytest.fixture
def sample_audio_file():
    """Create a temporary audio file for testing."""
    # This is a placeholder - in a real test, you would use a real audio file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        f.write(b'dummy audio data')
        temp_file = f.name
    
    yield temp_file
    
    # Clean up
    if os.path.exists(temp_file):
        os.remove(temp_file)


@pytest.fixture
def mock_audio_data():
    """Create mock audio data for testing."""
    import numpy as np
    
    # Create a simple sine wave
    sr = 22050
    duration = 2.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    
    # A4 = 440 Hz
    y = 0.5 * np.sin(2 * np.pi * 440 * t)
    
    return {
        'y': y,
        'sr': sr,
        'duration': duration,
        'hop_length': 512,
        'frame_length': 2048,
        'frames': np.array([y[i:i+2048] for i in range(0, len(y), 512) if i+2048 <= len(y)])
    }


def test_preprocess_audio(sample_audio_file):
    """Test audio preprocessing."""
    # Mock librosa.load to avoid actually loading the file
    with patch('librosa.load') as mock_load, \
         patch('librosa.effects.trim') as mock_trim, \
         patch('librosa.util.normalize') as mock_normalize, \
         patch('librosa.get_duration') as mock_duration, \
         patch('librosa.util.frame') as mock_frame:
        
        # Set up mocks
        mock_load.return_value = (MagicMock(), 22050)
        mock_trim.return_value = (MagicMock(), MagicMock())
        mock_normalize.return_value = MagicMock()
        mock_duration.return_value = 2.0
        mock_frame.return_value = MagicMock()
        
        # Call the function
        result = preprocess_audio(sample_audio_file)
        
        # Check that the function returns the expected keys
        assert 'y' in result
        assert 'sr' in result
        assert 'duration' in result
        assert 'frames' in result
        assert 'frame_length' in result
        assert 'hop_length' in result


def test_detect_pitches(mock_audio_data):
    """Test pitch detection."""
    # Mock librosa.core.piptrack to avoid actual pitch detection
    with patch('librosa.core.piptrack') as mock_piptrack, \
         patch('librosa.times_like') as mock_times_like:
        
        # Set up mocks
        mock_piptrack.return_value = (MagicMock(), MagicMock())
        mock_times_like.return_value = MagicMock()
        
        # Call the function
        result = detect_pitches(mock_audio_data, algorithm='yin')
        
        # Check that the function returns the expected keys
        assert 'pitches' in result
        assert 'pitch_confidence' in result
        assert 'notes' in result
        assert 'times' in result


def test_detect_rhythm(mock_audio_data):
    """Test rhythm detection."""
    # Mock librosa functions to avoid actual rhythm detection
    with patch('librosa.onset.onset_strength') as mock_onset_strength, \
         patch('librosa.onset.onset_detect') as mock_onset_detect, \
         patch('librosa.frames_to_time') as mock_frames_to_time, \
         patch('librosa.beat.beat_track') as mock_beat_track:
        
        # Set up mocks
        mock_onset_strength.return_value = MagicMock()
        mock_onset_detect.return_value = MagicMock()
        mock_frames_to_time.return_value = MagicMock()
        mock_beat_track.return_value = (120.0, MagicMock())
        
        # Call the function
        result = detect_rhythm(mock_audio_data)
        
        # Check that the function returns the expected keys
        assert 'onset_times' in result
        assert 'quantized_times' in result
        assert 'tempo' in result
        assert 'beat_times' in result
        assert 'time_signature' in result
        assert 'measures' in result


def test_convert_to_notation():
    """Test conversion to music notation."""
    # Mock pitch and rhythm data
    pitch_data = {
        'notes': [],
        'times': []
    }
    
    rhythm_data = {
        'tempo': 120.0,
        'time_signature': MagicMock(),
        'measures': [],
        'quantized_times': []
    }
    
    # Call the function
    result = convert_to_notation(pitch_data, rhythm_data)
    
    # Check that the result is a music21.stream.Score object
    assert hasattr(result, 'insert')
    assert hasattr(result, 'metadata')


def test_generate_sheet_music():
    """Test sheet music generation."""
    # Mock music21.stream.Score
    mock_score = MagicMock()
    mock_score.write = MagicMock()
    
    # Call the function
    with patch('tempfile.gettempdir') as mock_tempdir, \
         patch('os.urandom') as mock_urandom, \
         patch('os.path.join') as mock_join:
        
        # Set up mocks
        mock_tempdir.return_value = '/tmp'
        mock_urandom.return_value = b'abcd'
        mock_join.return_value = '/tmp/sheet_music_61626364'
        
        # Call the function
        result = generate_sheet_music(mock_score, 'musicxml')
        
        # Check that the function returns the expected keys
        assert 'file_path' in result
        assert 'format' in result
        assert result['format'] == 'musicxml' 