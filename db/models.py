from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


# ─── Enums ───
class OrderType(str, Enum):
    DINE_IN = "dine_in"
    TAKEAWAY = "takeaway"


class OrderStatus(str, Enum):
    NEW = "new"
    ACCEPTED = "accepted"
    READY = "ready"
    DONE = "done"


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
    price_add: int = 0  # в наименьших единицах (лак)


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
    active: bool = True
    name_en: str
    name_lo: str
    name_cn: str
    name_ru: str
    name_th: str
    name_ko: str
    name_fr: str
    name_ar: str
    desc_en: str
    desc_lo: str
    desc_cn: str
    desc_ru: str
    desc_th: str
    desc_ko: str
    desc_fr: str
    desc_ar: str
    price: int  # в лаках
    photo_url: Optional[str] = None
    is_surprise_eligible: bool = False


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
    modifiers_json: Optional[str] = None  # JSON строка с выбранными модификаторами
    subtotal: int  # в лаках


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
    total: int  # в лаках


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


class OrderRequest(BaseModel):
    restaurant_id: int
    table_id: int
    order_type: OrderType
    items: List[dict]  # [{"dish_id": 1, "qty": 2, "modifiers": {...}}]


class UpdateOrderStatusRequest(BaseModel):
    status: OrderStatus
