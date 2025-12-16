import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dict.settings")
django.setup()

from django.apps import apps
from django.core.files import File

MODELS = [
    ("myapp", "TradeWiseCoin", "image"),
    ("myapp", "Product", "image"),
]

BASE_MEDIA = "media"

for app, model, field in MODELS:
    Model = apps.get_model(app, model)
    for obj in Model.objects.exclude(**{field: ""}):
        file_path = os.path.join(BASE_MEDIA, getattr(obj, field).name)
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                getattr(obj, field).save(
                    os.path.basename(file_path),
                    File(f),
                    save=True
                )
                print(f"Uploaded: {file_path}")
