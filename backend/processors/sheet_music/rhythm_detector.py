"""
Rhythm Detector Module

This module contains functions for detecting rhythm patterns in audio files.
"""

import librosa
import numpy as np
from typing import List, Dict, Any, Tuple
import music21


def detect_rhythm(audio_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """
    Detect rhythm patterns in preprocessed audio data.
    
    Args:
        audio_data: Dictionary containing preprocessed audio data
            - y: Audio time series
            - sr: Sample rate
            - hop_length: Hop length used for framing
        **kwargs: Additional options
            - onset_method: Method for onset detection ('energy', 'hfc', 'complex', default: 'complex')
            - tempo_method: Method for tempo estimation ('default', 'autocorrelation', default: 'default')
            - time_signature: Time signature as a string (e.g., '4/4', default: None for auto-detection)
            
    Returns:
        Dictionary containing:
            - onset_times: Array of detected onset times in seconds
            - tempo: Estimated tempo in BPM
            - beat_times: Array of beat times in seconds
            - time_signature: Detected time signature as a music21 TimeSignature object
            - measures: List of measure boundaries in seconds
    """
    y = audio_data['y']
    sr = audio_data['sr']
    hop_length = audio_data.get('hop_length', 512)
    
    # Set default parameters
    onset_method = kwargs.get('onset_method', 'complex')
    tempo_method = kwargs.get('tempo_method', 'default')
    time_signature_str = kwargs.get('time_signature', None)
    
    # Detect onsets (note beginnings)
    onset_times = detect_onsets(y, sr, hop_length, method=onset_method)
    
    # Estimate tempo
    tempo, beat_times = estimate_tempo(y, sr, hop_length, method=tempo_method)
    
    # Detect or set time signature
    if time_signature_str:
        time_signature = music21.meter.TimeSignature(time_signature_str)
    else:
        time_signature = detect_time_signature(onset_times, beat_times)
    
    # Determine measure boundaries
    measures = determine_measures(beat_times, time_signature)
    
    # Quantize onset times to a musical grid
    quantized_times = quantize_times(onset_times, beat_times, time_signature)
    
    return {
        'onset_times': onset_times,
        'quantized_times': quantized_times,
        'tempo': tempo,
        'beat_times': beat_times,
        'time_signature': time_signature,
        'measures': measures
    }


def detect_onsets(y: np.ndarray, sr: int, hop_length: int, **kwargs) -> np.ndarray:
    """
    Detect note onsets in an audio signal.
    
    Args:
        y: Audio time series
        sr: Sample rate
        hop_length: Hop length for onset detection
        **kwargs: Additional options
            - method: Onset detection method ('energy', 'hfc', 'complex', default: 'complex')
            - threshold: Detection threshold (default: 0.5)
            
    Returns:
        Array of onset times in seconds
    """
    method = kwargs.get('method', 'complex')
    threshold = kwargs.get('threshold', 0.5)
    
    # Compute onset strength
    if method == 'energy':
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    elif method == 'hfc':
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length, feature=librosa.feature.spectral_flux)
    elif method == 'complex':
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length, feature=librosa.feature.spectral_contrast)
    else:
        raise ValueError(f"Unknown onset detection method: {method}")
    
    # Detect onsets
    onset_frames = librosa.onset.onset_detect(
        onset_envelope=onset_env, 
        sr=sr, 
        hop_length=hop_length,
        threshold=threshold
    )
    
    # Convert frames to time
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop_length)
    
    return onset_times


def estimate_tempo(y: np.ndarray, sr: int, hop_length: int, **kwargs) -> Tuple[float, np.ndarray]:
    """
    Estimate tempo and beat times from an audio signal.
    
    Args:
        y: Audio time series
        sr: Sample rate
        hop_length: Hop length for tempo estimation
        **kwargs: Additional options
            - method: Tempo estimation method ('default', 'autocorrelation', default: 'default')
            - start_bpm: Initial tempo estimate in BPM (default: 120)
            
    Returns:
        Tuple containing:
            - Estimated tempo in BPM
            - Array of beat times in seconds
    """
    method = kwargs.get('method', 'default')
    start_bpm = kwargs.get('start_bpm', 120.0)
    
    if method == 'default':
        # Use librosa's default tempo estimation
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop_length, start_bpm=start_bpm)
    elif method == 'autocorrelation':
        # Use autocorrelation-based tempo estimation
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
        tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr, hop_length=hop_length)[0]
        beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr, hop_length=hop_length, start_bpm=tempo)[1]
    else:
        raise ValueError(f"Unknown tempo estimation method: {method}")
    
    # Convert frames to time
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length)
    
    return tempo, beat_times


