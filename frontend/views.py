import json
import time
import os
import face_recognition
import numpy as np
from datetime import datetime, timedelta
from faker import Faker  # For generating realistic fake data
from twilio.rest import Client
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from .models import MissingPerson
from .forms import MissingPersonForm
from django.db.models import Q  # Import for search functionality
from django.http import JsonResponse
from django.core.mail import send_mail
from dotenv import load_dotenv
from twilio.rest import Client
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from twilio.base.exceptions import TwilioRestException


# Load environment variables
load_dotenv()

# Get Twilio credentials from .env file
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

def send_match_notification(matched_person, latitude, longitude):
    """Send SMS and Email notification when a match is found."""

    # --- Add more debugging ---
    print("-" * 20)
    print(f"DEBUG [send_match_notification]: Preparing to notify match for {matched_person.name} (ID: {matched_person.id})")
    print(f"DEBUG [send_match_notification]: Recipient Phone from DB = '{matched_person.parent_phone}'") # Print exactly what's retrieved
    print(f"DEBUG [send_match_notification]: Using From Number = '{TWILIO_PHONE_NUMBER}'") # Verify From number hasn't changed
    print("-" * 20)
    # --- End debugging ---


    if not matched_person.parent_phone:
        print("⚠️ No valid parent phone number provided. Skipping SMS.")
        return

    # Use the phone number directly retrieved for checks and sending
    recipient_phone = matched_person.parent_phone
    from_phone = TWILIO_PHONE_NUMBER # Use the global variable

    if not recipient_phone.startswith("+"):
        print(f"⚠️ Invalid phone format for recipient: {recipient_phone}")
        return

    if not from_phone or not from_phone.startswith("+"):
         print(f"⚠️ Invalid or missing FROM phone number in settings: {from_phone}")
         return # Added check for From number

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    Maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
    message_body = (
        f"✅ Match Found! {matched_person.name} has been identified.\n"
        f"Last seen at: {matched_person.last_seen_location}.\n"
        f"Check the location: {Maps_link}"
    )
    try:
        message = client.messages.create(
            body=message_body,
            from_=from_phone, # Use variable
            to=recipient_phone # Use variable
        )
        print(f"📩 SMS Sent! Message SID: {message.sid} TO: {recipient_phone}") # Log recipient on success too

    except TwilioRestException as e:
        # Print more details from the exception if possible
        print(f"❌ Twilio Error sending TO: {recipient_phone}")
        print(f"  Error Code: {e.code}")
        print(f"  Message: {e.msg}")
        print(f"  Status: {e.status}")
        # print(f"  Full Exception: {e}") # Uncomment for very verbose error

def home(request):
    return render(request, 'frontend/home.html')

def upload_view(request):
    if request.method == 'POST':
        start_time = time.time()  # Start Timer

        form = MissingPersonForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['photo']  # Get uploaded file
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)  # Store temporarily
            temp_filename = fs.save(uploaded_file.name, uploaded_file)
            temp_image_path = os.path.join(settings.MEDIA_ROOT, temp_filename)

            print(f"✅ Temporarily stored image at: {temp_image_path}")

            # ✅ Step 1: Check if the image matches an existing one
            matched_person = check_face_match(temp_image_path)

            if matched_person:
                # No need to send notification here anymore, it's done in check_face_match
                print(f"🔍 Match found with: {matched_person.name}")
                return render(request, 'frontend/match_results.html', {'matched_person': matched_person})

            # ✅ Step 2: No match found → Save data
            person = form.save(commit=False)
            person.additional_audio = request.FILES.get('additional_audio')  # Get additional audio file
            person.latitude = request.POST.get('latitude')
            person.longitude = request.POST.get('longitude')
            person.photo = temp_filename  # Save the file reference
            person.save()

            print(f"✅ No match found. New data saved as: {person.name}")

            # ✅ Step 3: Send email notification (if applicable)
            if person.parent_email:
                send_mail(
                    subject="🚨 New Missing Person Reported",
                    message=f"A new missing person has been reported: {person.name}, last seen at {person.last_seen_location}.",
                    from_email="your_email@example.com",
                    recipient_list=[person.parent_email],
                )

            print(f"✅ Upload & Save Completed in {time.time() - start_time:.2f} seconds")
            return redirect('feed')  # Redirect to feed if no match is found

    else:
        form = MissingPersonForm()

    return render(request, 'frontend/upload.html', {'form': form})
