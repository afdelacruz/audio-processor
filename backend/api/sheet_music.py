"""
Sheet Music API Module

This module contains API endpoints for sheet music conversion.
"""

import os
import uuid
import json
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
import librosa

from processors.sheet_music import (
    preprocess_audio,
    detect_pitches,
    detect_rhythm,
    convert_to_notation,
    generate_sheet_music
)
from processors.sheet_music.guitar_utils import detect_guitar_tuning

# Create a Blueprint for sheet music API endpoints
sheet_music_bp = Blueprint('sheet_music', __name__)


@sheet_music_bp.route('/convert', methods=['POST'])
def convert_audio_to_sheet_music():
    """
    Convert an audio file to sheet music.
    
    Request:
        - Audio file (multipart/form-data)
        - Conversion options (JSON)
    
    Response:
        - job_id: ID for tracking conversion progress
        - status: "processing"
    """
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({
            'status': 'error',
            'message': 'No file part in the request'
        }), 400
    
    file = request.files['file']
    
    # If user does not select file, browser also submits an empty part without filename
    if file.filename == '':
        return jsonify({
            'status': 'error',
            'message': 'No selected file'
        }), 400
    
    # Check if the file is an allowed audio format
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'mp3', 'wav', 'flac', 'ogg'})
    if not allowed_file(file.filename, allowed_extensions):
        return jsonify({
            'status': 'error',
            'message': f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}'
        }), 400
    
    # Create a unique job ID
    job_id = str(uuid.uuid4())
    
    # Create a directory for this job
    job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    # Save the uploaded file
    filename = secure_filename(file.filename)
    file_path = os.path.join(job_dir, filename)
    file.save(file_path)
    
    # Get conversion options
    options = {}
    if 'options' in request.form:
        try:
            options = json.loads(request.form['options'])
        except json.JSONDecodeError:
            return jsonify({
                'status': 'error',
                'message': 'Invalid options format'
            }), 400
    
    # Store job information
    job_info = {
        'job_id': job_id,
        'file_path': file_path,
        'options': options,
        'status': 'processing',
        'progress': 0,
        'result': None,
        'error': None
    }
    
    # Save job info to a file
    with open(os.path.join(job_dir, 'job_info.json'), 'w') as f:
        json.dump(job_info, f)
    
    # Start processing in a background task (using Celery in a real application)
    # For simplicity, we'll process it synchronously here
    try:
        process_audio_file(job_id, file_path, options)
        
        # Update job status
        job_info['status'] = 'completed'
        job_info['progress'] = 100
        
        # Save updated job info
        with open(os.path.join(job_dir, 'job_info.json'), 'w') as f:
            json.dump(job_info, f)
        
        return jsonify({
            'status': 'success',
            'job_id': job_id,
            'message': 'Conversion completed'
        })
    
    except Exception as e:
        # Update job status
        job_info['status'] = 'failed'
        job_info['error'] = str(e)
        
        # Save updated job info
        with open(os.path.join(job_dir, 'job_info.json'), 'w') as f:
            json.dump(job_info, f)
        
        return jsonify({
            'status': 'error',
            'job_id': job_id,
            'message': f'Conversion failed: {str(e)}'
        }), 500


@sheet_music_bp.route('/status/<job_id>', methods=['GET'])
def get_conversion_status(job_id):
    """
    Get the status of a sheet music conversion job.
    
    Response:
        - status: "processing", "completed", or "failed"
        - progress: percentage (0-100)
        - error: error message if failed
    """
    job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
    
    # Check if job exists
    if not os.path.exists(job_dir):
        return jsonify({
            'status': 'error',
            'message': 'Job not found'
        }), 404
    
    # Load job info
    try:
        with open(os.path.join(job_dir, 'job_info.json'), 'r') as f:
            job_info = json.load(f)
        
        return jsonify({
            'status': job_info['status'],
            'progress': job_info['progress'],
            'error': job_info['error']
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get job status: {str(e)}'
        }), 500


@sheet_music_bp.route('/download/<job_id>', methods=['GET'])
def download_sheet_music(job_id):
    """
    Download the generated sheet music.
    
    Query parameters:
        - format: "musicxml", "pdf", "midi", "png", "tablature" (default: "pdf")
    
    Response:
        - File download
    """
    job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
    
    # Check if job exists
    if not os.path.exists(job_dir):
        return jsonify({
            'status': 'error',
            'message': 'Job not found'
        }), 404
    
    # Load job info
    try:
        with open(os.path.join(job_dir, 'job_info.json'), 'r') as f:
            job_info = json.load(f)
        
        # Check if job is completed
        if job_info['status'] != 'completed':
            return jsonify({
                'status': 'error',
                'message': f'Job is not completed (status: {job_info["status"]})'
            }), 400
        
        # Get requested format
        output_format = request.args.get('format', 'pdf').lower()
        
        # Check if the format is valid
        valid_formats = {'musicxml', 'pdf', 'midi', 'png', 'tablature'}
        if output_format not in valid_formats:
            return jsonify({
                'status': 'error',
                'message': f'Invalid format. Allowed formats: {", ".join(valid_formats)}'
            }), 400
        
        # Get the file path
        if output_format == 'musicxml':
            file_path = os.path.join(job_dir, 'sheet_music.xml')
        elif output_format == 'pdf':
            file_path = os.path.join(job_dir, 'sheet_music.pdf')
        elif output_format == 'midi':
            file_path = os.path.join(job_dir, 'sheet_music.mid')
        elif output_format == 'png':
            file_path = os.path.join(job_dir, 'sheet_music.png')
        elif output_format == 'tablature':
            file_path = os.path.join(job_dir, 'sheet_music_tab.json')
        
        # Check if the file exists
        if not os.path.exists(file_path):
            return jsonify({
                'status': 'error',
                'message': f'File not found for format: {output_format}'
            }), 404
        
        # Send the file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f'sheet_music.{output_format}'
        )
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to download file: {str(e)}'
        }), 500


