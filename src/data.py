EXPENSE_CATEGORIES = [
    ("餐饮", "RESTAURANT"), ("食材生鲜", "LOCAL_GROCERY_STORE"), ("交通出行", "DIRECTIONS_CAR"),
    ("住房物业", "HOME"), ("水电燃气", "ELECTRIC_BOLT"), ("日用百货", "SHOPPING_BAG"),
    ("服饰美容", "CHECKROOM"), ("医疗健康", "MEDICAL_SERVICES"), ("教育学习", "SCHOOL"),
    ("通讯网络", "PHONE_ANDROID"), ("娱乐休闲", "MOVIE"), ("旅行住宿", "FLIGHT"),
    ("人情礼物", "CARD_GIFT_CARD"), ("宠物", "PETS"), ("运动健身", "FITNESS_CENTER"),
    ("育儿母婴", "CHILD_CARE"), ("汽车养护", "DIRECTIONS_CAR"), ("办公用品", "WORK"),
    ("订阅服务", "SUBSCRIPTIONS"), ("其他支出", "MORE_HORIZ"),
]
INCOME_CATEGORIES = [
    ("工资薪酬", "WORK"), ("奖金补贴", "CARD_GIFT_CARD"), ("投资理财", "TRENDING_UP"),
    ("兼职副业", "COMPUTER"), ("报销退款", "REPLAY"), ("礼金收入", "REDEEM"), ("其他收入", "MORE_HORIZ"),
]
MEALS = ["早餐", "午餐", "晚餐", "加餐", "不区分"]
PAYMENT_METHODS = ["现金", "银行卡", "支付宝", "微信支付", "信用卡", "其他"]
ALL_CATEGORIES = [(name, "支出", icon) for name, icon in EXPENSE_CATEGORIES] + [
    (name, "收入", icon) for name, icon in INCOME_CATEGORIES
]
