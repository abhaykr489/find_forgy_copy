import os
import uuid
import time
import re
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, send_from_directory
import cv2
import pytesseract
import numpy as np
from PIL import Image, ImageChops

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['IMAGES_FOLDER'] = 'images'


@app.route('/')
def index():
    return render_template('index.html')


# Function to get bounding box of detected text
def get_text_bounding_box(image_path, detected_text):
    color_image = cv2.imread(image_path)
    target_width = 640
    target_height = 480
    color_image = cv2.resize(color_image, (target_width, target_height))

    # Convert color image to grayscale
    gray_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
    _, binary_image = cv2.threshold(gray_image, 150, 255, cv2.THRESH_BINARY_INV)

    boxes = pytesseract.image_to_boxes(binary_image)
    for box in boxes.splitlines():
        box = box.split()
        x, y, w, h = int(box[1]), int(box[2]), int(box[3]), int(box[4])
        text = box[0]
        if text == detected_text:
            return x, y, w, h
    return None


# Function to detect scribbling or overwriting forgery
def detect_scribbling_or_overwriting(image_path):
    extracted_text = pytesseract.image_to_string(Image.open(image_path))
    date_pattern = r'\b\d{2}/\d{2}/\d{4}\b'
    name_pattern = r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b'
    amount_pattern = r'\$\d+\.\d{2}\b'
    combined_pattern = f"({'|'.join([date_pattern, name_pattern, amount_pattern])})"
    matches = re.finditer(combined_pattern, extracted_text)

    forgery_areas = []
    for match in matches:
        bounding_box = get_text_bounding_box(image_path, match.group())
        if bounding_box is not None:
            x, y, w, h = bounding_box
            forgery_areas.append(((x, y, x + w, y + h), "Scribbling-Overwriting"))
    return forgery_areas


# Function to detect digital forgery
def detect_digital_forgery(image_path):
    try:
        print("Inside detect_digital_forgery function")
        original_image = cv2.imread(image_path)
        target_width = 640
        target_height = 480
        original_image = cv2.resize(original_image, (target_width, target_height))
        gray_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)

        cv2.imwrite("original_temp.jpg", gray_image, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        original_temp = cv2.imread("original_temp.jpg")
        ela_image = cv2.absdiff(original_temp, gray_image)
        print(ela_image.shape)
        ela_image = cv2.cvtColor(ela_image, cv2.COLOR_BGR2GRAY)
        ela_threshold = 40
        ela_binary = cv2.threshold(ela_image, ela_threshold, 255, cv2.THRESH_BINARY)[1]
        contours, _ = cv2.findContours(ela_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        forgery_areas = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            forgery_areas.append(((x, y, x + w, y + h), "Digital Forgery"))
        os.remove("original_temp.jpg")
        print("Function execution completed")
        return forgery_areas
    except Exception as e:
        print("An error occurred:", str(e))
        return []


# Function to detect whitener forgery
def detect_whitener_forgery(image_path):
    color_image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    target_width = 640
    target_height = 480
    color_image = cv2.resize(color_image, (target_width, target_height))

    gray_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

    whitener_threshold = 200
    whitener_pixel_count = np.sum(gray_image > whitener_threshold)
    whitener_percentage_threshold = 0.1
    total_pixels = gray_image.size
    whitener_percentage = whitener_pixel_count / total_pixels

    forgery_areas = []
    if whitener_percentage > whitener_percentage_threshold:
        contours, _ = cv2.findContours(gray_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            forgery_areas.append(((x, y, x + w, y + h), "Whitener Forgery"))
    return forgery_areas


# Function to detect data manipulation forgery
def detect_data_manipulation_forgery(image_path):
    extracted_text = pytesseract.image_to_string(cv2.imread(image_path))
    date_pattern = r'\b\d{2}/\d{2}/\d{4}\b'
    amount_pattern = r'\$\d+\.\d{2}\b'
    combined_pattern = f"({'|'.join([date_pattern, amount_pattern])})"
    matches = re.finditer(combined_pattern, extracted_text)

    forgery_areas = []
    for match in matches:
        x, y, w, h = get_text_bounding_box(image_path, match.group())
        if (x, y, w, h) is not None:
            forgery_areas.append(((x, y, x + w, y + h), "Data Manipulation"))
    return forgery_areas


# Function to detect and mark forgery areas
def detect_and_mark_forgery(original_path):
    forgery_areas = []
    forgery_types = []

    print("before scribbling_or_overwriting_areas function call")
    scribbling_or_overwriting_areas = detect_scribbling_or_overwriting(original_path)
    print("after scribbling_or_overwriting_areas function call")
    if scribbling_or_overwriting_areas:
        forgery_areas.extend(scribbling_or_overwriting_areas)
        forgery_types.append("Scribbling-Overwriting")

    print("before whitener_areas forgery function call")
    whitener_areas = detect_whitener_forgery(original_path)
    print("after whitener_areas forgery function call")
    if whitener_areas:
        forgery_areas.extend(whitener_areas)
        forgery_types.append("Whitener Forgery")

    print("before manipulation_areas forgery function call")
    manipulation_areas = detect_data_manipulation_forgery(original_path)
    print("after manipulation_areas forgery function call")
    if manipulation_areas:
        forgery_areas.extend(manipulation_areas)
        forgery_types.append("Data Manipulation")

    # print("before digital forgery function call")
    # digital_forgery_areas = detect_digital_forgery(original_path)
    # print("after digital forgery function call")
    # if digital_forgery_areas:
    #     forgery_areas.extend(digital_forgery_areas)
    #     forgery_types.append("Digital Forgery")

    if forgery_areas:
        image = cv2.imread(original_path)
        target_width = 640
        target_height = 480
        image = cv2.resize(image, (target_width, target_height))

        for (x1, y1, x2, y2), _ in forgery_areas:
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
        unique_filename = str(int(time.time())) + '_' + str(uuid.uuid4()) + '.jpg'
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        marked_image_path = os.path.join(app.config['IMAGES_FOLDER'], unique_filename)
        pil_image.save(marked_image_path, format='PNG')
        return marked_image_path, ", ".join(forgery_types)

    return original_path, "No Forgery Detected"


# Route for file upload
# Route for file upload
@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file:
            filename = secure_filename(file.filename)
            uploaded_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(uploaded_image_path)
            marked_image_path, forgery_type = detect_and_mark_forgery(uploaded_image_path)

            if forgery_type != "No Forgery Detected":
                response = {
                    'message': 'Forgery detected successfully',
                    'forgery_image_path': marked_image_path,
                    'forgery_type': forgery_type
                }
            else:
                response = {
                    'message': 'No forgery detected',
                    'forgery_type': forgery_type
                }
            return jsonify(response)
    except Exception as e:
        # Log the detailed error message
        app.logger.error("An error occurred: %s", str(e))
        return jsonify({'error': 'Internal Server Error'}), 500


# Route to serve uploaded images
@app.route('/images/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['IMAGES_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