def detect_time_signature(onset_times: np.ndarray, beat_times: np.ndarray) -> music21.meter.TimeSignature:
    """
    Detect time signature from onset and beat times.
    
    Args:
        onset_times: Array of onset times in seconds
        beat_times: Array of beat times in seconds
        
    Returns:
        music21 TimeSignature object
    """
    # This is a simplified implementation
    # For a real application, consider more sophisticated methods
    
    # Count onsets between consecutive beats
    onsets_per_beat = []
    for i in range(len(beat_times) - 1):
        start = beat_times[i]
        end = beat_times[i + 1]
        count = np.sum((onset_times >= start) & (onset_times < end))
        onsets_per_beat.append(count)
    
    if len(onsets_per_beat) < 4:
        # Not enough data, default to 4/4
        return music21.meter.TimeSignature('4/4')
    
    # Look for patterns in the first few beats
    pattern_length = 4  # Try to find 4-beat patterns first
    
    # Check if the pattern repeats
    if len(onsets_per_beat) >= pattern_length * 2:
        first_pattern = onsets_per_beat[:pattern_length]
        second_pattern = onsets_per_beat[pattern_length:pattern_length*2]
        if np.allclose(first_pattern, second_pattern, atol=1):
            # Pattern repeats, likely 4/4
            return music21.meter.TimeSignature('4/4')
    
    # Try 3/4 time
    pattern_length = 3
    if len(onsets_per_beat) >= pattern_length * 2:
        first_pattern = onsets_per_beat[:pattern_length]
        second_pattern = onsets_per_beat[pattern_length:pattern_length*2]
        if np.allclose(first_pattern, second_pattern, atol=1):
            # Pattern repeats, likely 3/4
            return music21.meter.TimeSignature('3/4')
    
    # Default to 4/4 if no clear pattern
    return music21.meter.TimeSignature('4/4')


def determine_measures(beat_times: np.ndarray, time_signature: music21.meter.TimeSignature) -> List[Tuple[float, float]]:
    """
    Determine measure boundaries from beat times and time signature.
    
    Args:
        beat_times: Array of beat times in seconds
        time_signature: music21 TimeSignature object
        
    Returns:
        List of tuples (start_time, end_time) for each measure
    """
    if len(beat_times) == 0:
        return []
    
    # Get the number of beats per measure
    beats_per_measure = time_signature.numerator
    
    # Group beats into measures
    measures = []
    for i in range(0, len(beat_times), beats_per_measure):
        if i + beats_per_measure <= len(beat_times):
            start_time = beat_times[i]
            end_time = beat_times[i + beats_per_measure - 1]
            # For the last beat in the measure, extend to the next beat if available
            if i + beats_per_measure < len(beat_times):
                end_time = beat_times[i + beats_per_measure]
            measures.append((start_time, end_time))
    
    return measures


def quantize_times(times: np.ndarray, beat_times: np.ndarray, time_signature: music21.meter.TimeSignature) -> np.ndarray:
    """
    Quantize times to a musical grid based on beats and time signature.
    
    Args:
        times: Array of times in seconds to quantize
        beat_times: Array of beat times in seconds
        time_signature: music21 TimeSignature object
        
    Returns:
        Array of quantized times in seconds
    """
    if len(times) == 0 or len(beat_times) < 2:
        return times
    
    # Determine the smallest note division (e.g., sixteenth notes)
    # For simplicity, we'll use 16th notes (4 divisions per beat)
    divisions_per_beat = 4
    
    # Create a grid of possible quantized times
    grid_times = []
    for i in range(len(beat_times) - 1):
        beat_duration = beat_times[i + 1] - beat_times[i]
        division_duration = beat_duration / divisions_per_beat
        for j in range(divisions_per_beat):
            grid_times.append(beat_times[i] + j * division_duration)
    
    # Add the last beat
    if len(beat_times) > 0:
        grid_times.append(beat_times[-1])
    
    # Quantize each time to the nearest grid point
    quantized_times = []
    for t in times:
        # Find the closest grid point
        idx = np.argmin(np.abs(np.array(grid_times) - t))
        quantized_times.append(grid_times[idx])
    
    return np.array(quantized_times) 