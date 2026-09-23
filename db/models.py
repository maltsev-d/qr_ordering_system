from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

# ─── Константы тегов ───

DIETARY_TAGS = ["veg", "no_pork", "no_gluten", "spicy", "halal", "seafood"]

ALLERGENS = ["gluten", "nuts", "dairy", "eggs", "shellfish", "soy"]

DIETARY_TAG_LABELS = {
    "veg": {"en": "Vegetarian", "lo": "ຜັກ", "emoji": "🌿"},
    "no_pork": {"en": "No Pork", "lo": "ບໍ່ມີໝູ", "emoji": "🐷"},
    "no_gluten": {"en": "Gluten Free", "lo": "ບໍ່ມີ Gluten", "emoji": "🌾"},
    "spicy": {"en": "Spicy", "lo": "ເຜັດ", "emoji": "🌶️"},
    "halal": {"en": "Halal", "lo": "ຮາລານ", "emoji": "☪️"},
    "seafood": {"en": "Seafood", "lo": "ອາຫານທະເລ", "emoji": "🦐"},
}

ALLERGEN_LABELS = {
    "gluten": {"en": "Gluten", "emoji": "🌾"},
    "nuts": {"en": "Nuts", "emoji": "🥜"},
    "dairy": {"en": "Dairy", "emoji": "🥛"},
    "eggs": {"en": "Eggs", "emoji": "🥚"},
    "shellfish": {"en": "Shellfish", "emoji": "🦞"},
    "soy": {"en": "Soy", "emoji": "🫘"},
}


# ─── Enums ───

class OrderType(str, Enum):
    DINE_IN = "dine_in"
    TAKEAWAY = "takeaway"


class OrderStatus(str, Enum):
    NEW = "new"
    ACCEPTED = "accepted"
    READY = "ready"
    AWAITING_PAYMENT = "awaiting_payment"
    DONE = "done"
    CANCELLED = "cancelled"


class Language(str, Enum):
    EN = "en"
    ZH = "zh"
    TH = "th"
    RU = "ru"
    KO = "ko"
    FR = "fr"
    LO = "lo"
    AR = "ar"


# ─── Restaurant ───

class RestaurantBase(BaseModel):
    name: str
    logo_url: Optional[str] = None
    wifi_password: Optional[str] = None


class RestaurantCreate(RestaurantBase):
    pass


class Restaurant(RestaurantBase):
    id: int

    class Config:
        from_attributes = True


# ─── Table ───

class TableBase(BaseModel):
    restaurant_id: int
    number: int
    label: Optional[str] = None


class TableCreate(TableBase):
    pass


class Table(TableBase):
    id: int

    class Config:
        from_attributes = True


# ─── Category ───

class CategoryBase(BaseModel):
    restaurant_id: int
    sort_order: int = 0
    name_en: str
    name_lo: str
    name_cn: str
    name_ru: str
    name_th: str
    name_ko: str
    name_fr: str
    name_ar: str


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True


# ─── Modifier ───

class ModifierBase(BaseModel):
    group_id: int
    label_en: str
    label_lo: str
    label_cn: str
    label_ru: str
    label_th: str
    label_ko: str
    label_fr: str
    label_ar: str
    emoji: Optional[str] = None
    price_add: int = 0  # 0 = бесплатно


class ModifierCreate(ModifierBase):
    pass


class Modifier(ModifierBase):
    id: int

    class Config:
        from_attributes = True


# ─── ModifierGroup ───

class ModifierGroupBase(BaseModel):
    dish_id: int
    name_en: str
    name_lo: str
    name_cn: str
    name_ru: str
    name_th: str
    name_ko: str
    name_fr: str
    name_ar: str
    required: bool = False


class ModifierGroupCreate(ModifierGroupBase):
    pass


class ModifierGroup(ModifierGroupBase):
    id: int
    modifiers: List[Modifier] = []

    class Config:
        from_attributes = True


# ─── Dish ───

class DishBase(BaseModel):
    category_id: int
    sort_order: int = 0

    # availability
    active: bool = True
    is_available: bool = True
    is_new: bool = False
    is_surprise_eligible: bool = False

    # names
    name_en: str
    name_lo: str
    name_cn: str
    name_ru: str
    name_th: str
    name_ko: str
    name_fr: str
    name_ar: str

    # descriptions
    desc_en: str
    desc_lo: str
    desc_cn: str
    desc_ru: str
    desc_th: str
    desc_ko: str
    desc_fr: str
    desc_ar: str

    # pricing
    price: int
    discount_price: Optional[int] = None

    # media
    photo_url: Optional[str] = None

    # tags
    dietary_tags: List[str] = []
    allergens: List[str] = []


class DishCreate(DishBase):
    pass


class Dish(DishBase):
    id: int
    modifier_groups: List[ModifierGroup] = []

    class Config:
        from_attributes = True


# ─── OrderItem ───

class OrderItemBase(BaseModel):
    order_id: int
    dish_id: int
    qty: int
    modifiers_json: Optional[str] = None  # {"group_id": modifier_id, ...}
    subtotal: int  # с учётом price_add и qty


class OrderItemCreate(OrderItemBase):
    pass


class OrderItem(OrderItemBase):
    id: int

    class Config:
        from_attributes = True


# ─── Order ───

class OrderBase(BaseModel):
    restaurant_id: int
    table_id: int
    order_type: OrderType
    status: OrderStatus = OrderStatus.NEW
    total: int
    comment: Optional[str] = None


class OrderCreate(OrderBase):
    pass


class Order(OrderBase):
    id: int
    created_at: datetime
    items: List[OrderItem] = []

    class Config:
        from_attributes = True


# ─── WaiterCall ───

class WaiterCallBase(BaseModel):
    restaurant_id: int
    table_id: int


class WaiterCallCreate(WaiterCallBase):
    pass


class WaiterCall(WaiterCallBase):
    id: int
    called_at: datetime
    answered_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Request/Response Schemas ───

class CallWaiterRequest(BaseModel):
    restaurant_id: int
    table_id: int


class OrderItemRequest(BaseModel):
    dish_id: int
    qty: int
    modifiers: dict = {}  # {str(group_id): modifier_id}


class OrderRequest(BaseModel):
    restaurant_id: int
    table_id: int
    order_type: OrderType
    items: List[OrderItemRequest]
    comment: Optional[str] = None


class UpdateOrderStatusRequest(BaseModel):
    status: OrderStatus
