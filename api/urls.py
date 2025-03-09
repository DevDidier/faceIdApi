from django.urls import include, path
from api.controllers.healthController import urlpatterns as user_urls
from api.controllers.faceController import urlpatterns as face_urls

urlpatterns = [
    path('', include(user_urls)),
    path('face/', include(face_urls)),
]