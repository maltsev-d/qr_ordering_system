import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from db.models import OrderStatus, OrderType

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─── ORM Models ───

class RestaurantDB(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    logo_url = Column(String, nullable=True)
    wifi_password = Column(String, nullable=True)
    payment_qr_url = Column(String, nullable=True)

    tables = relationship("TableDB", back_populates="restaurant")
    categories = relationship("CategoryDB", back_populates="restaurant")
    orders = relationship("OrderDB", back_populates="restaurant")
    waiter_calls = relationship("WaiterCallDB", back_populates="restaurant")
    modifier_groups = relationship("ModifierGroupDB", back_populates="restaurant")


class TableDB(Base):
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), index=True)
    number = Column(Integer)
    label = Column(String, nullable=True)

    restaurant = relationship("RestaurantDB", back_populates="tables")
    orders = relationship("OrderDB", back_populates="table")
    waiter_calls = relationship("WaiterCallDB", back_populates="table")


class CategoryDB(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), index=True)
    sort_order = Column(Integer, default=0)
    name_en = Column(String)
    name_lo = Column(String)
    name_cn = Column(String)
    name_ru = Column(String)
    name_th = Column(String)
    name_ko = Column(String)
    name_fr = Column(String)
    name_ar = Column(String)

    restaurant = relationship("RestaurantDB", back_populates="categories")
    dishes = relationship("DishDB", back_populates="category")


class DishDB(Base):
    __tablename__ = "dishes"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), index=True)
    sort_order = Column(Integer, default=0)

    # availability
    active = Column(Boolean, default=True, index=True)  # блюдо существует в меню
    is_available = Column(Boolean, default=True, index=True)  # блюдо доступно сейчас (стоп-лист)
    is_new = Column(Boolean, default=False)  # бейдж NEW
    is_surprise_eligible = Column(Boolean, default=False)

    # names
    name_en = Column(String)
    name_lo = Column(String)
    name_cn = Column(String)
    name_ru = Column(String)
    name_th = Column(String)
    name_ko = Column(String)
    name_fr = Column(String)
    name_ar = Column(String)

    # descriptions
    desc_en = Column(Text)
    desc_lo = Column(Text)
    desc_cn = Column(Text)
    desc_ru = Column(Text)
    desc_th = Column(Text)
    desc_ko = Column(Text)
    desc_fr = Column(Text)
    desc_ar = Column(Text)

    # pricing
    price = Column(Integer)
    discount_price = Column(Integer, nullable=True)  # None = нет скидки

    # media
    photo_url = Column(String, nullable=True)

    # tags (JSON-массивы, значения из DIETARY_TAGS / ALLERGENS)
    dietary_tags = Column(JSON, default=list)  # ["veg", "no_pork", ...]
    allergens = Column(JSON, default=list)  # ["gluten", "nuts", ...]

    category = relationship("CategoryDB", back_populates="dishes")
    modifier_links = relationship("DishModifierGroup", back_populates="dish")
    order_items = relationship("OrderItemDB", back_populates="dish")


class ModifierGroupDB(Base):
    __tablename__ = "modifier_groups"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), index=True)
    name_en = Column(String)
    name_lo = Column(String)
    name_cn = Column(String)
    name_ru = Column(String)
    name_th = Column(String)
    name_ko = Column(String)
    name_fr = Column(String)
    name_ar = Column(String)
    required = Column(Boolean, default=False)

    restaurant = relationship("RestaurantDB", back_populates="modifier_groups")
    modifiers = relationship("ModifierDB", back_populates="group")
    dish_links = relationship("DishModifierGroup", back_populates="group")


class DishModifierGroup(Base):
    __tablename__ = "dish_modifier_groups"

    id = Column(Integer, primary_key=True, index=True)
    dish_id = Column(Integer, ForeignKey("dishes.id"), index=True)
    group_id = Column(Integer, ForeignKey("modifier_groups.id"), index=True)
    sort_order = Column(Integer, default=0)

    dish = relationship("DishDB", back_populates="modifier_links")
    group = relationship("ModifierGroupDB", back_populates="dish_links")


class ModifierDB(Base):
    __tablename__ = "modifiers"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("modifier_groups.id"), index=True)
    label_en = Column(String)
    label_lo = Column(String)
    label_cn = Column(String)
    label_ru = Column(String)
    label_th = Column(String)
    label_ko = Column(String)
    label_fr = Column(String)
    label_ar = Column(String)
    emoji = Column(String, nullable=True)
    price_add = Column(Integer, default=0)  # 0 = бесплатно

    group = relationship("ModifierGroupDB", back_populates="modifiers")


class OrderDB(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), index=True)
    table_id = Column(Integer, ForeignKey("tables.id"), index=True)
    order_type = Column(Enum(OrderType), default=OrderType.DINE_IN)
    status = Column(Enum(OrderStatus), default=OrderStatus.NEW, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    total = Column(Integer)
    comment = Column(Text, nullable=True)  # комментарий гостя

    restaurant = relationship("RestaurantDB", back_populates="orders")
    table = relationship("TableDB", back_populates="orders")
    items = relationship("OrderItemDB", back_populates="order")


class OrderItemDB(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), index=True)
    dish_id = Column(Integer, ForeignKey("dishes.id"), index=True)
    qty = Column(Integer)
    modifiers_json = Column(Text, nullable=True)  # {"group_id": modifier_id, ...}
    subtotal = Column(Integer)  # уже с учётом price_add и qty

    order = relationship("OrderDB", back_populates="items")
    dish = relationship("DishDB", back_populates="order_items")


class WaiterCallDB(Base):
    __tablename__ = "waiter_calls"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), index=True)
    table_id = Column(Integer, ForeignKey("tables.id"), index=True)
    called_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    answered_at = Column(DateTime, nullable=True)

    restaurant = relationship("RestaurantDB", back_populates="waiter_calls")
    table = relationship("TableDB", back_populates="waiter_calls")


# ─── Init ───

def create_tables():
    Base.metadata.create_all(bind=engine)


def drop_and_recreate():
    """Пересоздать все таблицы. Все данные удаляются."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
