# --- Start Copying Here ---
import random
import json
from datetime import datetime, timedelta
from faker import Faker
import os
import shutil  # For copying files
from pathlib import Path  # For easier path handling

# --- 1. Configuration ---
# *** IMPORTANT: YOU MUST CHANGE THESE PATHS! ***

# --- 1a. SET THIS: Path to the folder containing your folders of images ---
#       (e.g., the folder that has "Person_A", "Person_B" inside it)
#       Use FULL paths. Examples:
#       Windows: "C:/Users/YourUser/Desktop/MissingPersonsImages" (Use forward slashes!)
#       Linux/Mac: "/home/user/data/missing_images"
SOURCE_IMAGE_BASE_DIR = "C:/Users/Ramanpreet Kaur/Downloads/archive/lfw-deepfunneled/lfw-deepfunneled"

# --- 1b. SET THIS: Path to your Django project's MEDIA folder ---
#       (Should match MEDIA_ROOT in your settings.py if defined, otherwise the full path)
#       Use FULL paths. Examples:
#       Windows: "C:/Users/YourUser/projects/AI_MISSING_P/media"
#       Linux/Mac: "/home/user/projects/AI_MISSING_P/media"
DJANGO_MEDIA_ROOT = "D:/Ai_missing_person_project/missing_persons/media"

# --- How many fake entries to create? ---
#     (Make sure this isn't vastly more than the number of unique images you have,
#      otherwise images will be reused many times)
NUM_ENTRIES_TO_GENERATE = 1000  # Adjust as needed

# --- Optional: Use a specific language/region for Faker data ---
FAKER_LOCALE = 'en_IN'  # Keep or change as needed ('en_US', etc.)

# --- End Configuration ---


# --- 2. Setup Paths and Folders ---
# Calculate the destination path for missing person images inside the media folder
DESTINATION_MISSING_PERSONS_DIR = Path(DJANGO_MEDIA_ROOT) / "missing_persons"
# Calculate the destination path for audio files (if you handle them later)
# DESTINATION_AUDIO_DIR = Path(DJANGO_MEDIA_ROOT) / "additional_audio"

# Create the destination folders inside your media directory if they don't exist
print(f"Ensuring destination folder exists: {DESTINATION_MISSING_PERSONS_DIR}")
os.makedirs(DESTINATION_MISSING_PERSONS_DIR, exist_ok=True)
# os.makedirs(DESTINATION_AUDIO_DIR, exist_ok=True) # Uncomment if handling audio

# --- 3. Find Your Source Images ---
valid_image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
person_image_map = {}  # Dictionary: {folder_path: [list_of_image_paths]}
all_image_paths = [] # Flat list of all valid images found

source_base_path = Path(SOURCE_IMAGE_BASE_DIR)
if not source_base_path.is_dir():
    print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(f"!!! ERROR: Source image directory NOT FOUND:")
    print(f"!!!   '{SOURCE_IMAGE_BASE_DIR}'")
    print(f"!!! Please check the path in the script configuration.")
    print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    exit()

print(f"Scanning for images in: {SOURCE_IMAGE_BASE_DIR}")
person_folders = [d for d in source_base_path.iterdir() if d.is_dir()]

if not person_folders:
    print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(f"!!! ERROR: No person-specific subfolders found directly inside:")
    print(f"!!!   '{SOURCE_IMAGE_BASE_DIR}'")
    print(f"!!! Make sure it contains folders like 'Person_A', 'Person_B', etc.")
    print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    exit()

for person_folder in person_folders:
    images_in_folder = []
    for item in person_folder.iterdir():
        if item.is_file() and item.suffix.lower() in valid_image_extensions:
            images_in_folder.append(item)
            all_image_paths.append(item) # Add to the flat list too
    if images_in_folder:
        person_image_map[str(person_folder)] = images_in_folder
    else:
        print(f"Warning: No valid images found in folder: {person_folder.name}")

if not all_image_paths: # Check the flat list
    print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(f"!!! ERROR: No usable images found in any subfolders of:")
    print(f"!!!   '{SOURCE_IMAGE_BASE_DIR}'")
    print(f"!!! Check image file types (jpg, png, etc.)")
    print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    exit()

print(f"Found images in {len(person_image_map)} person folders. Total images: {len(all_image_paths)}")


