"""
Guitar Utilities Module

This module contains utility functions for guitar-specific processing.
"""

import numpy as np
import librosa
import music21
from typing import List, Dict, Any, Tuple, Optional, Union


# Standard guitar tuning (E2, A2, D3, G3, B3, E4)
STANDARD_TUNING = [40, 45, 50, 55, 59, 64]  # MIDI note numbers

# Common alternate tunings
ALTERNATE_TUNINGS = {
    'Drop D': [38, 45, 50, 55, 59, 64],       # D2, A2, D3, G3, B3, E4
    'Half Step Down': [39, 44, 49, 54, 58, 63],  # Eb2, Ab2, Db3, Gb3, Bb3, Eb4
    'Open G': [38, 43, 50, 55, 59, 62],       # D2, G2, D3, G3, B3, D4
    'Open D': [38, 45, 50, 54, 57, 62],       # D2, A2, D3, F#3, A3, D4
    'DADGAD': [38, 45, 50, 55, 57, 62]        # D2, A2, D3, G3, A3, D4
}

# Guitar range (E2 to E6 in standard tuning)
GUITAR_MIN_FREQ = 82.41  # E2
GUITAR_MAX_FREQ = 1318.51  # E6

# Common guitar chord shapes (represented as fret positions on strings, -1 means string not played)
COMMON_CHORDS = {
    'C': [(0, 3), (1, 2), (2, 0), (3, 1), (4, 0), (5, 0)],  # x32010
    'D': [(0, -1), (1, 0), (2, 0), (3, 2), (4, 3), (5, 2)],  # xx0232
    'E': [(0, 0), (1, 2), (2, 2), (3, 1), (4, 0), (5, 0)],  # 022100
    'G': [(0, 3), (1, 2), (2, 0), (3, 0), (4, 0), (5, 3)],  # 320003
    'A': [(0, 0), (1, 0), (2, 2), (3, 2), (4, 2), (5, 0)],  # x02220
    # Add more common chords as needed
}


def detect_guitar_tuning(audio_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """
    Detect the guitar tuning from audio data.
    
    Args:
        audio_data: Dictionary containing preprocessed audio data
            - y: Audio time series
            - sr: Sample rate
        **kwargs: Additional options
            
    Returns:
        Dictionary containing:
            - tuning: Detected tuning name (e.g., 'Standard', 'Drop D')
            - notes: List of detected open string notes
            - midi_notes: List of MIDI note numbers for the tuning
    """
    y = audio_data['y']
    sr = audio_data['sr']
    
    # This is a simplified implementation
    # In a real application, you would analyze the audio for open string frequencies
    
    # For now, we'll just return standard tuning
    tuning_name = 'Standard'
    tuning_notes = ['E2', 'A2', 'D3', 'G3', 'B3', 'E4']
    tuning_midi = STANDARD_TUNING
    
    return {
        'tuning': tuning_name,
        'notes': tuning_notes,
        'midi_notes': tuning_midi
    }


def constrain_to_guitar_range(frequencies: np.ndarray) -> np.ndarray:
    """
    Constrain detected frequencies to the guitar range.
    
    Args:
        frequencies: Array of frequencies in Hz
        
    Returns:
        Array of frequencies constrained to guitar range
    """
    # Set frequencies outside guitar range to 0
    return np.where(
        (frequencies >= GUITAR_MIN_FREQ) & (frequencies <= GUITAR_MAX_FREQ),
        frequencies,
        0
    )


def detect_guitar_chords(notes: List[music21.note.Note], **kwargs) -> List[Dict[str, Any]]:
    """
    Detect guitar chords from a list of notes.
    
    Args:
        notes: List of music21 note objects
        **kwargs: Additional options
            - tuning: Guitar tuning as list of MIDI note numbers (default: standard tuning)
            
    Returns:
        List of dictionaries containing chord information:
            - name: Chord name (e.g., 'C', 'G7')
            - positions: List of (string, fret) positions
            - start_time: Start time of the chord
            - duration: Duration of the chord
    """
    # This is a simplified implementation
    # In a real application, you would analyze the notes to identify chords
    
    # For now, we'll just return an empty list
    return []


def notes_to_tablature(notes: List[music21.note.Note], **kwargs) -> List[Dict[str, Any]]:
    """
    Convert music21 notes to guitar tablature.
    
    Args:
        notes: List of music21 note objects
        **kwargs: Additional options
            - tuning: Guitar tuning as list of MIDI note numbers (default: standard tuning)
            
    Returns:
        List of dictionaries containing tablature information:
            - string: Guitar string number (0-5, where 0 is the lowest E string)
            - fret: Fret number
            - start_time: Start time in seconds
            - duration: Duration in seconds
            - techniques: List of techniques (e.g., 'bend', 'slide')
    """
    tuning = kwargs.get('tuning', STANDARD_TUNING)
    
    tablature = []
    
    for note in notes:
        if not hasattr(note, 'pitch') or not hasattr(note.pitch, 'midi'):
            continue
        
        midi_note = note.pitch.midi
        
        # Find possible positions on the fretboard
        positions = []
        for string, open_note in enumerate(tuning):
            fret = midi_note - open_note
            if 0 <= fret <= 24:  # Standard guitar has 24 frets
                positions.append((string, fret))
        
        if not positions:
            continue  # Note is not playable on guitar
        
        # Choose the best position (simplistic approach - choose lowest fret)
        best_position = min(positions, key=lambda p: p[1])
        
        # Get start time and duration
        start_time = note.offset if hasattr(note, 'offset') else 0
        duration = note.duration.quarterLength if hasattr(note, 'duration') else 1
        
        tablature.append({
            'string': best_position[0],
            'fret': best_position[1],
            'start_time': start_time,
            'duration': duration,
            'techniques': []
        })
    
    return tablature


def optimize_fretboard_positions(tablature: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
    """
    Optimize fretboard positions for playability.
    
    Args:
        tablature: List of tablature dictionaries
        **kwargs: Additional options
            - max_stretch: Maximum fret stretch (default: 4)
            - preferred_position: Preferred fret position (default: 0)
            
    Returns:
        Optimized tablature list
    """
    # This is a simplified implementation
    # In a real application, you would use a more sophisticated algorithm
    
    # For now, we'll just return the input tablature
    return tablature


def generate_guitar_chord_diagram(chord_name: str, positions: List[Tuple[int, int]]) -> Dict[str, Any]:
    """
    Generate a guitar chord diagram.
    
    Args:
        chord_name: Name of the chord (e.g., 'C', 'G7')
        positions: List of (string, fret) positions
        
    Returns:
        Dictionary containing chord diagram information
    """
    # This is a placeholder
    # In a real application, you would generate an actual diagram
    
    return {
        'name': chord_name,
        'positions': positions
    }


def detect_guitar_techniques(audio_data: Dict[str, Any], notes: List[music21.note.Note], **kwargs) -> Dict[str, List[Dict[str, Any]]]:
    """
    Detect guitar-specific techniques from audio data.
    
    Args:
        audio_data: Dictionary containing preprocessed audio data
        notes: List of music21 note objects
        **kwargs: Additional options
            
    Returns:
        Dictionary containing detected techniques:
            - bends: List of bend information
            - slides: List of slide information
            - hammer_ons: List of hammer-on information
            - pull_offs: List of pull-off information
    """
    # This is a placeholder
    # In a real application, you would analyze the audio for techniques
    
    return {
        'bends': [],
        'slides': [],
        'hammer_ons': [],
        'pull_offs': []
    } 