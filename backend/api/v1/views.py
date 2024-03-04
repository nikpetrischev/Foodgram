# Standart Library
import io
from http import HTTPStatus

# Django Library
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import FileResponse
from django_filters import rest_framework as drf_filters

# DRF Library
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.response import Response

# from reportlab.lib.pagesizes import A4, landscape
# from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics, ttfonts
# from reportlab.platypus import Paragraph, SimpleDocTemplate
from reportlab.platypus.tables import Table, TableStyle

# Local Imports
from .filters import NameSearchFilter, RecipeFilter
from .mixins import PatchNotPutModelMixin
from .permissions import RecipePermission
from .serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShortenedRecipeSerializer,
    TagSerializer,
)
from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
    UserRecipe,
)
from users.serializers import FavouritesOrCartSerializer

User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.order_by('id')
    filter_backends = [drf_filters.DjangoFilterBackend]
    filterset_class = NameSearchFilter
    pagination_class = None
    permission_classes = [permissions.AllowAny]


class RecipeViewSet(
    viewsets.GenericViewSet,
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    PatchNotPutModelMixin,
):
    queryset = Recipe.objects.order_by('id')
    filter_backends = [drf_filters.DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = [RecipePermission]

    def get_serializer_class(self):
        if self.request.method in ['GET']:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = Recipe.objects.filter(pk=pk).first()
        if not recipe:
            return Response(
                {'errors': 'Рецепт не найден'},
                status=HTTPStatus.BAD_REQUEST,
            )
        favorite_item, _ = UserRecipe.objects.get_or_create(
            user=request.user,
            recipe=recipe,
        )
        if favorite_item.is_favorited:
            return Response(
                {'errors': f'"{recipe.name}" уже в избранном'},
                status=HTTPStatus.BAD_REQUEST,
            )
        serializer = FavouritesOrCartSerializer(
            favorite_item,
            data={'is_favorited': True},
            partial=True,
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                ShortenedRecipeSerializer(recipe).data,
                status=HTTPStatus.CREATED,
            )
        return Response(
            serializer.errors,
            status=HTTPStatus.BAD_REQUEST,
        )

    @favorite.mapping.delete
    def favorite_delete(self, request, pk=None):
        recipe = Recipe.objects.filter(pk=pk).first()
        if not recipe:
            return Response(
                {'errors': 'Рецепт не найден'},
                status=HTTPStatus.NOT_FOUND,
            )

        favorite_item = UserRecipe.objects.filter(
            user=request.user,
            recipe=recipe,
            is_favorited=True,
        ).first()
        if not favorite_item:
            return Response(
                {'errors': f'"{recipe.name}" нет в избранном'},
                status=HTTPStatus.BAD_REQUEST,
            )

        serializer = FavouritesOrCartSerializer(
            favorite_item,
            data={'is_favorited': False},
            partial=True,
        )
        if serializer.is_valid():
            serializer.save()
            return Response(status=HTTPStatus.NO_CONTENT)

        return Response(
            serializer.errors,
            status=HTTPStatus.BAD_REQUEST,
        )

    @staticmethod
    def create_pdf(cart_data):
        buffer = io.BytesIO()

        # response = Response(content_type='application/pdf')
        # response['Content-Disposition'] = ('attachment; '
        #                                    'filename="shopping_cart.pdf"')
        # response = Response(
        #     headers={
        #         'Content-Type': 'application/pdf',
        #         'Content-Disposition':
        #             'attachment; filename=shopping_list.pdf',
        #     },
        # )

        pdfmetrics.registerFont(
            ttfonts.TTFont(
                'DejaVuSerif',
                './static/font/DejaVuSerif.ttf',
            ),
        )

        # elements = []
        '''
        doc = SimpleDocTemplate(
            # response,
            buffer,
            pagesize=(landscape(A4)),
        )

        styles = getSampleStyleSheet()
        title_style = styles['Title']
        title_style.fontName = 'DejaVuSerif'
        paragraph = Paragraph('Покупки', styles['Title'])

        elements.append(paragraph)
        '''
        cart_list = [('Продукт', 'Ед.изм.', 'Кол-во')]
        for item in cart_data:
            cart_list.append(
                (
                    item['ingredient__name'],
                    item['ingredient__measurement_unit'],
                    item['total'],
                ),
            )
        table = Table(cart_list, colWidths=(20 * cm, 3 * cm, 5 * cm))

        table.setStyle(
            TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 1, (0, 0, 0)),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSerif', 18),
                    ('BACKGROUND', (0, 0), (-1, 0), (0, 0, 0)),
                    ('TEXTCOLOR', (0, 0), (-1, 0), (1, 1, 1)),
                    ('LINEBEFORE', (1, 0), (1, 0), 2, (1, 1, 1)),
                    ('LINEBEFORE', (2, 0), (2, 0), 2, (1, 1, 1)),
                    ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSerif'),
                    (
                        'ROWBACKGROUNDS',
                        (0, 1),
                        (-1, -1),
                        [(1, 1, 1), (210 / 255, 210 / 255, 210 / 255)],
                    ),
                ],
            ),
        )

        # elements.append(table)
        # doc.build(elements)

        from reportlab.pdfgen import canvas

        # page = canvas.Canvas(response)
        page = canvas.Canvas(buffer)
        table.wrapOn(page, 2.5 * cm, 2.5 * cm)
        table.drawOn(page, 2.5 * cm, 2.5 * cm)
        # page.showPage()
        page.save()
        # response['Content-Disposition'] = ('attachment; '
        #                                    'filename="shopping_list.pdf"')
        # response.write(buffer.getvalue())
        # buffer.close()
        buffer.seek(0)
        response = FileResponse(
            buffer,
            as_attachment=True,
            filename='shopping_list.pdf',
        )
        return response

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        recipes = Recipe.objects.filter(
            userrecipe__user=request.user,
            userrecipe__is_in_shopping_cart=True,
        )
        ingredients = (
            RecipeIngredient.objects.filter(recipe__in=recipes)
            .values(
                'ingredient__name',
                'ingredient__measurement_unit',
            )
            .annotate(total=Sum('amount'))
        )
        return self.create_pdf(ingredients)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = Recipe.objects.filter(pk=pk).first()
        if not recipe:
            return Response(
                {'errors': 'Рецепт не найден'},
                status=HTTPStatus.BAD_REQUEST,
            )

        cart_item, _ = UserRecipe.objects.get_or_create(
            user=request.user,
            recipe=recipe,
        )
        if cart_item.is_in_shopping_cart:
            return Response(
                {'errors': f'"{recipe.name}" уже в корзине'},
                status=HTTPStatus.BAD_REQUEST,
            )

        serializer = FavouritesOrCartSerializer(
            cart_item,
            data={'is_in_shopping_cart': True},
            partial=True,
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                ShortenedRecipeSerializer(recipe).data,
                status=HTTPStatus.CREATED,
            )

        return Response(
            serializer.errors,
            status=HTTPStatus.BAD_REQUEST,
        )

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk=None):
        recipe = Recipe.objects.filter(pk=pk).first()
        if not recipe:
            return Response(
                {'errors': 'Рецепт не найден'},
                status=HTTPStatus.NOT_FOUND,
            )

        cart_item = UserRecipe.objects.filter(
            user=request.user,
            recipe=recipe,
            is_in_shopping_cart=True,
        ).first()
        if not cart_item:
            return Response(
                {'errors': f'"{recipe.name}" нет в корзине'},
                status=HTTPStatus.BAD_REQUEST,
            )

        serializer = FavouritesOrCartSerializer(
            cart_item,
            data={'is_in_shopping_cart': False},
            partial=True,
        )
        if serializer.is_valid():
            serializer.save()
            return Response(status=HTTPStatus.NO_CONTENT)

        return Response(
            serializer.errors,
            status=HTTPStatus.BAD_REQUEST,
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.order_by('id')
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
