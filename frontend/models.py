from django.db import models
from django.conf import settings  # ✅ Import settings here
import face_recognition
import numpy as np
import os 
import json

class MissingPerson(models.Model):
    name = models.CharField(max_length=255)
    age = models.IntegerField()
    last_seen_location = models.CharField(max_length=500)
    photo = models.ImageField(upload_to="missing_persons/")
    date_reported = models.DateTimeField(auto_now_add=True)
    latitude = models.FloatField(null=True, blank=True)  # New field
    longitude = models.FloatField(null=True, blank=True)  # New field
    parent_email = models.EmailField(null=True, blank=True)  # Allow blank values temporarily
    face_encoding = models.TextField(null=True, blank=True)  # Add this field
    parent_phone = models.CharField(max_length=15, blank=True, null=True) # Add this field
    additional_audio = models.FileField(upload_to='additional_audio/', null=True, blank=True) # New field
    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)  # Save the instance first
    #     if not os.path.exists(self.photo.path):
    #         raise FileNotFoundError(f"File not found: {self.photo.path}")

    #     image = face_recognition.load_image_file(self.photo.path)
    #     encodings = face_recognition.face_encodings(image)
    #     if encodings:
    #         self.face_encoding = np.array(encodings[0]).tolist()  # Convert to list
    #         super().save(*args, **kwargs)  # Save again with encoding
    def save(self, *args, **kwargs):
        """Precompute and store face encodings when saving an image."""
        super().save(*args, **kwargs)  # Save the image first

        if self.photo:  # ✅ Check if an image is uploaded
            image_path = os.path.join(settings.MEDIA_ROOT, str(self.photo))
            try:
                image = face_recognition.load_image_file(image_path)
                encoding = face_recognition.face_encodings(image)

                if encoding:  
                    self.face_encoding = json.dumps(encoding[0].tolist())  # ✅ Store as JSON
                    super().save(update_fields=["face_encoding"])  # ✅ Save only encoding field
            except Exception as e:
                print(f"❌ Error encoding face: {e}")  # Handle errors
    def get_face_encoding(self):
        """✅ Fix: Retrieve face encoding as a NumPy array"""
        if self.face_encoding:
            return np.array(json.loads(self.face_encoding))  # Convert back to NumPy array
        return None
    def __str__(self):
        return self.name