# --- 4. Generate Fake Data and Link Images ---
fake = Faker(FAKER_LOCALE)
dataset = []
copied_files_count = 0

print(f"Generating {NUM_ENTRIES_TO_GENERATE} data entries...")

for i in range(NUM_ENTRIES_TO_GENERATE):
    # --- Generate standard fake data ---
    name = fake.name()
    age = random.randint(3, 85)
    last_seen_location = fake.city() + ", " + fake.state()
    latitude = round(random.uniform(8.0, 37.0), 6)
    longitude = round(random.uniform(68.0, 97.0), 6)
    parent_email = fake.email()
    parent_phone = "+91" + str(random.randint(6000000000, 9999999999))
    date_reported = fake.date_time_between(start_date='-2y', end_date='now').strftime('%Y-%m-%d %H:%M:%S')

    # --- Select, Copy, and Path for Real Image ---
    photo_db_path = None  # Default to None

    if all_image_paths:
        # Select a random image from ALL available images
        # Using modulo ensures we cycle through if num_entries > num_images
        source_image_path_obj = all_image_paths[i % len(all_image_paths)]
        source_filename = source_image_path_obj.name # e.g., "img_01.jpg"

        # Define destination path inside 'media/missing_persons/'
        destination_image_path_obj = DESTINATION_MISSING_PERSONS_DIR / source_filename

        # --- Action: Copy the file ---
        try:
            # Only copy if it doesn't already exist in the destination
            if not destination_image_path_obj.exists():
                shutil.copy2(source_image_path_obj, destination_image_path_obj)
                copied_files_count += 1

            # Set the relative path for the database record
            photo_db_path = f"missing_persons/{source_filename}"

        except Exception as e:
            print(f"!!! ERROR copying file !!!")
            print(f"  From: {source_image_path_obj}")
            print(f"  To:   {destination_image_path_obj}")
            print(f"  Error: {e}")
            photo_db_path = None # Reset to None if copy failed
    else:
        print("!!! CRITICAL ERROR: No images available to select from, though scan seemed okay.")
        # This case should ideally not be reached due to earlier checks


    # --- Placeholder for Audio (Remains placeholder for now) ---
    # You would need a similar process if you have real audio files
    audio_placeholder_filename = f"placeholder_audio_{i+1}.mp3"
    audio_db_path = f"additional_audio/{audio_placeholder_filename}"

    # --- Assemble the final data record ---
    dataset.append({
        "name": name,
        "age": age,
        "last_seen_location": last_seen_location,
        "photo": photo_db_path, # Use the path to the COPIED real image, or None if copy failed
        "date_reported": date_reported,
        "latitude": latitude,
        "longitude": longitude,
        "parent_email": parent_email,
        "parent_phone": parent_phone,
        "additional_audio": audio_db_path, # Still using placeholder audio path
        "face_encoding": None  # Still None - generated later by Django/separate script
    })

    # --- Show progress ---
    if (i + 1) % 100 == 0 or (i + 1) == NUM_ENTRIES_TO_GENERATE:
        print(f"  Generated {i+1}/{NUM_ENTRIES_TO_GENERATE} entries...")


# --- 5. Save the Generated Data ---
output_filename = "missing_persons_dataset.json" # Keep the same output filename

print("-" * 30)
print(f"Saving generated data to: {output_filename}")
try:
    # Save the generated data list to the JSON file
    with open(output_filename, 'w') as f:
        json.dump(dataset, f, indent=4)
    print(f"Successfully saved data.")
except Exception as e:
    print(f"!!! ERROR saving JSON file: {e} !!!")


print("-" * 30)
print(f"Finished generating {len(dataset)} data entries.")
print(f"Copied {copied_files_count} new image files to '{DESTINATION_MISSING_PERSONS_DIR}'")
print("-" * 30)
print("NEXT STEPS:")
print("1. Check the output file:", output_filename)
print("   (Verify 'photo' fields point to 'missing_persons/your_real_image.jpg')")
print("2. Check your Django media folder:", DESTINATION_MISSING_PERSONS_DIR)
print("   (Verify your real images have been copied there)")
print("3. Import the data from", output_filename, "into your Django database.")
print("   (Using the 'load_missing_data' management command from the previous step)")
print("4. Generate face encodings using the 'update_encodings' management command.")
print("-" * 30)

# --- End of Script ---