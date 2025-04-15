import requests

# URL of the Flask API
url = 'http://localhost:5000/api/get_image'

# Path to the image you want to upload
image_path = r'myimg.jpg'


# Open the image file in binary mode
with open(image_path, 'rb') as img:
    files = {'image': img}
    response = requests.post(url, files=files)

# Print the response
print(response.status_code)
print(response.json())
