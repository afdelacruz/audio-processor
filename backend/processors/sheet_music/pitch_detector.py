"""
Pitch Detector Module

This module contains functions for detecting pitches in audio files.
"""

import librosa
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import music21
from .guitar_utils import constrain_to_guitar_range, detect_guitar_chords


def detect_pitches(audio_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """
    Detect pitches in preprocessed audio data.
    
    Args:
        audio_data: Dictionary containing preprocessed audio data
            - y: Audio time series
            - sr: Sample rate
            - frames: Audio frames
            - hop_length: Hop length used for framing
        **kwargs: Additional options
            - algorithm: Pitch detection algorithm ('yin', 'pyin', 'crepe', default: 'pyin')
            - fmin: Minimum frequency in Hz (default: 65.0, low C)
            - fmax: Maximum frequency in Hz (default: 2093.0, high C)
            - instrument: Instrument type ('guitar', 'piano', etc., default: None)
            - guitar_tuning: Guitar tuning as list of MIDI note numbers (default: standard tuning)
            
    Returns:
        Dictionary containing:
            - pitches: Array of detected pitches in Hz
            - pitch_confidence: Confidence values for pitch detection
            - notes: List of music21 note objects
            - times: Time points in seconds for each detected pitch
            - chords: List of detected chords (if instrument is 'guitar')
    """
    y = audio_data['y']
    sr = audio_data['sr']
    hop_length = audio_data.get('hop_length', 512)
    
    # Set default parameters
    algorithm = kwargs.get('algorithm', 'pyin')
    instrument = kwargs.get('instrument', None)
    
    # Set frequency range based on instrument
    if instrument == 'guitar':
        fmin = kwargs.get('fmin', 82.41)  # E2 (lowest standard guitar note)
        fmax = kwargs.get('fmax', 1318.51)  # E6 (high guitar note)
    else:
        fmin = kwargs.get('fmin', 65.0)  # Low C
        fmax = kwargs.get('fmax', 2093.0)  # High C
    
    # Detect pitches using the specified algorithm
    if algorithm == 'yin':
        pitches, magnitudes = librosa.core.piptrack(
            y=y, sr=sr, fmin=fmin, fmax=fmax, hop_length=hop_length
        )
        # Select the most likely pitch for each frame
        pitch_indices = np.argmax(magnitudes, axis=0)
        pitches = np.array([pitches[pitch_indices[i], i] for i in range(len(pitch_indices))])
        pitch_confidence = np.max(magnitudes, axis=0)
        
    elif algorithm == 'pyin':
        # pYIN is more accurate but slower
        pitches, pitch_confidence = librosa.core.pitch_tuning(y)
        
    elif algorithm == 'crepe':
        # CREPE is a neural network-based pitch tracker
        # This is a placeholder - actual implementation would use the crepe package
        # For simplicity, we'll use librosa's pitch tracking here
        pitches, pitch_confidence = librosa.core.piptrack(
            y=y, sr=sr, fmin=fmin, fmax=fmax, hop_length=hop_length
        )
        pitch_indices = np.argmax(pitch_confidence, axis=0)
        pitches = np.array([pitches[pitch_indices[i], i] for i in range(len(pitch_indices))])
        pitch_confidence = np.max(pitch_confidence, axis=0)
    
    else:
        raise ValueError(f"Unknown pitch detection algorithm: {algorithm}")
    
    # Apply instrument-specific constraints
    if instrument == 'guitar':
        pitches = constrain_to_guitar_range(pitches)
    
    # Convert time frames to seconds
    times = librosa.times_like(pitches, sr=sr, hop_length=hop_length)
    
    # Convert frequencies to music21 note objects
    notes = frequencies_to_notes(pitches, times, pitch_confidence)
    
    result = {
        'pitches': pitches,
        'pitch_confidence': pitch_confidence,
        'notes': notes,
        'times': times
    }
    
    # Detect chords for guitar
    if instrument == 'guitar':
        guitar_tuning = kwargs.get('guitar_tuning', None)
        chords = detect_guitar_chords(notes, tuning=guitar_tuning)
        result['chords'] = chords
    
    return result


def frequencies_to_notes(
    frequencies: np.ndarray, 
    times: np.ndarray, 
    confidence: np.ndarray, 
    confidence_threshold: float = 0.7
) -> List[music21.note.Note]:
    """
    Convert frequencies in Hz to music21 note objects.
    
    Args:
        frequencies: Array of frequencies in Hz
        times: Array of time points in seconds
        confidence: Array of confidence values for each frequency
        confidence_threshold: Minimum confidence to consider a pitch valid
        
    Returns:
        List of music21 note objects
    """
    notes = []
    
    # Filter out low-confidence pitches and zeros
    valid_indices = np.where((confidence > confidence_threshold) & (frequencies > 0))[0]
    
    if len(valid_indices) == 0:
        return notes
    
    # Group consecutive frames with similar pitches into notes
    current_note_start = times[valid_indices[0]]
    current_pitch = frequencies[valid_indices[0]]
    current_pitches = [current_pitch]
    
    for i in range(1, len(valid_indices)):
        idx = valid_indices[i]
        prev_idx = valid_indices[i-1]
        
        # If this is a consecutive frame and the pitch is similar
        if idx == prev_idx + 1 and is_same_pitch(frequencies[idx], current_pitch):
            current_pitches.append(frequencies[idx])
        else:
            # End the current note and start a new one
            note_duration = times[prev_idx] - current_note_start
            if note_duration > 0.05:  # Minimum duration threshold (50ms)
                # Use the median pitch for stability
                median_pitch = np.median(current_pitches)
                note = create_note_from_frequency(median_pitch, note_duration)
                if note:
                    notes.append(note)
            
            # Start a new note
            current_note_start = times[idx]
            current_pitch = frequencies[idx]
            current_pitches = [current_pitch]
    
    # Add the last note
    if len(current_pitches) > 0:
        last_idx = valid_indices[-1]
        note_duration = times[last_idx] - current_note_start
        if note_duration > 0.05:
            median_pitch = np.median(current_pitches)
            note = create_note_from_frequency(median_pitch, note_duration)
            if note:
                notes.append(note)
    
    return notes


def is_same_pitch(freq1: float, freq2: float, tolerance: float = 0.5) -> bool:
    """
    Check if two frequencies represent the same pitch within a tolerance.
    
    Args:
        freq1: First frequency in Hz
        freq2: Second frequency in Hz
        tolerance: Tolerance in semitones
        
    Returns:
        True if the frequencies represent the same pitch, False otherwise
    """
    if freq1 <= 0 or freq2 <= 0:
        return False
    
    # Convert frequency ratio to semitones
    semitone_diff = 12 * np.log2(freq1 / freq2)
    
    return abs(semitone_diff) < tolerance


def create_note_from_frequency(frequency: float, duration: float) -> Optional[music21.note.Note]:
    """
    Create a music21 note object from a frequency and duration.
    
    Args:
        frequency: Frequency in Hz
        duration: Duration in seconds
        
    Returns:
        music21 note object or None if the frequency is invalid
    """
    if frequency <= 0:
        return None
    
    # Convert frequency to MIDI note number
    midi_number = librosa.hz_to_midi(frequency)
    
    # Create a music21 note
    note = music21.note.Note()
    note.pitch.midi = round(midi_number)
    
    # Convert duration from seconds to quarter notes (assuming 60 BPM)
    # This will be adjusted later based on tempo detection
    quarter_length = duration * (60 / 60) / 4
    note.duration.quarterLength = quarter_length
    
    return note 