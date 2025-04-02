from django.urls import path
from .views import home, search_missing_person

urlpatterns = [
    path('', home),
    path('search/', search_missing_person, name='search-missing-person'),

]
