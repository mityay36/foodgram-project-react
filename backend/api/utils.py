from users.models import Follow


def subscribed_check(request, instance):
    return (Follow.objects.filter(
        user=request.user, author=instance
    ).exists() and request.user.is_authenticated)
