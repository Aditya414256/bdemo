import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has an allowed extension."""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'png', 'jpg', 'jpeg'})
    return ext in allowed


def get_file_extension(filename: str) -> str:
    """Extract lowercase file extension."""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''


def save_prescription_file(file_storage) -> tuple[str, str, str]:
    """
    Validate, sanitize, and save uploaded prescription.
    Returns: (stored_filename, original_filename, file_type)
    """
    if not file_storage or file_storage.filename == '':
        raise ValueError("No file provided for upload.")
    
    orig_name = secure_filename(file_storage.filename)
    if not orig_name:
        orig_name = "prescription_upload"

    if not allowed_file(file_storage.filename):
        raise ValueError("Invalid file format. Only PDF, JPG, JPEG, and PNG files are allowed.")
    
    ext = get_file_extension(file_storage.filename)
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    
    upload_dir = Path(current_app.config['UPLOAD_FOLDER'])
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    full_path = upload_dir / unique_filename
    file_storage.save(str(full_path))
    
    file_type = file_storage.mimetype or f"application/{ext}"
    
    return unique_filename, orig_name, file_type


def get_prescription_full_path(stored_filename: str) -> Path:
    """Get absolute Path for a stored prescription filename."""
    upload_dir = Path(current_app.config['UPLOAD_FOLDER'])
    return upload_dir / stored_filename
