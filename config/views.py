from django.shortcuts import render
from django.core.serializers import serialize
import json
from frontend.models import MissingPerson

def feed(request):
    missing_persons = MissingPerson.objects.values("name", "latitude", "longitude")
    
    # Convert QuerySet to JSON
    missing_persons_json = json.dumps(list(missing_persons))

    return render(request, "feed.html", {"missing_persons_json": missing_persons_json})
