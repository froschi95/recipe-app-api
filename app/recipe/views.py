"""
Views for the recipe APIs
"""
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)
from rest_framework import (
    viewsets,
    mixins,
    status,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import (
    Recipe,
    Tag,
    Ingredient,
)
from recipe import serializers

@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma separated list of tag IDs to filter',
            ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description='Comma separated list of ingredient IDs to filter'
            )
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    """View for Manage recipes APIs"""
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication,]
    permission_classes = [IsAuthenticated,]

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers"""
        return [int(str_id)for str_id in qs.split(',')]

    def get_queryset(self):
        """Retrieve recipes for authenticated users."""
        tags  = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients:
            ingredient_ids =self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)

        return queryset.filter(user=self.request.user).order_by('-id').distinct()

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return serializers.RecipeSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe"""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to a recipe"""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        # Save the file and create the Image model instance
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.BOOL, enum=[0, 1],
                description='Filter by items assigned to recipes'
            )
        ]
    )
)
class BaseRecipeAttrViewSet(mixins.DestroyModelMixin,
                 mixins.UpdateModelMixin,
                 mixins.ListModelMixin,
                 viewsets.GenericViewSet):
    """Base viewset for recipe attributes"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve and filter queryset to authenticated user"""
        assigned_only = bool(int(self.request.query_params.get('assigned_only', 0)))
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)

        return queryset.filter(user=self.request.user).order_by('-name').distinct()



class TagViewSet(BaseRecipeAttrViewSet):
    """View to Manage Tags in the DB"""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()





class IngredientViewSet(BaseRecipeAttrViewSet):
    """Handle creating and updating ingredients"""
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()


    # # Overriding the create method from Generic ViewSet
    # def create(self, request, *args, **kwargs):
    #     """Add an ingredient to the database"""
    #     data = request.data
    #     name = data['name']
    #     owner = request.user

    #     # Checks if there is already an ingredient with that name
    #     try:
    #         existing_ingredient = Ingredient.objects.get(user=owner, name=name)
    #         return Response({'error': 'Ingredient already exists'}, status=status.