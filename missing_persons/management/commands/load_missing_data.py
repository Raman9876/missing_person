# --- Start Copying Here ---
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
import os

# --- IMPORTANT ---
# Make sure 'missing_persons' is the correct name of your Django app
# where the MissingPerson model is defined (the folder containing models.py).
# If your app folder has a different name, change it below.
from frontend.models import MissingPerson
# --- End Important ---

class Command(BaseCommand):
    help = 'Loads missing persons data from JSON file into the database'

    def handle(self, *args, **options):
        # --- Configuration ---
        # Assumes the JSON file is in the project root directory (same level as manage.py)
        json_filename = "missing_persons_dataset.json"
        json_file_path = os.path.join(settings.BASE_DIR, json_filename)
        # --- End Configuration ---

        # Check if the JSON file exists
        if not os.path.exists(json_file_path):
            self.stdout.write(self.style.ERROR(f"❌ Error: JSON file not found at {json_file_path}"))
            self.stdout.write(self.style.ERROR(f"   Please ensure '{json_filename}' is in the same directory as manage.py."))
            return # Stop execution if file not found

        self.stdout.write(f"Attempting to load data from: {json_file_path}")

        # Read the JSON data
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f: # Added encoding='utf-8' for safety
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: Invalid JSON format in {json_filename}: {e}"))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error reading JSON file: {e}"))
            return

        if not isinstance(data, list):
             self.stdout.write(self.style.ERROR(f"❌ Error: Expected JSON file to contain a list of objects, but got {type(data)}."))
             return

        # Counters for reporting
        loaded_count = 0
        skipped_count = 0
        error_count = 0
        updated_count = 0

        self.stdout.write(f"Found {len(data)} entries in the JSON file. Processing...")

        # Loop through each entry in the JSON data
        for index, entry in enumerate(data):
            if not isinstance(entry, dict):
                 self.stdout.write(self.style.WARNING(f"⚠️ Warning: Skipping item at index {index} because it's not a dictionary: {entry}"))
                 skipped_count += 1
                 continue

            try:
                # --- Data Validation and Preparation ---
                name = entry.get('name')
                photo_path = entry.get('photo')

                # Basic check: Skip if essential data like name or photo path is missing
                if not name:
                    self.stdout.write(self.style.WARNING(f"⚠️ Warning: Skipping entry at index {index} due to missing 'name'."))
                    skipped_count += 1
                    continue
                if not photo_path:
                    self.stdout.write(self.style.WARNING(f"⚠️ Warning: Skipping entry '{name}' (index {index}) due to missing 'photo' path."))
                    skipped_count += 1
                    continue

                # Convert date string to datetime object
                date_reported_obj = None
                date_str = entry.get('date_reported')
                if date_str:
                    try:
                        # Adjust the format '%Y-%m-%d %H:%M:%S' if your generate_dataset.py script uses a different one
                        date_reported_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        self.stdout.write(self.style.WARNING(f"⚠️ Warning: Could not parse date '{date_str}' for '{name}'. Setting date_reported to None."))
                # --- End Data Validation ---

                # --- Database Operation ---
                # Try to find an existing record or create a new one.
                # Using 'name' as the primary lookup key here. BE CAREFUL: Names might not be unique.
                # If duplicates are possible, consider a different unique identifier or allow duplicates.
                person, created = MissingPerson.objects.update_or_create(
                    name=name, # Using name to check for existing records
                    defaults={ # Values to set for NEW records or to UPDATE existing ones
                        'age': entry.get('age'),
                        'last_seen_location': entry.get('last_seen_location'),
                        'photo': photo_path, # Store the relative path string
                        'date_reported': date_reported_obj,
                        'latitude': entry.get('latitude'),
                        'longitude': entry.get('longitude'),
                        'parent_email': entry.get('parent_email'),
                        'parent_phone': entry.get('parent_phone'),
                        'additional_audio': entry.get('additional_audio'),
                        # 'face_encoding' will remain None; it's handled by update_encodings command
                    }
                )
                # --- End Database Operation ---

                # Update counters based on whether it was created or updated
                if created:
                    loaded_count += 1
                else:
                    updated_count += 1
                    # Optional: Print a notice if a record was updated instead of created
                    # self.stdout.write(self.style.NOTICE(f"ℹ️ Updated existing entry for: {name}"))

            except Exception as e:
                # Catch any other errors during processing this specific entry
                self.stdout.write(self.style.ERROR(f"❌ Error processing entry for '{entry.get('name', 'UNKNOWN NAME')}' (index {index}): {e}"))
                error_count += 1

            # Optional: Print progress periodically
            if (index + 1) % 100 == 0:
                 self.stdout.write(f"   ... processed {index + 1}/{len(data)} entries ...")


        # --- Final Report ---
        self.stdout.write("-" * 30)
        self.stdout.write(self.style.SUCCESS(f"✅ Finished loading data."))
        self.stdout.write(f"   New records created: {loaded_count}")
        self.stdout.write(f"   Existing records updated: {updated_count}")
        self.stdout.write(f"   Entries skipped: {skipped_count}")
        self.stdout.write(f"   Errors encountered: {error_count}")
        self.stdout.write("-" * 30)
# --- End Code Block ---