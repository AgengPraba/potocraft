from flask import Blueprint, request, jsonify, current_app, send_from_directory, render_template
from PIL import Image
from rembg import remove
import uuid
import os
from werkzeug.utils import secure_filename

process_bp = Blueprint('process', __name__)

@process_bp.route('/upload', methods=['POST'])
def upload():
    file = request.files['photo']
    filename = f"{uuid.uuid4().hex}.png"
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(path)
    return jsonify({"filename": filename})

@process_bp.route('/crop', methods=['POST'])
def crop():
    file = request.files['cropped']
    filename = f"{uuid.uuid4().hex}_cropped.png"
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(path)
    return jsonify({"filename": filename, "cropped_path": f"/{path}"})

@process_bp.route('/remove_bg', methods=['POST'])
def remove_bg():
    data = request.json
    filename = data['filename']
    bg_color = data['bgColor']
    input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

    with Image.open(input_path) as img:
        no_bg = remove(img)
        bg = Image.new("RGBA", no_bg.size, bg_color)
        combined = Image.alpha_composite(bg, no_bg.convert("RGBA"))

        new_name = f"{uuid.uuid4().hex}_nobg.png"
        output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], new_name)
        combined.save(output_path)

    return jsonify({"processed_path": f"/{output_path}", "filename": new_name})

@process_bp.route('/download/<filename>')
def download(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@process_bp.route('/compress', methods=['POST'])
def compress_image():
    file = request.files.get("image")
    quality = int(request.form.get("quality", 70))

    if file:
        original_name = secure_filename(file.filename)

        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        compressed_folder = os.path.join(current_app.root_path, 'static', 'compressed')
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(compressed_folder, exist_ok=True)

        input_path = os.path.join(upload_folder, original_name)
        new_name = f"{uuid.uuid4().hex}_compressed.jpg"
        output_path = os.path.join(compressed_folder, new_name)

        file.save(input_path)

        img = Image.open(input_path)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(output_path, "JPEG", quality=quality)

        print("Original:", original_name)
        print("Compressed:", new_name)

        return render_template(
            'kompresi.jinja',
            original='uploads/' + original_name,
            compressed='compressed/' + new_name
        )

    return "Tidak ada file yang diupload", 400

@process_bp.route('/download/compressed/<filename>')
def download_compressed(filename):
    compressed_folder = os.path.join(current_app.root_path, 'static', 'compressed')
    return send_from_directory(compressed_folder, filename, as_attachment=True)