def feed_view(request):
    query = request.GET.get('q', '')  # Get search term
    missing_persons = MissingPerson.objects.all()

    if query:
        missing_persons = missing_persons.filter(
            Q(name__icontains=query) | Q(last_seen_location__icontains=query)
        )

        # ✅ If a match is found, send an email to the parent/guardian
        for person in missing_persons:
            if person.parent_email:
                send_mail(
                    subject="✅ Possible Match for Your Missing Person",
                    message=f"Hello,\n\nA person matching {person.name} has been reported in {person.last_seen_location}.\n"
                            f"You can check details at: http://yourwebsite.com/feed/\n\nBest Regards,\nMissing Persons Team",
                    from_email="rkrk09134@gmail.com",  # Replace with your email
                    recipient_list=[person.parent_email],  # Send email to parent
                )

    # Convert queryset to JSON for map display
    missing_persons_json = json.dumps([
        {
            "name": person.name,
            "latitude": person.latitude,
            "longitude": person.longitude,
            "last_seen_location": person.last_seen_location,
            "photo_url": person.photo.url if person.photo else "",
        } for person in missing_persons
    ])

    return render(request, 'frontend/feed.html', {
        'missing_persons': missing_persons,
        'query': query,
        'missing_persons_json': missing_persons_json
    })
def upload(request):
    return render(request, 'upload.html')

def upload_face_match(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)
        uploaded_image_path = fs.path(filename)

        # Call face matching function
        match_name = check_face_match(uploaded_image_path)

        if match_name:
            matched_person = MissingPerson.objects.filter(name=match_name).first()
            return render(request, 'frontend/match_results.html', {'matched_person': matched_person})

    return render(request, 'frontend/upload_face.html', {'error': 'No match found'})


@csrf_exempt  # Remove this if using CSRF protection
def update_location(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))  # Safe JSON parsing
            latitude = data.get('latitude')
            longitude = data.get('longitude')

            if not latitude or not longitude:
                return JsonResponse({'error': 'Missing latitude or longitude'}, status=400)

            # Ensure user exists in MissingPerson
            person = MissingPerson.objects.filter(id=request.POST.get("person_id")).first()
            if not person:
                return JsonResponse({'error': 'User not associated with any missing person'}, status=404)

            # Update location
            person.latitude = latitude
            person.longitude = longitude
            person.save()

            return JsonResponse({'status': 'success', 'latitude': latitude, 'longitude': longitude})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


def check_face_match(uploaded_image_path):
    """Matches the uploaded image with existing missing persons & sends notifications and deletes matched record."""
    missing_people = MissingPerson.objects.exclude(face_encoding="")  # Only check encoded images

    uploaded_image = face_recognition.load_image_file(uploaded_image_path)
    uploaded_encodings = face_recognition.face_encodings(uploaded_image)

    if not uploaded_encodings:
        return None  # No face detected

    uploaded_encoding = uploaded_encodings[0]

    known_encodings = []
    known_persons = []

    for person in missing_people:
        encoding = person.get_face_encoding()
        if encoding is not None:
            known_encodings.append(encoding)
            known_persons.append(person)

    if known_encodings:
        distances = face_recognition.face_distance(known_encodings, uploaded_encoding)
        best_match_index = np.argmin(distances)

        if distances[best_match_index] < 0.5:  # Match found!
            matched_person = known_persons[best_match_index]

            # ✅ Send notifications
            send_match_notification(matched_person, matched_person.latitude, matched_person.longitude)

            # ✅ Delete the matched person's image file
            if matched_person.photo:
                if os.path.exists(os.path.join(settings.MEDIA_ROOT, matched_person.photo.name)):
                    os.remove(os.path.join(settings.MEDIA_ROOT, matched_person.photo.name))

            # ✅ Delete the matched person's record from the database
            matched_person.delete()
            print(f"🗑️ Deleted matched person: {matched_person.name} from the database.")

            return matched_person  # Return matched person

    return None  # No match found