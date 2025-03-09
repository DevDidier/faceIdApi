import os
import face_recognition
from django.core.files.storage import default_storage
from rest_framework.response import Response
from rest_framework.views import APIView
from django.urls import path
from django.conf import settings

FACES_DIR = os.path.join(settings.MEDIA_ROOT, "faces")
os.makedirs(FACES_DIR, exist_ok=True)

class UploadFaceView(APIView):
    def post(self, request):
        """
        Guarda imágenes con el ID de usuario al inicio del nombre,
        pero solo si contienen un rostro válido.
        """
        user_id = request.data.get("user_id")

        if not user_id:
            return Response({"error": "El campo 'user_id' es obligatorio"}, status=400)

        files = request.FILES.getlist("images")
        if not files:
            return Response({"error": "No se enviaron imágenes"}, status=400)

        if len(files) > 10:
            return Response({"error": "Límite de imágenes excedido (máximo 10)"}, status=400)

        saved_files = []
        for file in files:
            filename = f"{user_id}_{file.name}"
            file_path = os.path.join(FACES_DIR, filename)

            # Guardar temporalmente la imagen
            with default_storage.open(file_path, "wb") as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            # Verificar si la imagen contiene un rostro
            image = face_recognition.load_image_file(file_path)
            face_locations = face_recognition.face_locations(image)

            if not face_locations:
                os.remove(file_path)  # Eliminar si no tiene rostro
                continue  # Pasar a la siguiente imagen

            saved_files.append(filename)

        if not saved_files:
            return Response({"error": "No se detectó correctamente el rostro, intente nuevamente"}, status=400)

        return Response({
            "message": f"Se guardaron {len(saved_files)} imágenes con rostro para el usuario {user_id}",
            "files": saved_files
        })

class RecognizeFaceView(APIView):
    def post(self, request):
        """
        Recibe una imagen, la compara con las imágenes almacenadas y devuelve si hay coincidencia.
        La imagen temporal se elimina después de su uso.
        """
        file = request.FILES.get("image")
        if not file:
            return Response({"error": "No se envió ninguna imagen"}, status=400)

        # Guardar la imagen temporalmente en el directorio de medios
        temp_path = os.path.join(settings.MEDIA_ROOT, file.name)
        with default_storage.open(temp_path, "wb") as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        try:
            # Cargar la imagen y obtener sus codificaciones faciales
            test_image = face_recognition.load_image_file(temp_path)
            test_encoding = face_recognition.face_encodings(test_image)

            if not test_encoding:
                return Response({"error": "No se detectó ningún rostro en la imagen"}, status=400)

            test_encoding = test_encoding[0]

            # Comparar con imágenes almacenadas en FACES_DIR
            for face_file in os.listdir(FACES_DIR):
                known_image = face_recognition.load_image_file(os.path.join(FACES_DIR, face_file))
                known_encoding = face_recognition.face_encodings(known_image)

                if known_encoding:
                    result = face_recognition.compare_faces([known_encoding[0]], test_encoding)
                    if result[0]:
                        return Response({"message": f"¡Rostro reconocido! Coincide con {face_file}"})

            return Response({"message": "Rostro no reconocido"})

        finally:
            # Eliminar la imagen temporal después de la comparación
            if os.path.exists(temp_path):
                os.remove(temp_path)

urlpatterns = [
    path('upload-face', UploadFaceView.as_view(), name='upload_face'),
    path('recognize-face', RecognizeFaceView.as_view(), name='recognize_face'),
]