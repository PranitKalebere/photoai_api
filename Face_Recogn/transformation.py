from facenet_pytorch import InceptionResnetV1
from torchvision import transforms
import torch
from PIL import Image
import numpy as np

facenet_model = InceptionResnetV1(pretrained='vggface2').eval()

transform = transforms.Compose([
    transforms.Resize((160, 160)),
    transforms.ToTensor(),
    transforms.Normalize([0.5], [0.5]) ])

def get_embedding(cropped_face_np):
    cropped_face_pil = Image.fromarray(cropped_face_np)

    face_tensor = transform(cropped_face_pil)
    face_tensor = face_tensor.unsqueeze(0)

    with torch.no_grad():
        embedding = facenet_model(face_tensor)

    return embedding.squeeze(0)