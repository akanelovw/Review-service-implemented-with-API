from enum import Enum


class Enums(tuple, Enum):

    TRUE_SEARCH = "1", "true"
    FALSE_SEARCH = "0", "false"


class Urls(str, Enum):

    SEARCH_ING_NAME = "name"
    FAVORITES = "is_favorited"
    SHOPPING_CART = "is_in_shopping_cart"
    AUTHOR = "author"
    TAGS = "tags"
