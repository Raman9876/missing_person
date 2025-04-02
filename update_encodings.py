import json
import os
import face_recognition
import numpy as np
from django.conf import settings

if not settings.configured:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "missing_persons.settings") # Replace with your project name
    import django
    django.setup()

def update_dataset_with_encodings(dataset_path, image_directory):
    with open(dataset_path, 'r') as f:
        dataset = json.load(f)

    updated_dataset = []
    for entry in dataset:
        image_filename = entry["photo"].split('/')[-1]
        image_path = os.path.join(image_directory, image_filename)
        try:
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                entry["face_encoding"] = json.dumps(encodings[0].tolist())
            else:
                print(f"No face found in {image_path}")
        except FileNotFoundError:
            print(f"Image not found: {image_path}")
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
        updated_dataset.append(entry)

    with open(dataset_path, 'w') as f:
        json.dump(updated_dataset, f, indent=4)

    print(f"Updated {dataset_path} with face encodings (where found).")

if __name__ == "__main__":
    dataset_file = "missing_persons_dataset.json"
    image_dir = os.path.join(settings.MEDIA_ROOT, "missing_persons") # Adjust if your image directory is different
    update_dataset_with_encodings(dataset_file, image_dir)