from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, validate_slug

User = get_user_model()


class Tag(models.Model):

    name = models.CharField(
        'Название тэга',
        max_length=200,
        blank=False,
        unique=True,
    )
    color = models.CharField(
        'Цвет',
        max_length=7,
        blank=False,
        default='#ffffff',
    )
    slug = models.SlugField(
        'Слаг тэга',
        unique=True,
        blank=False,
        validators=[
            validate_slug
        ],
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):

    name = models.CharField(
        'Ингредиент',
        max_length=200,
        blank=False,
    )
    measurement = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='Единицы измерения',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):

    name = models.CharField(
        'Название рецепта',
        max_length=200,
        blank=False,
        help_text='Введите название рецепта',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=False,
        related_name='recipes',
        verbose_name='Автор рецепта',
    )
    image = models.ImageField(
        'Изображение',
        upload_to='recipes/',
        blank=False,
        help_text='Прикрепите изображение',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        blank=False,
        related_name='recipes',
        verbose_name='Ингредиенты',
        help_text='Выберите ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        blank=False,
        related_name='recipes',
        verbose_name='Тэги',
        help_text='Выберите тэги',
    )
    text = models.TextField(
        'Описание рецепта',
        blank=False,
        help_text='Введите описание рецепта',
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        blank=False,
        validators=[
            MinValueValidator(
                1,
                'Время приготовления должно быть больше 1'
            )
        ],
        help_text='Время приготовления в минутах',
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        blank=False,
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'Состав рецепта'
        verbose_name_plural = 'Состав рецептов'


class ShoppingList(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        verbose_name='Покупатель',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        null=True,
        related_name='shopping_list',
        verbose_name='Рецепт к покупке',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_recipe'
            ),
        ]

    def __str__(self):
        return f'Корзина пользователя {self.user}'


class Follows(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_favorites',
        verbose_name='Избранное пользователя',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        null=True,
        related_name='favorites',
        verbose_name='Избранные рецепты',
    )

    class Meta:
        verbose_name = 'Список избранных рецептов'
        verbose_name_plural = 'Списки избранных рецептов'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorites'
            ),
        ]

    def __str__(self):
        return f'Избранный рецепт пользователя {self.user}'