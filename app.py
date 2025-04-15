from flask import Flask, render_template, request, redirect, url_for, jsonify
# import os
from Face_Recogn.face_ide import image_classification
from flask_cors import CORS 

from Face_Recogn.database import S3_file_Upload,MongoDb_
import os
from werkzeug.utils import secure_filename
# Now you can access them
aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
bucket_name = os.getenv("AWS_S3_BUCKET")
MongoDb_URL = os.getenv("MONGO_URL")

# Create the object
uploader = S3_file_Upload(
    bucket_name=bucket_name,
    aws_access_key=aws_access_key,
    aws_secret_key=aws_secret_key,
    region_name='ap-south-1')

mongodb = MongoDb_(
    MongoDb_URL,
    database="photo_ai_project",
    event_collection="events",
    persons_collection="persons"
)
app = Flask("Wedding Photos")

CORS(app, origins="*")

# Set the upload folder and allowed file extensions
UPLOAD_FOLDER = 'uploads/photos/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Check if file is allowed based on extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/api/list-events",methods=["GET"])
def list_events():
    all_main_events = mongodb.list_main_event()

    return jsonify({"events":all_main_events})

@app.route('/api/create-event', methods=['POST'])
def create_event():
    data = request.get_json()
    event_name = data.get('eventName')

    if not event_name:
        return jsonify({'error': 'Event name is required'}), 400

    print(f"Received event: {event_name}")
    mongodb.save_event(event_name)
    return jsonify({'message': f'Event {event_name} created successfully!'}), 200

@app.route('/api/get-event-details/<event_name>', methods=['GET'])
def get_event_details(event_name):
    sub_events = mongodb.get_sub_events(event_name)
    event = {
        'subEvents': sub_events
    }
    return jsonify(event)

@app.route('/api/upload-photos', methods=['POST'])
def upload_photos():
    if 'photos' not in request.files:
        return jsonify({'message': 'No file part'}), 400

    files = request.files.getlist('photos')
    
    # Ensure the sub-event name is present in the request
    event_name = request.form.get('eventName')
    sub_event_name = request.form.get('subEventName')
    image_classification(files)
    print(event_name,sub_event_name)
    urls = uploader.upload_image(event_name,sub_event_name,files)
    return jsonify({
        "urls":urls
    })
@app.route('/api/get-photos/<event_name>/<sub_event_name>', methods=['GET'])
def get_photos(event_name, sub_event_name):
    try:

        photos = uploader.list_images(event_name,sub_event_name)
        return jsonify({"photos": photos}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/create-sub-event', methods=['POST'])
def create_sub_event():
    data = request.json
    event_name = data.get('eventName')
    sub_event_name = data.get('subEventName')
    mongodb.add_sub_event(event_name,sub_event_name)

    # Save sub_event_name under event_name logic here...
    # Example: Update DB or file.

    return jsonify({'message': 'Sub Event Created Successfully'}), 200

if __name__ == "__main__":
    app.run(debug=True)


if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
