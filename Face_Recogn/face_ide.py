import pickle
from scipy.spatial.distance import cosine
from dotenv import load_dotenv
import os
from utils.constant import known_faces_file_path,mapping_file_path
from Face_Recogn.transformation import get_embedding
import cv2
from mtcnn.mtcnn import MTCNN
detector = MTCNN()
import tempfile
import shutil
load_dotenv()
from Face_Recogn.database import MongoDb_,S3_file_Upload

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

MongoDb = MongoDb_(
    MongoDb_URL,
    database="photo_ai_project",
    event_collection="events",
    persons_collection="persons"
)
# # Upload a file into a folder (e.g., 'temp-folder/')
# uploaded_url = uploader.upload_file('path/to/your/file.jpg', 'temp-folder')

# print(uploaded_url)

if os.path.exists(known_faces_file_path) and os.path.getsize(known_faces_file_path) > 0:
    try:
        with open(known_faces_file_path, "rb") as f:
            known_embeddings, unique_id_counter = pickle.load(f)
    except Exception as e:
        print(f"Error loading embeddings: {e}")
        known_embeddings = []
        unique_id_counter = 0
else:
    known_embeddings = []
    unique_id_counter = 0



image_person_mapping = {}

def is_match(known_embeddings, new_embedding, threshold=0.4):
    for emb, uid, _ in known_embeddings:
        if cosine(emb, new_embedding) < threshold:
            return uid
    return None


def image_classification(file_paths,event_name,sub_event_name):
    image_person_mapping = {}
    global known_embeddings, unique_id_counter

    try:
        for file_path in file_paths:
            image = cv2.cvtColor(cv2.imread(file_path), cv2.COLOR_BGR2RGB)
            res = detector.detect_faces(image)
            persons_in_image = []

            for face in res:
                if face['confidence'] > 0.97:
                    x, y, w, h = face['box']
                    cropped_face = image[y:y+h, x:x+w]
                    uploader.upload_image(event_name,sub_event_name,cropped_face,cropped=True)

                    embedding = get_embedding(cropped_face)
                    embedding = embedding.detach().numpy()

                    uid = is_match(known_embeddings, embedding)
                    if uid is None:
                        uid = unique_id_counter
                        unique_id_counter += 1
                        known_embeddings.append((embedding, uid, cropped_face))

                    persons_in_image.append(uid)

            image_person_mapping[file_path] = persons_in_image

    except Exception as e:
        print("Error during image classification:", e)

    # Save updated embeddings and mapping
    with open(known_faces_file_path, "wb") as f:
        pickle.dump((known_embeddings, unique_id_counter), f)

    MongoDb.image_info(image_person_mapping)

print("complete")


