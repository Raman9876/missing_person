# File: missing_persons/management/commands/update_encodings.py

import os
import json
import numpy as np
import face_recognition # Make sure this library is installed
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q # For complex lookups

# --- IMPORTANT ---
# Make sure 'missing_persons' is the correct name of your Django app
# where the MissingPerson model is defined (the folder containing models.py).
# If your app folder has a different name, change it below.
from frontend.models import MissingPerson
# --- End Important ---

class Command(BaseCommand):
    help = 'Calculates and updates face encodings for MissingPerson records that do not have one.'

    def handle(self, *args, **options):
        self.stdout.write("Starting face encoding update process...")

        # Select records where face_encoding is NULL or an empty string
        # This avoids reprocessing already encoded images unless forced (add --force option later if needed)
        persons_to_process = MissingPerson.objects.filter(
            Q(face_encoding__isnull=True) | Q(face_encoding__exact='')
        )

        total_persons = persons_to_process.count()
        if total_persons == 0:
            self.stdout.write(self.style.SUCCESS("✅ No missing persons found needing face encoding."))
            return

        self.stdout.write(f"Found {total_persons} records to process.")

        processed_count = 0
        error_count = 0
        skipped_no_photo_path = 0
        skipped_file_not_found = 0
        skipped_no_face_found = 0
        skipped_multi_face_found = 0

        for person in persons_to_process.iterator(): # Use iterator for memory efficiency
            processed_count += 1
            self.stdout.write(f"\nProcessing record {processed_count}/{total_persons}: ID={person.id}, Name={person.name}")

            # 1. Check if photo path exists in the record
            if not person.photo or not person.photo.name:
                self.stdout.write(self.style.WARNING("  ⚠️ Skipping: No photo path associated with this record."))
                skipped_no_photo_path += 1
                continue

            # 2. Construct the full path to the image file
            try:
                # person.photo.path should give the absolute path if MEDIA_ROOT is set correctly
                # If not, construct manually (less robust):
                # full_image_path = os.path.join(settings.MEDIA_ROOT, person.photo.name)
                full_image_path = person.photo.path
            except Exception as e:
                 self.stdout.write(self.style.ERROR(f"  ❌ Error getting full image path for '{person.photo.name}': {e}"))
                 error_count += 1
                 continue


            # 3. Check if the actual image file exists on the filesystem
            if not os.path.exists(full_image_path):
                self.stdout.write(self.style.ERROR(f"  ❌ Skipping: Image file not found at path: {full_image_path}"))
                skipped_file_not_found += 1
                continue

            # 4. Load image and calculate encoding
            try:
                self.stdout.write(f"  Loading image: {full_image_path}")
                image = face_recognition.load_image_file(full_image_path)
                # Find all face encodings in the image
                encodings = face_recognition.face_encodings(image)

                if not encodings:
                    self.stdout.write(self.style.WARNING("  ⚠️ Skipping: No faces found in the image."))
                    skipped_no_face_found += 1
                    continue # Don't save anything if no face found

                if len(encodings) > 1:
                    self.stdout.write(self.style.WARNING(f"  ⚠️ Warning: Multiple ({len(encodings)}) faces found in the image. Using the first one found."))
                    skipped_multi_face_found += 1 # Count as a potential issue

                # Select the first encoding found
                face_encoding_array = encodings[0]

                # Convert numpy array to list, then to JSON string for storage
                face_encoding_json = json.dumps(face_encoding_array.tolist())

                # 5. Save the encoding back to the database
                person.face_encoding = face_encoding_json
                # Save only the updated field to be efficient
                person.save(update_fields=['face_encoding'])
                self.stdout.write(self.style.SUCCESS("  ✅ Successfully updated face encoding."))

            except UnidentifiedImageError: # Catch PIL specific error for corrupt images
                 self.stdout.write(self.style.ERROR(f"  ❌ Error: Could not load image. File might be corrupted: {full_image_path}"))
                 error_count += 1
            except Exception as e:
                # Catch other potential errors during face_recognition processing
                self.stdout.write(self.style.ERROR(f"  ❌ Error processing image or saving encoding for ID {person.id}: {e}"))
                error_count += 1

            # Optional: Add a small delay if needed, e.g., time.sleep(0.1)

        # --- Final Report ---
        self.stdout.write("-" * 30)
        self.stdout.write(self.style.SUCCESS("✅ Face encoding update process finished."))
        self.stdout.write(f"  Total records needing encoding: {total_persons}")
        self.stdout.write(f"  Successfully encoded: {processed_count - error_count - skipped_no_photo_path - skipped_file_not_found - skipped_no_face_found}")
        self.stdout.write(f"  Skipped (No photo path in DB): {skipped_no_photo_path}")
        self.stdout.write(f"  Skipped (Image file not found): {skipped_file_not_found}")
        self.stdout.write(f"  Skipped (No face detected): {skipped_no_face_found}")
        self.stdout.write(f"  Processed with multiple faces (used first): {skipped_multi_face_found}")
        self.stdout.write(f"  Errors during processing: {error_count}")
        self.stdout.write("-" * 30)