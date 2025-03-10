"""
Audio Preprocessor Module

This module contains functions for preprocessing audio files before pitch and rhythm detection.
"""

import librosa
import numpy as np
from typing import Tuple, Dict, Any


def preprocess_audio(file_path: str, **kwargs) -> Dict[str, Any]:
    """
    Preprocess an audio file for sheet music conversion.
    
    Args:
        file_path: Path to the audio file
        **kwargs: Additional preprocessing options
            - sr: Sample rate (default: 22050)
            - mono: Convert to mono (default: True)
            - normalize: Normalize audio (default: True)
            - trim_silence: Trim silence from beginning and end (default: True)
            
    Returns:
        Dictionary containing:
            - y: Audio time series
            - sr: Sample rate
            - duration: Duration in seconds
            - frames: Audio frames for analysis
    """
    # Set default parameters
    sr = kwargs.get('sr', 22050)
    mono = kwargs.get('mono', True)
    normalize = kwargs.get('normalize', True)
    trim_silence = kwargs.get('trim_silence', True)
    
    # Load audio file
    y, sr = librosa.load(file_path, sr=sr, mono=mono)
    
    # Trim silence
    if trim_silence:
        y, _ = librosa.effects.trim(y, top_db=30)
    
    # Normalize
    if normalize:
        y = librosa.util.normalize(y)
    
    # Calculate duration
    duration = librosa.get_duration(y=y, sr=sr)
    
    # Create frames for analysis
    frame_length = 2048
    hop_length = 512
    frames = librosa.util.frame(y, frame_length=frame_length, hop_length=hop_length)
    
    return {
        'y': y,
        'sr': sr,
        'duration': duration,
        'frames': frames,
        'frame_length': frame_length,
        'hop_length': hop_length
    }


def apply_noise_reduction(y: np.ndarray, sr: int, **kwargs) -> np.ndarray:
    """
    Apply noise reduction to an audio signal.
    
    Args:
        y: Audio time series
        sr: Sample rate
        **kwargs: Additional options
            - n_fft: FFT window size (default: 2048)
            - noise_clip: Clip of noise to use for profile (default: None)
            
    Returns:
        Noise-reduced audio time series
    """
    # This is a simplified implementation
    # For a real application, consider using more sophisticated methods
    
    n_fft = kwargs.get('n_fft', 2048)
    
    # Simple noise reduction using spectral gating
    S_full = librosa.stft(y, n_fft=n_fft)
    S_mag = np.abs(S_full)
    
    # Compute a noise profile from the first 0.5 seconds (assuming it's noise)
    noise_clip = kwargs.get('noise_clip', None)
    if noise_clip is None:
        noise_clip = y[:int(0.5 * sr)]
    
    noise_stft = librosa.stft(noise_clip, n_fft=n_fft)
    noise_mag = np.abs(noise_stft)
    noise_profile = np.mean(noise_mag, axis=1)
    
    # Apply spectral gating
    gain = (S_mag.T - 2 * noise_profile).T
    gain = np.maximum(gain, 0)
    S_cleaned = gain * np.exp(1j * np.angle(S_full))
    
    # Inverse STFT
    y_cleaned = librosa.istft(S_cleaned)
    
    return y_cleaned


def detect_silence(y: np.ndarray, sr: int, **kwargs) -> np.ndarray:
    """
    Detect silent regions in an audio signal.
    
    Args:
        y: Audio time series
        sr: Sample rate
        **kwargs: Additional options
            - top_db: Threshold for silence detection (default: 30)
            
    Returns:
        Array of intervals [start, end] in seconds where audio is non-silent
    """
    top_db = kwargs.get('top_db', 30)
    
    # Get non-silent intervals
    intervals = librosa.effects.split(y, top_db=top_db)
    
    # Convert frame indices to seconds
    intervals_sec = intervals / sr
    
    return intervals_sec 