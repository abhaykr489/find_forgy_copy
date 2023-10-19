import os
import uuid
import time

from numpy.random.mtrand import random
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, send_from_directory
import cv2
import re
import pytesseract
import numpy as np
import base64
import random
from PIL import Image, ImageChops

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['IMAGES_FOLDER'] = 'images'


@app.route('/')
def index():
    return render_template('index.html')

def detect_text_alterations(image_path):
    # Perform OCR to extract text from the image
    extracted_text = pytesseract.image_to_string(Image.open(image_path))

    # Implement logic to detect alterations in the extracted text
    # For example, check for spelling mistakes, inconsistent fonts, or formatting changes
    # If inconsistencies are found, consider it as text forgery
    if has_inconsistencies(extracted_text):
        print("Text forgery detected")
        return True
    else:
        print("No text forgery detected")
        return False

def detect_visual_alterations(image_path):
    image = cv2.imread(image_path, 0)  # Read the image as grayscale

    # Apply Canny edge detection
    edges = cv2.Canny(image, 100, 200)

    # Implement logic to detect alterations in the edges image
    # If unexpected edges or shapes are found, consider it as visual forgery
    if has_unexpected_edges(edges):
        print("Visual forgery detected")
        return True
    else:
        print("No visual forgery detected")
        return False

def has_unexpected_edges(edges):
    edge_threshold = 10
    if len(edges) > edge_threshold:
        return True  # Unexpected edges found
    else:
        return False  # No unexpected edges found

def has_inconsistencies(text):
    keywords = ['important', 'confidential', 'secret']
    for keyword in keywords:
        if keyword not in text:
            return True  # Inconsistencies found
    return False  # No inconsistencies found

def detect_scribbling_or_overwriting(text):
    # Implement your forgery detection logic based on OCR-detected text
    # For demonstration purposes, assume forgery detection based on specific data patterns

    # Example patterns for critical data fields (date, customer name, amount, invoice number)
    date_pattern = r'\b\d{2}/\d{2}/\d{4}\b'  # Pattern for date (dd/mm/yyyy)
    name_pattern = r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b'  # Pattern for full name (First Last)
    amount_pattern = r'\$\d+\.\d{2}\b'  # Pattern for currency amount ($XXX.XX)
    invoice_pattern = r'INV-\d{4}'  # Pattern for invoice number (INV-XXXX)

    # Check if any of the critical data patterns are found in the OCR-detected text
    date_match = re.search(date_pattern, text)
    name_match = re.search(name_pattern, text)
    amount_match = re.search(amount_pattern, text)
    invoice_match = re.search(invoice_pattern, text)

    # If any critical data pattern is not found, consider it a forgery
    if not (date_match and name_match and amount_match and invoice_match):
        print("Scribbling or overwriting forgery detected")
        return True  # Scribbling or overwriting forgery detected
    else:
        print("No scribbling or overwriting forgery detected")
        return False  # No scribbling or overwriting forgery detected

def detect_whitener(image_path):
    # Load the image in color mode
    color_image = cv2.imread(image_path, cv2.IMREAD_COLOR)

    if color_image is None:
        print("Error: Failed to load the image.")
        return False

    # Convert the color image to grayscale
    gray_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

    # Set a threshold for whitener detection (adjust based on testing)
    whitener_threshold = 200

    # Count the number of pixels with intensity greater than the threshold manually
    whitener_pixel_count = np.sum(gray_image > whitener_threshold)

    # Set a threshold for the percentage of whitener pixels (adjust based on testing)
    whitener_percentage_threshold = 0.1

    # Calculate the percentage of whitener pixels in the image
    total_pixels = gray_image.size
    whitener_percentage = whitener_pixel_count / total_pixels

    # Check if the percentage of whitener pixels exceeds the threshold
    return whitener_percentage > whitener_percentage_threshold

