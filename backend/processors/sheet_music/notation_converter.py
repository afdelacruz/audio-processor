"""
Notation Converter Module

This module contains functions for converting detected pitches and rhythms to music notation.
"""

import music21
import numpy as np
from typing import List, Dict, Any, Tuple, Optional


def convert_to_notation(pitch_data: Dict[str, Any], rhythm_data: Dict[str, Any], **kwargs) -> music21.stream.Score:
    """
    Convert detected pitches and rhythms to music notation.
    
    Args:
        pitch_data: Dictionary containing pitch detection results
            - notes: List of music21 note objects
            - times: Time points in seconds for each detected pitch
        rhythm_data: Dictionary containing rhythm detection results
            - tempo: Estimated tempo in BPM
            - time_signature: Detected time signature
            - measures: List of measure boundaries
            - quantized_times: Quantized onset times
        **kwargs: Additional options
            - key: Key signature as a string (e.g., 'C', 'F#', default: None for auto-detection)
            - instrument: Instrument name (default: 'Piano')
            - title: Title of the piece (default: 'Transcribed Score')
            - composer: Composer name (default: 'Audio Processor')
            
    Returns:
        music21 Score object containing the transcribed music
    """
    # Extract data
    notes = pitch_data.get('notes', [])
    times = pitch_data.get('times', [])
    
    tempo = rhythm_data.get('tempo', 120.0)
    time_signature = rhythm_data.get('time_signature', music21.meter.TimeSignature('4/4'))
    measures = rhythm_data.get('measures', [])
    quantized_times = rhythm_data.get('quantized_times', [])
    
    # Set default parameters
    key_str = kwargs.get('key', None)
    instrument_name = kwargs.get('instrument', 'Piano')
    title = kwargs.get('title', 'Transcribed Score')
    composer = kwargs.get('composer', 'Audio Processor')
    
    # Create a new score
    score = music21.stream.Score()
    
    # Add metadata
    score.insert(0, music21.metadata.Metadata())
    score.metadata.title = title
    score.metadata.composer = composer
    
    # Create a part for the instrument
    part = music21.stream.Part()
    part.insert(0, music21.instrument.fromString(instrument_name))
    
    # Add time signature
    part.insert(0, time_signature)
    
    # Detect or set key signature
    if key_str:
        key = music21.key.Key(key_str)
    else:
        key = detect_key_signature(notes)
    part.insert(0, key)
    
    # Add tempo marking
    tempo_mark = music21.tempo.MetronomeMark(number=tempo)
    part.insert(0, tempo_mark)
    
    # Create measures and add notes
    create_measures_with_notes(part, notes, quantized_times, measures, time_signature)
    
    # Add the part to the score
    score.insert(0, part)
    
    return score


def detect_key_signature(notes: List[music21.note.Note]) -> music21.key.Key:
    """
    Detect the key signature from a list of notes.
    
    Args:
        notes: List of music21 note objects
        
    Returns:
        music21 Key object
    """
    if not notes:
        return music21.key.Key('C')  # Default to C major if no notes
    
    # Create a stream with the notes
    stream = music21.stream.Stream()
    for note in notes:
        stream.append(note)
    
    # Use music21's key analysis
    key = stream.analyze('key')
    
    return key


