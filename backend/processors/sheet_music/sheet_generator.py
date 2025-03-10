"""
Sheet Generator Module

This module contains functions for generating sheet music files in various formats.
"""

import os
import tempfile
import music21
from typing import Dict, Any, Optional, Union, BinaryIO


def generate_sheet_music(score: music21.stream.Score, output_format: str = 'musicxml', **kwargs) -> Dict[str, Any]:
    """
    Generate sheet music files from a music21 Score object.
    
    Args:
        score: music21 Score object
        output_format: Output format ('musicxml', 'pdf', 'midi', 'png', default: 'musicxml')
        **kwargs: Additional options
            - filename: Output filename (without extension, default: temporary file)
            - dpi: DPI for image formats (default: 300)
            
    Returns:
        Dictionary containing:
            - file_path: Path to the generated file
            - format: Format of the generated file
            - content: File content as bytes (if requested)
    """
    # Set default parameters
    filename = kwargs.get('filename', None)
    dpi = kwargs.get('dpi', 300)
    return_content = kwargs.get('return_content', False)
    
    # Create a temporary file if no filename is provided
    if filename is None:
        temp_dir = tempfile.gettempdir()
        filename = os.path.join(temp_dir, f"sheet_music_{os.urandom(4).hex()}")
    
    # Generate the sheet music in the requested format
    if output_format.lower() == 'musicxml':
        file_path = f"{filename}.xml"
        score.write('musicxml', fp=file_path)
    
    elif output_format.lower() == 'pdf':
        file_path = f"{filename}.pdf"
        score.write('musicxml.pdf', fp=file_path)
    
    elif output_format.lower() == 'midi':
        file_path = f"{filename}.mid"
        score.write('midi', fp=file_path)
    
    elif output_format.lower() == 'png':
        file_path = f"{filename}.png"
        score.write('musicxml.png', fp=file_path, dpi=dpi)
    
    else:
        raise ValueError(f"Unsupported output format: {output_format}")
    
    result = {
        'file_path': file_path,
        'format': output_format.lower()
    }
    
    # Read the file content if requested
    if return_content:
        with open(file_path, 'rb') as f:
            result['content'] = f.read()
    
    return result


def convert_format(input_file: Union[str, BinaryIO], input_format: str, output_format: str, **kwargs) -> Dict[str, Any]:
    """
    Convert between sheet music formats.
    
    Args:
        input_file: Path to input file or file-like object
        input_format: Input format ('musicxml', 'midi')
        output_format: Output format ('musicxml', 'pdf', 'midi', 'png')
        **kwargs: Additional options
            - filename: Output filename (without extension, default: temporary file)
            - dpi: DPI for image formats (default: 300)
            
    Returns:
        Dictionary containing:
            - file_path: Path to the generated file
            - format: Format of the generated file
            - content: File content as bytes (if requested)
    """
    # Load the input file
    if input_format.lower() == 'musicxml':
        score = music21.converter.parse(input_file, format='musicxml')
    elif input_format.lower() == 'midi':
        score = music21.converter.parse(input_file, format='midi')
    else:
        raise ValueError(f"Unsupported input format: {input_format}")
    
    # Generate the output file
    return generate_sheet_music(score, output_format, **kwargs)


def create_empty_score(title: str = 'New Score', **kwargs) -> music21.stream.Score:
    """
    Create an empty score with basic metadata.
    
    Args:
        title: Title of the score
        **kwargs: Additional options
            - composer: Composer name (default: '')
            - time_signature: Time signature as a string (default: '4/4')
            - key: Key signature as a string (default: 'C')
            - instrument: Instrument name (default: 'Piano')
            
    Returns:
        Empty music21 Score object
    """
    # Set default parameters
    composer = kwargs.get('composer', '')
    time_signature_str = kwargs.get('time_signature', '4/4')
    key_str = kwargs.get('key', 'C')
    instrument_name = kwargs.get('instrument', 'Piano')
    
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
    time_signature = music21.meter.TimeSignature(time_signature_str)
    part.insert(0, time_signature)
    
    # Add key signature
    key = music21.key.Key(key_str)
    part.insert(0, key)
    
    # Add an empty measure
    m = music21.stream.Measure(number=1)
    m.timeSignature = time_signature
    r = music21.note.Rest()
    r.quarterLength = time_signature.numerator
    m.append(r)
    part.append(m)
    
    # Add the part to the score
    score.insert(0, part)
    
    return score 