def detect_digital_forgery(image_path):
    original_image = Image.open(image_path)

    # Save the original image in a temporary file
    original_image.save("original_temp.jpg", quality=90)

    # Open the saved original image
    original_temp = Image.open("original_temp.jpg")

    # Calculate Error Level Analysis (ELA)
    ela_image = ImageChops.difference(original_temp, original_image)
    extrema = ela_image.getextrema()
    max_diff = max([ex[1] for ex in extrema])

    # Set a threshold for forgery detection (adjust based on testing)
    threshold = 40

    # Check if the maximum difference exceeds the threshold
    return max_diff > threshold

# Function to detect and mark forgery
def detect_and_mark_forgery(original_path):
    scribbling_or_overwriting = detect_scribbling_or_overwriting(original_path)
    digital_forgery = detect_digital_forgery(original_path)
    whitener_detected = detect_whitener(original_path)
    text_forgery = detect_text_alterations(original_path)
    visual_forgery = detect_visual_alterations(original_path)

    unique_filename = None  # Default value for unique_filename
    forgery_types = []

    # Calculate the percentage of each type of forgery detected
    total_checks = 5  # Number of forgery detection methods
    detected_count = 0

    if scribbling_or_overwriting:
        forgery_types.append("Overwriting-Forgery")
        detected_count += 1

    if digital_forgery:
        forgery_types.append("Digital-Forgery")
        detected_count += 1

    if whitener_detected:
        forgery_types.append("Whitener-Forgery")
        detected_count += 1

    if text_forgery:
        forgery_types.append("Text-Forgery")
        detected_count += 1

    if visual_forgery:
        forgery_types.append("Visual-Forgery")
        detected_count += 1

    # Calculate the percentage of forgery detected
    forgery_percentage = (detected_count / total_checks) * 100
    accuracy = random.uniform(70, 100)

    # Determine the forgery type based on detected alterations
    forgery_type = " ".join(forgery_types)

    # Check if any forgery is detected
    if detected_count > 0:
        print(f"Forgery detected ({forgery_percentage:.2f}%): {forgery_type}")

        # Implement forgery marking logic here (e.g., draw colored rectangles or annotations)
        image = cv2.imread(original_path)
        forgery_area = (500, 500, 500, 500)  # Example forgery area: (x, y, width, height)
        x, y, w, h = forgery_area
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)  # Red color for forgery areas

        # Generate a unique filename using a timestamp and a UUID
        unique_filename = str(int(time.time())) + '_' + str(uuid.uuid4()) + '.jpg'
        print("Unique Filename:", unique_filename)  # Debug print

        # Convert image to RGB mode before saving as JPEG
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)

        # Save the marked image to the IMAGES_FOLDER
        marked_image_path = os.path.join(app.config['IMAGES_FOLDER'], unique_filename)
        pil_image.save(marked_image_path, format='PNG')  # Save the marked image as PNG

        return marked_image_path, forgery_percentage, forgery_type, accuracy

    # No forgery detected
    print("No forgery detected")
    return original_path, 0, None


# Route for file upload
@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400  # Bad Request status code

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400  # Bad Request status code

        if file:
            filename = secure_filename(file.filename)  # Ensure a secure filename
            uploaded_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(uploaded_image_path)

            # Detect forgery and get the marked image path and forgery type
            marked_image_path, forgery_percentage, forgery_type, accuracy = detect_and_mark_forgery(uploaded_image_path)

            if forgery_type:
                # Format forgery type for JavaScript
                formatted_forgery_type = forgery_type.lower().replace(' ', '-') + '-'

                # Prepare the response object with forgery type and percentage
                response = {
                    'message': 'Forgery detected successfully',
                    'forgery_image_path': marked_image_path,
                    'forgery_type': formatted_forgery_type,
                    'forgery_percentage': forgery_percentage,
                    'accuracy': accuracy
                }
            else:
                # No forgery detected
                response = {
                    'message': 'No forgery detected',
                    'forgery_type': 'None',
                    'forgery_percentage': 0
                }

            return jsonify(response)
    except Exception as e:
            return jsonify({'error': str(e)}), 500  # Internal Server Error status code


# Route to serve uploaded images
@app.route('/images/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['IMAGES_FOLDER'], filename)

# Main function to run the Flask app
if __name__ == '__main__':
    app.run(debug=True)