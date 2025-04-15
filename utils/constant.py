import os 

artifacts_folder = "artifacts"

if not os.path.exists(artifacts_folder):
    os.mkdir(artifacts_folder)

known_faces_file = "known_faces.pkl"
# input_folder = "/content/drive/MyDrive/test_images"
mapping_file = "image_person_mapping.pkl"

known_faces_file_path = os.path.join(artifacts_folder,known_faces_file)
mapping_file_path = os.path.join(artifacts_folder,mapping_file)


if __name__=="__main__":
    print("created_successfully")

