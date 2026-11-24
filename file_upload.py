import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename):
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'webp', 'gif'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def _save_to_cloudinary(file, subfolder=''):
    """Upload to Cloudinary (used in production / Vercel)."""
    try:
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(
            cloud_name=current_app.config.get('CLOUDINARY_CLOUD_NAME'),
            api_key=current_app.config.get('CLOUDINARY_API_KEY'),
            api_secret=current_app.config.get('CLOUDINARY_API_SECRET'),
        )

        folder = f"findit/{subfolder}" if subfolder else "findit"
        public_id = f"{folder}/{uuid.uuid4().hex}"

        file.seek(0)
        result = cloudinary.uploader.upload(
            file,
            public_id=public_id,
            overwrite=True,
            resource_type="image",
            transformation=[
                {"width": 1600, "height": 1600, "crop": "limit"},
                {"quality": "auto:good"},
                {"fetch_format": "auto"}
            ]
        )
        return result.get("secure_url")
    except Exception as e:
        raise ValueError(f"Cloudinary upload failed: {str(e)}")


def _save_to_local(file, subfolder=''):
    """Save image locally (used in local development)."""
    from PIL import Image

    original_ext = file.filename.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{original_ext}"

    upload_dir = current_app.config['UPLOAD_FOLDER']
    if subfolder:
        upload_dir = os.path.join(upload_dir, subfolder)

    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, unique_name)

    try:
        img = Image.open(file)
        img.verify()
        file.seek(0)
        img = Image.open(file)
        img.thumbnail((1600, 1600))

        if original_ext in ['jpg', 'jpeg']:
            img = img.convert('RGB')
            img.save(file_path, 'JPEG', quality=85, optimize=True)
        elif original_ext == 'png':
            img.save(file_path, 'PNG', optimize=True)
        else:
            img.save(file_path)

        relative_url = f"/uploads/{subfolder + '/' if subfolder else ''}{unique_name}"
        return relative_url
    except Exception as e:
        raise ValueError(f"Failed to process image: {str(e)}")


def save_image(file, subfolder=''):
    """
    Validates and saves an uploaded image.
    - In production (Cloudinary configured): uploads to Cloudinary, returns HTTPS URL.
    - In development: saves locally, returns relative /uploads/... path.
    Returns the URL string or raises ValueError.
    """
    if not file or file.filename == '':
        return None

    if not allowed_file(file.filename):
        raise ValueError("Invalid file format. Allowed formats: PNG, JPG, JPEG, WEBP, GIF.")

    # File size check
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    max_length = current_app.config.get('MAX_CONTENT_LENGTH', 5 * 1024 * 1024)
    if size > max_length:
        raise ValueError(f"File size exceeds maximum allowed limit of {max_length // (1024 * 1024)}MB.")

    # Choose backend
    cloud_name = current_app.config.get('CLOUDINARY_CLOUD_NAME', '').strip()
    if cloud_name:
        return _save_to_cloudinary(file, subfolder)
    else:
        return _save_to_local(file, subfolder)