@sheet_music_bp.route('/preview/<job_id>', methods=['GET'])
def preview_sheet_music(job_id):
    """
    Get a preview image of the sheet music.
    
    Response:
        - PNG image data
    """
    job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
    
    # Check if job exists
    if not os.path.exists(job_dir):
        return jsonify({
            'status': 'error',
            'message': 'Job not found'
        }), 404
    
    # Load job info
    try:
        with open(os.path.join(job_dir, 'job_info.json'), 'r') as f:
            job_info = json.load(f)
        
        # Check if job is completed
        if job_info['status'] != 'completed':
            return jsonify({
                'status': 'error',
                'message': f'Job is not completed (status: {job_info["status"]})'
            }), 400
        
        # Get the PNG file path
        file_path = os.path.join(job_dir, 'sheet_music.png')
        
        # Check if the file exists
        if not os.path.exists(file_path):
            return jsonify({
                'status': 'error',
                'message': 'Preview image not found'
            }), 404
        
        # Send the file
        return send_file(
            file_path,
            mimetype='image/png'
        )
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get preview: {str(e)}'
        }), 500


@sheet_music_bp.route('/detect-tuning', methods=['POST'])
def detect_guitar_tuning_endpoint():
    """
    Detect the guitar tuning from an audio file.
    
    Request:
        - Audio file (multipart/form-data)
    
    Response:
        - tuning: Detected tuning name (e.g., 'Standard', 'Drop D')
        - notes: List of detected open string notes
        - midi_notes: List of MIDI note numbers for the tuning
    """
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({
            'status': 'error',
            'message': 'No file part in the request'
        }), 400
    
    file = request.files['file']
    
    # If user does not select file, browser also submits an empty part without filename
    if file.filename == '':
        return jsonify({
            'status': 'error',
            'message': 'No selected file'
        }), 400
    
    # Check if the file is an allowed audio format
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'mp3', 'wav', 'flac', 'ogg'})
    if not allowed_file(file.filename, allowed_extensions):
        return jsonify({
            'status': 'error',
            'message': f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}'
        }), 400
    
    # Create a temporary directory
    temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Save the uploaded file
    filename = secure_filename(file.filename)
    file_path = os.path.join(temp_dir, filename)
    file.save(file_path)
    
    try:
        # Preprocess audio
        audio_data = preprocess_audio(file_path)
        
        # Detect guitar tuning
        tuning_data = detect_guitar_tuning(audio_data)
        
        # Clean up
        os.remove(file_path)
        
        return jsonify({
            'status': 'success',
            'tuning': tuning_data['tuning'],
            'notes': tuning_data['notes'],
            'midi_notes': tuning_data['midi_notes']
        })
    
    except Exception as e:
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return jsonify({
            'status': 'error',
            'message': f'Failed to detect tuning: {str(e)}'
        }), 500


def allowed_file(filename, allowed_extensions):
    """Check if a file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def process_audio_file(job_id, file_path, options):
    """
    Process an audio file and convert it to sheet music.
    
    Args:
        job_id: Job ID
        file_path: Path to the audio file
        options: Conversion options
    """
    job_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], job_id)
    
    # Update job progress
    def update_progress(progress, status='processing'):
        job_info_path = os.path.join(job_dir, 'job_info.json')
        with open(job_info_path, 'r') as f:
            job_info = json.load(f)
        job_info['progress'] = progress
        job_info['status'] = status
        with open(job_info_path, 'w') as f:
            json.dump(job_info, f)
    
    try:
        # Get instrument type from options
        instrument = options.get('instrument', 'piano')
        is_guitar = instrument.lower() in ['guitar', 'acoustic guitar', 'electric guitar']
        
        # Step 1: Preprocess audio
        update_progress(10)
        audio_data = preprocess_audio(file_path, **options)
        
        # Step 2: Detect guitar tuning if instrument is guitar
        if is_guitar:
            update_progress(20)
            tuning_data = detect_guitar_tuning(audio_data)
            options['guitar_tuning'] = tuning_data['midi_notes']
        
        # Step 3: Detect pitches
        update_progress(30)
        pitch_data = detect_pitches(audio_data, instrument=instrument, **options)
        
        # Step 4: Detect rhythm
        update_progress(50)
        rhythm_data = detect_rhythm(audio_data, **options)
        
        # Step 5: Convert to notation
        update_progress(70)
        generate_tablature = options.get('generate_tablature', is_guitar)
        notation_data = convert_to_notation(
            pitch_data, 
            rhythm_data, 
            instrument=instrument,
            generate_tablature=generate_tablature,
            **options
        )
        
        # Step 6: Generate sheet music files
        update_progress(90)
        
        # Generate all formats
        for output_format in ['musicxml', 'pdf', 'midi', 'png']:
            filename = os.path.join(job_dir, 'sheet_music')
            generate_sheet_music(notation_data, output_format, filename=filename)
        
        # Generate tablature if requested and instrument is guitar
        if is_guitar and generate_tablature:
            filename = os.path.join(job_dir, 'sheet_music')
            generate_sheet_music(notation_data, 'tablature', filename=filename)
        
        # Update job status
        update_progress(100, 'completed')
        
        return True
    
    except Exception as e:
        # Update job status
        update_progress(0, 'failed')
        
        # Re-raise the exception
        raise e 