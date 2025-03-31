# ocr_utils.py
from google.cloud import vision

def extract_text_from_image(image_file) -> str:
    client = vision.ImageAnnotatorClient()
    content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    return texts[0].description if texts else ""
