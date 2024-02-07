from rest_framework import serializers

from users.models import Follow


def subscribed_check(request, instance):
    if request.user.is_anonymous:
        return False
    return Follow.objects.filter(
        user=request.user, author=instance
    ).exists()


def validate_create_serializer(user, data, model, context):
    recipe = data['recipe']
    if context['request'].method == 'POST':
        if model.objects.filter(
                user=user, recipe=recipe
        ).exists():
            raise serializers.ValidationError(
                f'Повторное добавление объекта в модель {model} невозможно.'
            )
    elif context['request'].method == 'DELETE':
        if not model.objects.filter(
                user=user, recipe=recipe
        ).exists():
            raise serializers.ValidationError(
                f'Рецепт не найден в объекте модели {model}.'
            )
