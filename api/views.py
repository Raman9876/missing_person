from django.shortcuts import render
# Create your views here.
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
import face_recognition
import cv2
import numpy as np
import os
from django.core.files.storage import default_storage
from django.http import JsonResponse
from rest_framework.decorators import api_view

@api_view(['POST'])
def search_missing_person(request):
    if 'file' not in request.FILES:
        return JsonResponse({"error": "No file uploaded"}, status=400)

    uploaded_file = request.FILES['file']
    file_path = default_storage.save(f"uploads/{uploaded_file.name}", uploaded_file)

    # Load known faces from a database or a folder
    known_faces_dir = "media/known_faces"
    known_encodings = []
    known_names = []

    for filename in os.listdir(known_faces_dir):
        known_image = face_recognition.load_image_file(os.path.join(known_faces_dir, filename))
        encodings = face_recognition.face_encodings(known_image)
        if encodings:
            known_encodings.append(encodings[0])
            known_names.append(filename.split('.')[0])

    # Load the uploaded image and encode it
    unknown_image = face_recognition.load_image_file(file_path)
    unknown_encodings = face_recognition.face_encodings(unknown_image)

    if not unknown_encodings:
        return JsonResponse({"error": "No face detected in the uploaded image"}, status=400)

    unknown_encoding = unknown_encodings[0]

    # Compare the uploaded image with known faces
    matches = face_recognition.compare_faces(known_encodings, unknown_encoding)
    name = "No Match Found"

    if True in matches:
        match_index = matches.index(True)
        name = known_names[match_index]

    return JsonResponse({"result": name})


def home(request):
    return JsonResponse({"message": "Welcome to Missing Persons API"})

