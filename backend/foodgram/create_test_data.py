import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodgram.settings')
django.setup()

from api.models import Ingredient

def create_data():
    ingredients = [
        {"name": "Мука", "measurement_unit": "г"},
        {"name": "Сахар", "measurement_unit": "г"},
    ]
    
    for item in ingredients:
        Ingredient.objects.get_or_create(**item)
    
    print("Тестовые данные успешно созданы!")

if __name__ == "__main__":
    create_data()