def create_measures_with_notes(
    part: music21.stream.Part,
    notes: List[music21.note.Note],
    note_times: List[float],
    measure_times: List[Tuple[float, float]],
    time_signature: music21.meter.TimeSignature
) -> None:
    """
    Create measures and add notes to a part.
    
    Args:
        part: music21 Part object to add measures to
        notes: List of music21 note objects
        note_times: List of note onset times in seconds
        measure_times: List of measure boundary times (start, end) in seconds
        time_signature: music21 TimeSignature object
        
    Returns:
        None (modifies part in-place)
    """
    if not notes or not measure_times:
        # Create a single empty measure if no notes or measure boundaries
        m = music21.stream.Measure()
        m.timeSignature = time_signature
        r = music21.note.Rest()
        r.quarterLength = time_signature.numerator
        m.append(r)
        part.append(m)
        return
    
    # Sort notes by time
    if note_times:
        sorted_indices = np.argsort(note_times)
        notes = [notes[i] for i in sorted_indices]
        note_times = [note_times[i] for i in sorted_indices]
    
    # Create measures
    for i, (start_time, end_time) in enumerate(measure_times):
        m = music21.stream.Measure(number=i+1)
        
        # Find notes that belong in this measure
        measure_notes = []
        for note, time in zip(notes, note_times):
            if start_time <= time < end_time:
                # Adjust note duration if it extends beyond the measure
                if hasattr(note, 'duration') and hasattr(note.duration, 'quarterLength'):
                    note_end_time = time + (note.duration.quarterLength * 60 / 120)  # Assuming 120 BPM
                    if note_end_time > end_time:
                        # Truncate note to end of measure
                        note.duration.quarterLength = (end_time - time) * 120 / 60
                
                measure_notes.append((note, time - start_time))
        
        # If no notes in this measure, add a rest
        if not measure_notes:
            r = music21.note.Rest()
            r.quarterLength = time_signature.numerator
            m.append(r)
        else:
            # Sort notes by their offset within the measure
            measure_notes.sort(key=lambda x: x[1])
            
            # Add notes to the measure
            current_offset = 0.0
            for note, offset in measure_notes:
                # Add rests if there's a gap
                if offset > current_offset:
                    rest_duration = offset - current_offset
                    r = music21.note.Rest()
                    r.quarterLength = rest_duration * 120 / 60  # Convert seconds to quarter notes
                    m.insert(current_offset * 120 / 60, r)
                
                # Add the note
                m.insert(offset * 120 / 60, note)
                current_offset = offset + (note.duration.quarterLength * 60 / 120)
            
            # Add a final rest if needed
            measure_duration = end_time - start_time
            if current_offset < measure_duration:
                rest_duration = measure_duration - current_offset
                r = music21.note.Rest()
                r.quarterLength = rest_duration * 120 / 60
                m.insert(current_offset * 120 / 60, r)
        
        # Add the measure to the part
        part.append(m)


def adjust_note_durations(notes: List[music21.note.Note], times: List[float]) -> List[music21.note.Note]:
    """
    Adjust note durations based on the time between consecutive notes.
    
    Args:
        notes: List of music21 note objects
        times: List of note onset times in seconds
        
    Returns:
        List of notes with adjusted durations
    """
    if len(notes) <= 1:
        return notes
    
    # Sort notes by time
    sorted_indices = np.argsort(times)
    sorted_notes = [notes[i] for i in sorted_indices]
    sorted_times = [times[i] for i in sorted_indices]
    
    # Adjust durations
    for i in range(len(sorted_notes) - 1):
        duration = sorted_times[i + 1] - sorted_times[i]
        # Convert seconds to quarter notes (assuming 60 BPM for simplicity)
        quarter_length = duration * (60 / 60)
        # Ensure minimum duration
        quarter_length = max(quarter_length, 0.25)  # Minimum 16th note
        sorted_notes[i].duration.quarterLength = quarter_length
    
    # Set duration for the last note (use the same as the previous note)
    if len(sorted_notes) > 1:
        sorted_notes[-1].duration.quarterLength = sorted_notes[-2].duration.quarterLength
    
    return sorted_notes


def quantize_durations(notes: List[music21.note.Note]) -> List[music21.note.Note]:
    """
    Quantize note durations to standard note values.
    
    Args:
        notes: List of music21 note objects
        
    Returns:
        List of notes with quantized durations
    """
    # Standard note durations in quarter notes
    standard_durations = [
        0.25,  # 16th note
        0.375,  # Dotted 16th note
        0.5,   # 8th note
        0.75,  # Dotted 8th note
        1.0,   # Quarter note
        1.5,   # Dotted quarter note
        2.0,   # Half note
        3.0,   # Dotted half note
        4.0    # Whole note
    ]
    
    for note in notes:
        # Find the closest standard duration
        duration = note.duration.quarterLength
        closest_duration = min(standard_durations, key=lambda x: abs(x - duration))
        note.duration.quarterLength = closest_duration
    
    return notes 