import json
import random
from datetime import datetime, timedelta

from database import CategoryDB, DishDB, ModifierDB, ModifierGroupDB, OrderDB, OrderItemDB, RestaurantDB, SessionLocal, \
    TableDB, WaiterCallDB, create_tables
from models import OrderStatus, OrderType


def seed_database():
    """Заполняет БД демо-данными"""
    create_tables()
    db = SessionLocal()

    # ─── Restaurant ───
    restaurant = RestaurantDB(
        name="Sabaidee Kitchen 🐘",
        logo_url="/static/logo.png",
        wifi_password="sabaidee123"
    )
    db.add(restaurant)
    db.flush()
    rest_id = restaurant.id

    # ─── Tables ───
    tables = []
    table_labels = ["Corner", "Window", "Patio", "Bar", "Garden", "Terrace", "Family", "VIP"]
    for i in range(1, 9):
        t = TableDB(
            restaurant_id=rest_id,
            number=i,
            label=table_labels[i - 1]
        )
        db.add(t)
        tables.append(t)
    db.flush()
    table = tables[4]  # стол №5 — основной демо-стол для QR
    table_id = table.id
    table_ids = [t.id for t in tables]
    table_id = table.id

    # ─── Categories ───
    categories_data = [
        {
            "sort_order": 0,
            "name_en": "Soups",
            "name_lo": "ຊຸບ",
            "name_cn": "汤",
            "name_ru": "Супы",
            "name_th": "ซุป",
            "name_ko": "수프",
            "name_fr": "Soupes",
            "name_ar": "الحساء",
        },
        {
            "sort_order": 1,
            "name_en": "Rice & Noodles",
            "name_lo": "ເຂົ້າຈີ່",
            "name_cn": "米饭面条",
            "name_ru": "Рис и лапша",
            "name_th": "ข้าวและก๋วยเตียว",
            "name_ko": "밥과 국수",
            "name_fr": "Riz et nouilles",
            "name_ar": "الأرز والمعكرونة",
        },
        {
            "sort_order": 2,
            "name_en": "Grills",
            "name_lo": "ອາຫານປີ້ງ",
            "name_cn": "烤肉",
            "name_ru": "Гриль",
            "name_th": "บาร์บีคิว",
            "name_ko": "구이",
            "name_fr": "Grillades",
            "name_ar": "شواء",
        },
        {
            "sort_order": 3,
            "name_en": "Drinks",
            "name_lo": "ເຄື່ອງດື່ມ",
            "name_cn": "饮料",
            "name_ru": "Напитки",
            "name_th": "เครื่องดื่ม",
            "name_ko": "음료",
            "name_fr": "Boissons",
            "name_ar": "المشروبات",
        },
    ]

    categories = []
    for cat_data in categories_data:
        cat = CategoryDB(restaurant_id=rest_id, **cat_data)
        db.add(cat)
        categories.append(cat)
    db.flush()

    # ─── Dishes ───
    dishes_data = [
        # Soups
        {
            "category_id": categories[0].id,
            "sort_order": 0,
            "name_en": "Tom Yum Soup",
            "name_lo": "ແກງຕົ້ມຍໍາ",
            "name_cn": "冬阴功汤",
            "name_ru": "Том Ям",
            "name_th": "ต้มยำ",
            "name_ko": "톰얌",
            "name_fr": "Tom Yum",
            "name_ar": "حساء توم يام",
            "desc_en": "Lemongrass broth with mushrooms, galangal, kaffir lime and fresh chili. Hot and sour, served with jasmine rice.",
            "desc_lo": "ນ້ຳແກງຕົ້ມຍໍາມີເຫັດ, ຂາວ, ໃບໃບ, ແລະ ເມັກທາຽວ",
            "desc_cn": "柠檬草汤配蘑菇、高良姜、卡非石灰叶和新鲜辣椒。酸辣，配茉莉花米饭。",
            "desc_ru": "Суп том ям с грибами, галангалом, листьями кафира и свежим перцем.",
            "desc_th": "ต้มยำที่มีเห็ด กระเข้าและใบมะกรูด",
            "desc_ko": "레몬그래스 국물에 버섯, 갈랑갈, 카피르라임과 신선한 칠리",
            "desc_fr": "Bouillon de citronnelle avec champignons, galanga, feuilles de citron kaffir et piment frais.",
            "desc_ar": "مرق عشبة الليمون مع الفطر والجلنجال وأوراق الليمون الكافر والفلفل الحار الطازج",
            "price": 70000,
            "photo_url": "/static/img/tom_yum.jpg",
            "is_surprise_eligible": True,
        },
        {
            "category_id": categories[0].id,
            "sort_order": 1,
            "name_en": "Khao Piak Sen",
            "name_lo": "ເຂົ້າປຽກ",
            "name_cn": "汤米粉",
            "name_ru": "Као Пиак",
            "name_th": "ข้าวเปียกชี",
            "name_ko": "카오 피악",
            "name_fr": "Khao Piak",
            "name_ar": "خاو بياك",
            "desc_en": "Soft rice noodles in chicken broth with ginger, garlic, and turmeric.",
            "desc_lo": "ເຂົ້າຫຼາຍໃນນ້ຳບາយໄກ່",
            "desc_cn": "柔软的米粉在鸡汤中配生姜、大蒜和姜黄。",
            "desc_ru": "Мягкие рисовые лапша в курином бульоне с имбирем, чесноком и куркумой.",
            "desc_th": "เส้นข้าวอ่อนในสープไก่ที่มีขิง กระเทียม และขมิ้น",
            "desc_ko": "닭 국물에 부드러운 쌀 국수, 생강, 마늘, 강황",
            "desc_fr": "Nouilles de riz molles dans un bouillon de poulet avec gingembre, ail et curcuma.",
            "desc_ar": "نودلز الأرز اللينة في مرق الدجاج مع الزنجبيل والثوم والكركم",
            "price": 57000,
            "photo_url": "/static/img/khao_piak.jpg",
            "is_surprise_eligible": True,
        },
        # Rice & Noodles
        {
            "category_id": categories[1].id,
            "sort_order": 0,
            "name_en": "Larb Gai",
            "name_lo": "ລາບໄກ່",
            "name_cn": "辣椒鸡肉沙拉",
            "name_ru": "Лаб Гай",
            "name_th": "ลาบไก่",
            "name_ko": "라브 가이",
            "name_fr": "Larb Gai",
            "name_ar": "لارب قاي",
            "desc_en": "Minced chicken with lime juice, fish sauce, chili, herbs and toasted rice powder.",
            "desc_lo": "ໄກ່ຫັກກະສາວໃນ ນ້ຳໜາປາ ພະລ ແລະ ເຫຍ້າ",
            "desc_cn": "绞碎鸡肉配酸橙汁、鱼酱、辣椒、草本植物和烤米粉。",
            "desc_ru": "Рубленое куриное мясо с лаймом, рыбным соусом, перцем, травами и обжаренной рисовой мукой.",
            "desc_th": "ไก่ยากลับกับน้ำมะนาว น้ำปลา พริก สมุนไพร และผงข้าวอบ",
            "desc_ko": "라임 주스, 생선 소스, 고추, 허브 및 구운 쌀가루를 곁들인 갈아낸 닭고기",
            "desc_fr": "Poulet haché avec jus de lime, sauce de poisson, piment, herbes et poudre de riz grillée.",
            "desc_ar": "دجاج مفروم مع عصير الليمون وصلصة السمك والفلفل الحار والأعشاب ومسحوق الأرز المحمص",
            "price": 62000,
            "photo_url": "/static/img/larb_gai.jpg",
            "is_surprise_eligible": True,
        },
        {
            "category_id": categories[1].id,
            "sort_order": 1,
            "name_en": "Fried Rice",
            "name_lo": "ເຂົ້າຜັດ",
            "name_cn": "炒饭",
            "name_ru": "Жареный рис",
            "name_th": "ข้าวผัด",
            "name_ko": "볶음밥",
            "name_fr": "Riz frit",
            "name_ar": "الأرز المقلي",
            "desc_en": "Jasmine rice stir-fried with eggs, vegetables, garlic and soy sauce.",
            "desc_lo": "ເຂົ້າໄສໜາ ຜັດກັບ ໄຂ່, ຜັກ, ກະເລື່ອງ ແລະ ນ້ຳສົ້ມ",
            "desc_cn": "茉莉花米与鸡蛋、蔬菜、大蒜和酱油炒制。",
            "desc_ru": "Жасминовый рис, поджаренный с яйцами, овощами, чесноком и соевым соусом.",
            "desc_th": "ข้าวหอมมะลิผัดกับไข่ ผัก กระเทียม และซีอิ๊ว",
            "desc_ko": "계란, 야채, 마늘 및 간장으로 볶은 재스민 쌀",
            "desc_fr": "Riz jasmin sauté avec œufs, légumes, ail et sauce de soja.",
            "desc_ar": "أرز الياسمين المقلي مع البيض والخضروات والثوم وصلصة الصويا",
            "price": 51000,
            "photo_url": "/static/img/fried_rice.jpg",
            "is_surprise_eligible": True,
        },
        {
            "category_id": categories[1].id,
            "sort_order": 2,
            "name_en": "Pad Thai",
            "name_lo": "ປັດໄທ",
            "name_cn": "泰国炒面",
            "name_ru": "Пад Тай",
            "name_th": "ผัดไทย",
            "name_ko": "팟타이",
            "name_fr": "Pad Thai",
            "name_ar": "بات تايلاندي",
            "desc_en": "Rice noodles stir-fried with shrimp, chicken, eggs, peanuts, lime and tamarind sauce.",
            "desc_lo": "ເສັ້ນເຂົ້າຜັດກັບ ກຸ້ງ, ໄກ່, ໄຂ່, ຖົ່ວ ແລະ ແກງກະ�าລາວ",
            "desc_cn": "米粉与虾、鸡、鸡蛋、花生、酸橙和罗望子酱炒制。",
            "desc_ru": "Рисовая лапша, поджаренная с креветками, курицей, яйцами, арахисом, лаймом и тамариндовым соусом.",
            "desc_th": "ก๋วยเตียวผัดกับกุ้ง ไก่ ไข่ ถั่วลิสง มะนาว และน้ำมะขามหวาน",
            "desc_ko": "새우, 닭, 계란, 땅콩, 라임 및 타마린드 소스로 볶은 쌀 국수",
            "desc_fr": "Nouilles de riz sautées avec crevettes, poulet, œufs, cacahuètes, citron vert et sauce de tamarin.",
            "desc_ar": "نودلز الأرز المقلية مع الروبيان والدجاج والبيض والفول السوداني وعصير الليمون وصلصة التمر الهندي",
            "price": 65000,
            "photo_url": "/static/img/pad_thai.jpg",
            "is_surprise_eligible": True,
        },
        # Grills
        {
            "category_id": categories[2].id,
            "sort_order": 0,
            "name_en": "Ping Gai",
            "name_lo": "ໄກ່ປີ້ງ",
            "name_cn": "烤鸡",
            "name_ru": "Пин Гай",
            "name_th": "ไก่ย่าง",
            "name_ko": "핑 가이",
            "name_fr": "Poulet grillé",
            "name_ar": "دجاج مشوي",
            "desc_en": "Half chicken marinated in garlic, lemongrass and spices, grilled until crispy.",
            "desc_lo": "ໄກ່ສາກ ໝາກຕົ້ວ, ຖົ່ວລາວ ແລະ ເຫຼື້ອມ",
            "desc_cn": "用大蒜、柠檬草和香料腌制的半鸡，烤至酥脆。",
            "desc_ru": "Половинка курицы, маринованная в чесноке, лемонграссе и специях, запечённая до хрустящей корочки.",
            "desc_th": "ไก่ครึ่งตัว腌ด้วยกระเทียม หญ้าตะขบ และเครื่องเทศ ย่างจนกรอบ",
            "desc_ko": "마늘, 레몬그래스 및 향신료에 절인 반닭, 바삭해질 때까지 구워짐",
            "desc_fr": "Demi-poulet mariné à l'ail, citronnelle et épices, grillé jusqu'à croustillant.",
            "desc_ar": "نصف دجاجة مخللة بالثوم والليمون والتوابل، مشوية حتى تصبح مقرمشة",
            "price": 82000,
            "photo_url": "/static/img/ping_gai.jpg",
            "is_surprise_eligible": True,
        },
        {
            "category_id": categories[2].id,
            "sort_order": 1,
            "name_en": "Sai Oua",
            "name_lo": "ໄສ້ອົວ",
            "name_cn": "老挝香肠",
            "name_ru": "Сай Уа",
            "name_th": "ไส้อั่ว",
            "name_ko": "사이 우아",
            "name_fr": "Sai Oua",
            "name_ar": "ساي أوا",
            "desc_en": "Lao sausage with herbs, lemongrass and spices. Grilled and served with sticky rice.",
            "desc_lo": "ໄສ້ອົວລາວ ມີ ສົ້ມຕົ້ວ ແລະ ເຫຼື້ອມ. ປີ້ງ ແລະ ໃຫ້ຮັບປະທານ ກັບ ເຂົ້າຫນຽວ",
            "desc_cn": "老挝香肠，含有草本植物、柠檬草和香料。烤制，配粘米。",
            "desc_ru": "Лаосская колбаса с травами, лемонграссом и специями. Запечённая и подаётся с липким рисом.",
            "desc_th": "ไส้อั่วลาวมีสมุนไพร หญ้าตะขบ และเครื่องเทศ ย่างและแนวคิดด้วยข้าวเหนียว",
            "desc_ko": "허브, 레몬그래스 및 향신료를 포함한 라오 소시지. 구우면서 찹쌀밥과 함께 제공",
            "desc_fr": "Saucisse laotienne aux herbes, citronnelle et épices. Grillée et servie avec du riz gluant.",
            "desc_ar": "نقانق لاوية مع الأعشاب والليمون والتوابل. مشوية وتقدم مع الأرز اللزج",
            "price": 77000,
            "photo_url": "/static/img/sai_oua.jpg",
            "is_surprise_eligible": True,
        },
        # Drinks
        {
            "category_id": categories[3].id,
            "sort_order": 0,
            "name_en": "Beer Lao",
            "name_lo": "ເບຍລາວ",
            "name_cn": "老挝啤酒",
            "name_ru": "Бир Лао",
            "name_th": "เบียร์ลาว",
            "name_ko": "맥주 라오",
            "name_fr": "Bière Lao",
            "name_ar": "بيرة لاو",
            "desc_en": "Cold crisp beer, the most popular drink in Laos.",
            "desc_lo": "ເບຍເຢັນ ມີລົດຊາດ ຫຼາຍທີ່ສຸດໃນລາວ",
            "desc_cn": "冷清爽啤酒，老挝最受欢迎的饮料。",
            "desc_ru": "Холодное хрустящее пиво, самый популярный напиток в Лаосе.",
            "desc_th": "เบียร์เย็นและสดใหม่เครื่องดื่มที่นิยมที่สุดในลาว",
            "desc_ko": "차갑고 상큼한 맥주, 라오스에서 가장 인기 있는 음료",
            "desc_fr": "Bière froide et croustillante, la boisson la plus populaire au Laos.",
            "desc_ar": "بيرة باردة ومقرمشة، المشروب الأكثر شعبية في لاوس",
            "price": 31000,
            "photo_url": "/static/img/beer_lao.jpg",
            "is_surprise_eligible": False,
        },
        {
            "category_id": categories[3].id,
            "sort_order": 1,
            "name_en": "Lao Coffee",
            "name_lo": "ກາເຟ້ລາວ",
            "name_cn": "老挝咖啡",
            "name_ru": "Лаосский кофе",
            "name_th": "กาแฟลาว",
            "name_ko": "라오 커피",
            "name_fr": "Café Lao",
            "name_ar": "قهوة لاو",
            "desc_en": "Strong dark roast coffee served hot or iced with sweetened condensed milk.",
            "desc_lo": "ກາເຟ້ສີ່ນບຸ້ນ ມີນ້ຳຕາລສາວ",
            "desc_cn": "浓郁深焙咖啡，热或冰镇配甜炼乳。",
            "desc_ru": "Крепкий тёмный кофе, подаётся горячим или со льдом со сгущённым молоком.",
            "desc_th": "กาแฟดำเข้มเสียบร้อนหรือเย็นด้วยนมข้นหวาน",
            "desc_ko": "진하고 어두운 볶음 커피, 뜨겁거나 얼음으로 제공되며 단맛의 연유가 들어감",
            "desc_fr": "Café noir foncé servi chaud ou glacé avec du lait concentré sucré.",
            "desc_ar": "قهوة داكنة غنية مقدمة ساخنة أو مثلجة مع الحليب المحلى المكثف",
            "price": 25000,
            "photo_url": "/static/img/lao_coffee.jpg",
            "is_surprise_eligible": False,
        },
        {
            "category_id": categories[3].id,
            "sort_order": 2,
            "name_en": "Fresh Juice",
            "name_lo": "ນ້ຳສົ້ມ",
            "name_cn": "鲜果汁",
            "name_ru": "Свежий сок",
            "name_th": "น้ำสดใหม่",
            "name_ko": "신선한 주스",
            "name_fr": "Jus frais",
            "name_ar": "عصير طازج",
            "desc_en": "Fresh orange, mango or papaya juice, made daily.",
            "desc_lo": "ນ້ຳສົ້ມ, ໝາກມະມ່ວງ ຫຼື ມາລາຍາ ສົ້ມ ແລະ ປະທຸມວັນນະຄາມ",
            "desc_cn": "新鲜橙汁、芒果或木瓜汁，每天新鲜制作。",
            "desc_ru": "Свежий апельсиновый, манговый или папайский сок, изготовленный ежедневно.",
            "desc_th": "น้ำส้มสดใหม่ แมงโก้ หรือมะละกอ ทำใหม่ทุกวัน",
            "desc_ko": "신선한 오렌지, 망고 또는 파파야 주스, 매일 신선하게 제조",
            "desc_fr": "Jus d'orange, mangue ou papaye frais, préparé quotidiennement.",
            "desc_ar": "عصير برتقال أو مانجو أو بابايا طازج، مصنوع يوميًا",
            "price": 37000,
            "photo_url": "/static/img/fresh_juice.jpg",
            "is_surprise_eligible": False,
        },
        {
            "category_id": categories[3].id,
            "sort_order": 3,
            "name_en": "Water",
            "name_lo": "ນ້ຳ",
            "name_cn": "水",
            "name_ru": "Вода",
            "name_th": "น้ำ",
            "name_ko": "물",
            "name_fr": "Eau",
            "name_ar": "ماء",
            "desc_en": "Filtered water, hot or cold.",
            "desc_lo": "ນ້ຳຜ່ານກັ່ນຕອງ",
            "desc_cn": "过滤水，热或冷。",
            "desc_ru": "Фильтрованная вода, горячая или холодная.",
            "desc_th": "น้ำที่กรองแล้ว ร้อนหรือเย็น",
            "desc_ko": "여과된 물, 뜨겁거나 차가움",
            "desc_fr": "Eau filtrée, chaude ou froide.",
            "desc_ar": "ماء مفلتر ، ساخن أو بارد",
            "price": 10000,
            "photo_url": "/static/img/water.jpg",
            "is_surprise_eligible": False,
        },
        {
            "category_id": categories[1].id,
            "sort_order": 3,
            "name_en": "Sticky Rice",
            "name_lo": "ເຂົ້າຫນຽວ",
            "name_cn": "糯米饭",
            "name_ru": "Липкий рис",
            "name_th": "ข้าวเหนียว",
            "name_ko": "찹쌀밥",
            "name_fr": "Riz gluant",
            "name_ar": "الأرز اللزج",
            "desc_en": "Steamed glutinous rice, traditionally served with Lao dishes.",
            "desc_lo": "ເຂົ້າຫນຽວລາວຕາຸາມັກ",
            "desc_cn": "蒸糯米饭，传统配老挝菜肴。",
            "desc_ru": "Пропаренный клейкий рис, традиционно подаётся с лаосскими блюдами.",
            "desc_th": "ข้าวเหนียวนึ่ง มักจะเสิร์ฟกับอาหารลาวแบบดั้งเดิม",
            "desc_ko": "찐 찹쌀밥, 전통적으로 라오스 요리와 함께 제공",
            "desc_fr": "Riz gluant cuit à la vapeur, traditionnellement servi avec les plats laotiens.",
            "desc_ar": "أرز لزج مطبوخ على البخار، يقدم تقليديًا مع الأطباق اللاوية",
            "price": 20000,
            "photo_url": "/static/img/sticky_rice.jpg",
            "is_surprise_eligible": False,
        },
    ]

    dishes = []
    for dish_data in dishes_data:
        dish = DishDB(**dish_data)
        db.add(dish)
        dishes.append(dish)
    db.flush()

    # ─── Modifier Groups & Modifiers ───
    # Spicy level для некоторых блюд
    spicy_dishes = [0, 1, 2, 4]  # Tom Yum, Khao Piak, Larb, Pad Thai
    for dish_idx in spicy_dishes:
        mg = ModifierGroupDB(
            dish_id=dishes[dish_idx].id,
            name_en="Spicy level",
            name_lo="ລະດັບພີ້ງ",
            name_cn="辣度",
            name_ru="Острота",
            name_th="ระดับเผ็ด",
            name_ko="매운정도",
            name_fr="Niveau épicé",
            name_ar="مستوى الحار",
            required=True
        )
        db.add(mg)
        db.flush()

        modifiers = [
            {"label_en": "No spice", "label_lo": "ບໍ່ມີພີ້ງ", "label_cn": "不辣", "label_ru": "Без остроты",
             "label_th": "ไม่เผ็ด", "label_ko": "맵지않음", "label_fr": "Pas épicé", "label_ar": "بدون حار", "emoji": "🌿",
             "price_add": 0},
            {"label_en": "Mild", "label_lo": "ອ່ອນ", "label_cn": "温和", "label_ru": "Мягко",
             "label_th": "เบา", "label_ko": "약함", "label_fr": "Doux", "label_ar": "خفيف", "emoji": "🌿", "price_add": 0},
            {"label_en": "Medium", "label_lo": "ກາງ", "label_cn": "中等", "label_ru": "Среднее",
             "label_th": "ปานกลาง", "label_ko": "중간", "label_fr": "Moyen", "label_ar": "متوسط", "emoji": "🌶️",
             "price_add": 0},
            {"label_en": "Hot", "label_lo": "ຮ້ອນ", "label_cn": "辣", "label_ru": "Горячо",
             "label_th": "เผ็ด", "label_ko": "맵음", "label_fr": "Chaud", "label_ar": "حار", "emoji": "🌶️🌶️",
             "price_add": 0},
            {"label_en": "Fire", "label_lo": "ໄຟ", "label_cn": "极辣", "label_ru": "Огнь",
             "label_th": "ไฟ", "label_ko": "매운맛", "label_fr": "Feu", "label_ar": "نار", "emoji": "🌶️🌶️🌶️",
             "price_add": 0},
        ]

        for mod_data in modifiers:
            mod = ModifierDB(group_id=mg.id, **mod_data)
            db.add(mod)

    # Coffee sweetness
    lao_coffee_idx = 8
    mg_coffee = ModifierGroupDB(
        dish_id=dishes[lao_coffee_idx].id,
        name_en="Sweetness",
        name_lo="ຄວາມຫວານ",
        name_cn="甜度",
        name_ru="Сладость",
        name_th="ความหวาน",
        name_ko="단맛",
        name_fr="Douceur",
        name_ar="الحلاوة",
        required=True
    )
    db.add(mg_coffee)
    db.flush()

    coffee_mods = [
        {"label_en": "Sweet", "label_lo": "ຫວານ", "label_cn": "甜", "label_ru": "Сладко",
         "label_th": "หวาน", "label_ko": "달콤한", "label_fr": "Sucré", "label_ar": "حلو", "emoji": "🍯", "price_add": 0},
        {"label_en": "Medium", "label_lo": "ກາງ", "label_cn": "中等", "label_ru": "Среднее",
         "label_th": "ปานกลาง", "label_ko": "중간", "label_fr": "Moyen", "label_ar": "متوسط", "emoji": None,
         "price_add": 0},
        {"label_en": "No sugar", "label_lo": "ບໍ່ມີນ້ຳຕາລ", "label_cn": "无糖", "label_ru": "Без сахара",
         "label_th": "ไม่มีน้ำตาล", "label_ko": "설탕없음", "label_fr": "Sans sucre", "label_ar": "بدون سكر", "emoji": None,
         "price_add": 0},
    ]

    for mod_data in coffee_mods:
        mod = ModifierDB(group_id=mg_coffee.id, **mod_data)
        db.add(mod)

    db.commit()

    # ─── Generate fake orders (438 за 30 дней) ───
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)

    order_statuses = [OrderStatus.DONE, OrderStatus.DONE, OrderStatus.DONE, OrderStatus.DONE,
                      OrderStatus.DONE, OrderStatus.DONE, OrderStatus.READY, OrderStatus.ACCEPTED,
                      OrderStatus.NEW]  # 89.5% done, ~10% other

    # Распределение по времени суток (Morning: 72, Lunch: 187, Evening: 158, Night: 21)
    time_distribution = {
        "morning": (6, 11, 72),  # 6-11 часов, 72 заказа
        "lunch": (11, 15, 187),  # 11-15 часов, 187 заказов
        "evening": (15, 21, 158),  # 15-21 час, 158 заказов
        "night": (21, 6, 21),  # 21-6 часов, 21 заказ
    }

    order_count = 0
    for period, (start_hour, end_hour, count) in time_distribution.items():
        for _ in range(count):
            # Random datetime в диапазоне 30 дней
            random_date = thirty_days_ago + timedelta(days=random.randint(0, 29))

            # Random hour in period
            if period == "night":
                hour = random.choice(list(range(21, 24)) + list(range(0, 6)))
            else:
                hour = random.randint(start_hour, end_hour - 1)

            created_at = random_date.replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59))

            # Random order type (80% dine-in, 20% takeaway)
            order_type = OrderType.DINE_IN if random.random() > 0.2 else OrderType.TAKEAWAY

            # Random table
            order_table_id = table_id if random.random() > 0.7 else random.choice(table_ids)

            # Random status
            status = random.choice(order_statuses)

            # Random items (1-4 dishes per order)
            num_items = random.randint(1, 4)
            selected_dishes = random.sample(range(len(dishes)), min(num_items, len(dishes)))

            total = 0
            order = OrderDB(
                restaurant_id=rest_id,
                table_id=order_table_id,
                order_type=order_type,
                status=status,
                created_at=created_at,
                total=0
            )
            db.add(order)
            db.flush()

            for dish_idx in selected_dishes:
                qty = random.randint(1, 3)
                dish = dishes[dish_idx]
                subtotal = dish.price * qty
                total += subtotal

                modifiers_json = None
                if dish.modifier_groups:
                    mods = {}
                    for mg in dish.modifier_groups:
                        if mg.modifiers:
                            selected_mod = random.choice(mg.modifiers)
                            mods[mg.id] = selected_mod.id
                    modifiers_json = json.dumps(mods) if mods else None

                order_item = OrderItemDB(
                    order_id=order.id,
                    dish_id=dish.id,
                    qty=qty,
                    modifiers_json=modifiers_json,
                    subtotal=subtotal
                )
                db.add(order_item)

            order.total = total
            order_count += 1

    db.commit()

    # ─── Generate fake waiter calls (20-30 за месяц) ───
    for _ in range(random.randint(20, 30)):
        called_at = thirty_days_ago + timedelta(
            days=random.randint(0, 29),
            hours=random.randint(6, 22),
            minutes=random.randint(0, 59)
        )
        # 70% answered, 30% not answered
        answered_at = called_at + timedelta(minutes=random.randint(1, 5)) if random.random() > 0.3 else None

        call = WaiterCallDB(
            restaurant_id=rest_id,
            table_id=random.choice(table_ids),
            called_at=called_at,
            answered_at=answered_at
        )
        db.add(call)

    db.commit()
    db.close()

    print(f"✅ Database seeded successfully!")
    print(f"   Restaurant: Sabaidee Kitchen")
    print(f"   Tables: 1")
    print(f"   Categories: {len(categories)}")
    print(f"   Dishes: {len(dishes)}")
    print(f"   Orders: {order_count}")
    print(f"   Waiter calls: ~25")


if __name__ == "__main__":
    seed_database()
