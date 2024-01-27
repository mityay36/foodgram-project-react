import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка данных из csv файла в БД'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help='Путь к файлу')

    def handle(self, *args, **kwargs):
        file_path = kwargs['path'] + 'ingredients.csv'
        with open(
                file_path, 'r',
                encoding='UTF-8'
        ) as ingredients:
            reader = csv.reader(ingredients)

            for row in reader:
                try:
                    obj, created = Ingredient.objects.get_or_create(
                        name=row[0], measurement=row[1],
                    )
                    if not created:
                        print('Ошибка заполнения базы данных ингредиентами')
                except Exception as error:
                    print(f'Ошибка заполнения {row}. {error}.')
        print('Данные загружены')
