"""种子数据生成器 - 6平台x50条=300条商品数据"""

import sqlite3
import random
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "products.db")

PLATFORMS = ["淘宝", "京东", "拼多多", "闲鱼", "1688", "抖音"]
CATEGORIES = ["电子数码", "服装鞋帽", "家居生活", "食品零食", "美妆个护", "手机数码", "母婴用品", "运动户外"]

# 平台费率
PLATFORM_FEE = {
    "淘宝": 0.03, "京东": 0.05, "拼多多": 0.02,
    "闲鱼": 0.01, "1688": 0.005, "抖音": 0.05
}

# 每个分类的真实商品名称模板
PRODUCT_TEMPLATES = {
    "电子数码": [
        "小米Redmi Note 13 Pro 5G手机", "华为FreeBuds Pro 3无线耳机", "罗技G304无线鼠标",
        "雷柏V500Pro机械键盘", "Anker安克65W氮化镓充电器", "绿联Type-C扩展坞",
        "漫步者M120蓝牙音箱", "JBL Tune 510BT头戴耳机", "紫米QB806充电宝20000mAh",
        "小米手环8 Pro", "华为WATCH GT4智能手表", "OPPO Enco Air3耳机",
        "飞利浦SPK6204有线键盘", "樱桃MX 3.0S机械键盘", "倍思65W GaN充电器",
        "绿联高清HDMI线2米", "小米路由器AX3000T", "TP-Link WiFi6路由器",
        "海康威视C200Pro监控摄像头", "罗技C920高清直播摄像头", "绿联NAS硬盘盒",
        "ORICO移动硬盘盒Type-C", "金士顿DTKN 128GB U盘", "三星T7 1TB移动固态硬盘",
        "西部数据1TB机械硬盘", "威刚DDR4 32G内存条", "三星980 Pro 1TB SSD",
        "华硕RTX4060显卡", "微星B760M主板", "英特尔i5-13400F处理器",
        "金河田额定500W电源", "九州风神散热器", "航嘉机箱",
        "爱国者YOGO M2机箱", "绿联USB3.0分线器", "Anker安克数据线",
        "贝尔金苹果充电线", "小米插线板", "公牛GN-B3044插座",
        "飞利浦电动牙刷HX2421", "松下电吹风EH-NA98Q", "戴森V12无线吸尘器",
        "米家空气净化器4 Pro", "智米加湿器2", "石头P10扫地机器人",
        "科沃斯T20 Pro扫地机", "九阳破壁机L18-Y915S", "苏泊尔电饭煲IH",
        "美的微波炉PC23M6W", "格力空调挂机1.5匹", "海尔冰箱BCD-470"
    ],
    "服装鞋帽": [
        "南极人男士纯棉T恤", "优衣库AIRism短袖", "海澜之家男士休闲裤",
        "波司登羽绒服男士", "李宁运动短裤", "安踏跑步鞋男",
        "特步羽毛球鞋", "鸿星尔克卫衣", "361度运动套装",
        "回力帆布鞋经典款", "匹克态极运动鞋", "贵人鸟跑步鞋",
        "森马男士牛仔裤", "美特斯邦威外套", "马克华菲夹克",
        "太平鸟女装连衣裙", "ONLY女士风衣", "VERO MODA针织衫",
        "UR时尚女装外套", "ZARA男士衬衫", "海澜之家Polo衫",
        "耐克Air Force 1", "阿迪达斯Stan Smith", "新百伦574运动鞋",
        "匡威Chuck Taylor All Star", "Vans Old Skool板鞋", "斯凯奇D'lites熊猫鞋",
        "亚瑟士GEL-CONTEND跑鞋", "斐乐老爹鞋", "彪马RS-X运动鞋",
        "卡特保罗工装靴", "其乐沙漠靴", "ECCO商务休闲鞋",
        "红蜻蜓男士皮鞋", "百丽女靴", "达芙妮单鞋",
        "他她女鞋高跟鞋", "千百度女鞋", "意尔康休闲鞋",
        "探路者冲锋衣", "北面冲锋衣", "哥伦比亚抓绒衣",
        "狼爪户外速干衣", "迪卡侬运动背心", "Lululemon瑜伽裤",
        "蕉内冰丝内裤", "都市丽人文胸", "猫人保暖内衣",
        "恒源祥羊毛衫", "鄂尔多斯羊绒衫", "李宁运动文胸"
    ],
    "家居生活": [
        "宜家四件套纯棉床品", "水星家纺蚕丝被", "罗莱鹅绒被",
        "富安娜床垫1.8m", "南极人记忆枕", "小米乳胶枕",
        "佳丽斯床单被套", "梦洁家纺四件套", "博洋家纺被芯",
        "多喜爱床垫", "全友家居布艺沙发", "林氏木业电视柜",
        "源氏木语实木餐桌", "掌上明珠衣柜", "红苹果家具鞋柜",
        "顾家家居功能沙发", "左右家私休闲椅", "曲美家具书桌",
        "索菲亚定制衣柜", "尚品宅配书架", "宜家KALLAX搁架",
        "茶花收纳箱大号", "禧天龙整理箱", "美丽雅收纳袋",
        "生活日记抽屉分隔盒", "晨光文具收纳盒", "得力文件架",
        "爱丽思塑料收纳柜", "家英纳真空压缩袋", "太力真空收纳袋",
        "小米米家台灯1S", "飞利浦LED吸顶灯", "欧普照明吊灯",
        "雷士照明射灯", "佛山照明灯泡", "公牛LED灯带",
        "宜家窗帘遮光", "如鱼得水窗帘", "罗马布艺窗帘",
        "3M地垫门垫", "大达防滑地垫", "丽华地毯",
        "茶花垃圾桶感应", "佳帮手免手洗拖把", "美丽雅旋转拖把",
        "大卫拖把地板清洁", "妙洁百洁布", "思高清洁刷",
        "绿伞洗洁精", "蓝月亮洗衣液", "威露士消毒液"
    ],
    "食品零食": [
        "三只松鼠每日坚果750g", "百草味肉松饼", "良品铺子零食大礼包",
        "洽洽每日坚果", "沃隆每日坚果", "中粮山萃蜂蜜",
        "百草味牛肉干", "科尔沁牛肉粒", "蜀香牛肉丝",
        "周黑鸭卤鸭脖", "绝味鸭脖鸭翅", "煌上煌卤味",
        "卫龙大面筋辣条", "麻辣王子辣条", "三只松鼠辣条",
        "好丽友派巧克力", "奥利奥饼干", "趣多多曲奇",
        "徐福记沙琪玛", "稻香村糕点", "嘉士利早餐饼干",
        "达利园蛋黄派", "盼盼法式小面包", "旺旺雪饼",
        "康师傅红烧牛肉面", "统一老坛酸菜面", "白象汤好喝",
        "五谷道场非油炸面", "拉面说日式拉面", "自嗨锅自热火锅",
        "海底捞自热米饭", "莫小仙自热米粉", "好欢螺螺蛳粉",
        "李子柒螺蛳粉", "邹三和酸辣粉", "阿宽红油面皮",
        "三只松鼠芒果干", "百草味芒果干", "良品铺子草莓干",
        "每鲜说冻干水果", "沃隆蔓越莓干", "新疆大葡萄干",
        "百草味核桃", "三只松鼠夏威夷果", "良品铺子开心果",
        "沃隆巴旦木", "姚生记山核桃", "粒子社腰果",
        "甘源蟹黄味瓜子", "老街口瓜子", "旭东花生"
    ],
    "美妆个护": [
        "完美日记小细管唇釉", "花西子同心锁口红", "橘朵单色眼影",
        "colorkey空气唇釉", "卡姿兰黑磁散粉", "vnk十二色眼影盘",
        "美康粉黛散粉", "稚优泉唇釉", "酵色琥珀眼影",
        "彩棠修容盘", "毛戈平高光粉膏", "卡姿兰大眼眼线笔",
        "完美日记睫毛膏", "KISS ME花漾睫毛膏", "蜜丝婷睫毛膏",
        "珂润润浸保湿面霜", "芙丽芳丝洗面奶", "珂润泡沫洁面",
        "理肤泉B5修复霜", "修丽可CE精华", "倩碧黄油",
        "雅诗兰黛小棕瓶精华", "兰蔻小黑瓶精华", "SK-II神仙水",
        "欧莱雅紫熨斗眼霜", "玉兰油小白瓶", "珀莱雅红宝石精华",
        "薇诺娜舒敏保湿霜", "玉泽皮肤屏障修复", "百雀羚帧颜霜",
        "自然堂小紫瓶精华", "佰草集新七白霜", "相宜本草红景天",
        "大宝SOD蜜", "隆力奇蛇油膏", "百雀羚水嫩精纯",
        "凡士林润肤露", "妮维雅身体乳", "丝塔芙保湿乳",
        "施华蔻洗发水", "沙宣洗发露", "海飞丝去屑洗发水",
        "飘柔丝质柔顺洗发水", "阿道夫洗护套装", "滋源无硅油洗发水",
        "欧莱雅染发剂", "花王泡泡染发剂", "施华蔻染发膏"
    ],
    "手机数码": [
        "iPhone 15 128GB", "iPhone 15 Pro 256GB", "iPhone 15 Pro Max 512GB",
        "华为Mate 60 Pro", "华为Mate 60 Pro+", "华为Pura 70 Pro",
        "小米14 12+256GB", "小米14 Pro 16+512GB", "小米14 Ultra",
        "OPPO Find X7", "OPPO Reno 11 Pro", "vivo X100 Pro",
        "vivo S18 Pro", "荣耀Magic6 Pro", "荣耀100 Pro",
        "一加12 16+512GB", "一加Ace 3", "真我GT5 Pro",
        "iQOO 12 Pro", "红米K70 Pro", "红米K70E",
        "红米Note 13 Pro", "三星Galaxy S24 Ultra", "三星Galaxy S24",
        "三星Galaxy A55", "努比亚Z60 Ultra", "魅族21 Pro",
        "摩托罗拉Edge 50 Pro", "realme GT Neo5", "红魔9 Pro游戏手机",
        "iPad 10代 64GB WiFi", "iPad Air 5 64GB", "iPad Pro 11寸 128GB",
        "华为MatePad Pro 13.2", "小米平板6 Pro", "OPPO Pad 2",
        "vivo Pad3 Pro", "荣耀平板9", "联想小新Pad Pro",
        "Apple Watch S9 GPS", "Apple Watch Ultra 2", "华为Watch 4 Pro",
        "三星Galaxy Watch6", "小米手表S3", "OPPO Watch4 Pro",
        "AirPods Pro 2 USB-C", "AirPods 3", "华为FreeBuds Pro 3",
        "小米Buds 4 Pro", "OPPO Enco X2", "vivo TWS 4"
    ],
    "母婴用品": [
        "帮宝适纸尿裤NB号", "花王妙而舒纸尿裤M号", "大王GOO.N纸尿裤L号",
        "好奇金装纸尿裤XL号", "露安适纯净夜用纸尿裤", "巴布豆菠萝裤",
        "全棉时代棉柔巾", "好孩子婴儿湿巾", "子初婴儿柔湿巾",
        "Babycare湿巾加厚", "安慕斯婴儿湿巾", "可心柔婴儿柔纸巾",
        "飞鹤星飞帆奶粉3段", "伊利金领冠奶粉3段", "君乐宝奶粉3段",
        "爱他美奶粉3段", "美素佳儿奶粉3段", "a2奶粉3段",
        "合生元奶粉3段", "惠氏启赋奶粉3段", "雀巢超启能恩3段",
        "英氏婴儿米粉", "嘉宝米粉", "地球最好米粉",
        "亨氏婴儿面条", "方广婴儿肉泥", "伊威婴幼儿辅食",
        "好孩子婴儿推车", "Babycare婴儿推车", "cybex婴儿推车",
        "gb好孩子安全座椅", "宝得适安全座椅", "猫头鹰安全座椅",
        "可优比婴儿床", "好孩子婴儿床", "Babycare安抚奶嘴",
        "新安怡吸奶器", "美德乐吸奶器", "小白熊温奶器",
        "十月结晶待产包", "子初待产包", "全棉时代婴儿衣服",
        "英氏婴儿连体衣", "好孩子婴儿服装", "丽婴房婴儿套装",
        "巴布豆童鞋", "斯凯奇儿童运动鞋", "江博士学步鞋",
        "费雪玩具摇铃", "澳贝手摇铃", "面包超人牙胶"
    ],
    "运动户外": [
        "李宁篮球7号", "斯伯丁篮球74-604Y", "摩腾篮球GG7X",
        "威尔胜篮球NCAA", "耐克足球5号", "阿迪达斯足球",
        "李宁羽毛球拍", "尤尼克斯天斧99", "威克多神速100X",
        "凯胜K600羽毛球拍", "李宁乒乓球拍", "红双喜乒乓球拍",
        "蝴蝶乒乓球拍", "友谊729乒乓球拍", "迪卡侬网球拍",
        "威尔胜网球拍", "百保力网球拍", "海德网球拍",
        "迪卡侬瑜伽垫", "Keep瑜伽垫", "奥义瑜伽垫加厚",
        "李宁跳绳", "Keep智能跳绳", "悦动圈跳绳",
        "迪卡侬哑铃可调节", "海德哑铃", "Keep哑铃一对",
        "李宁壶铃8kg", "迪卡侬壶铃", "Keep壶铃",
        "Keep健腹轮", "李宁健腹轮", "迪卡侬健腹轮",
        "迪卡侬弹力带", "Keep弹力带", "赛乐弹力带",
        "哥伦比亚冲锋衣", "北面冲锋衣", "狼爪冲锋衣",
        "探路者登山鞋", "萨洛蒙登山鞋", "迈乐登山鞋",
        "挪客帐篷", "牧高笛帐篷", "迪卡侬帐篷",
        "挪客睡袋", "牧高笛睡袋", "天石睡袋",
        "迪卡侬登山包40L", "奥斯普瑞登山包", "格里高利登山包",
        "骑行头盔", "骑行手套", "骑行眼镜",
        "李宁游泳镜", "速比涛泳衣", "阿瑞娜泳镜"
    ]
}

# 每分类图片占位颜色
CATEGORY_GRADIENTS = {
    "电子数码": ["6366f1", "8b5cf6"],
    "服装鞋帽": ["ec4899", "f43f5e"],
    "家居生活": ["10b981", "14b8a6"],
    "食品零食": ["f59e0b", "ef4444"],
    "美妆个护": ["8b5cf6", "ec4899"],
    "手机数码": ["3b82f6", "6366f1"],
    "母婴用品": ["f093fb", "f5576c"],
    "运动户外": ["4facfe", "00f2fe"],
}


def generate_products():
    """生成300条商品数据"""
    products = []
    pid = 1
    for platform in PLATFORMS:
        for cat in CATEGORIES:
            templates = PRODUCT_TEMPLATES[cat]
            # 每平台每分类约取6-7条，总共50条/平台
            for i in range(6):
                if pid > 300:
                    break
                name = templates[(i * 8 + PLATFORMS.index(platform)) % len(templates)]
                # 价格区间按分类调整
                base_prices = {
                    "电子数码": (50, 800), "服装鞋帽": (30, 300),
                    "家居生活": (20, 500), "食品零食": (10, 150),
                    "美妆个护": (20, 400), "手机数码": (500, 2000),
                    "母婴用品": (30, 400), "运动户外": (40, 600)
                }
                lo, hi = base_prices[cat]
                price = round(random.uniform(lo, hi), 1)
                original_price = round(price * random.uniform(1.1, 1.5), 1)
                sales_count = random.randint(100, 50000)
                rating = round(random.uniform(4.2, 5.0), 1)
                seller_names = [
                    f"{platform}官方旗舰店", f"优品数码专营店", f"天天好物店",
                    f"潮流前线家居", f"品质生活馆", f"全球好货精选",
                    f"品牌工厂直销", f"正品惠民店", f"尚品宅配官方",
                    f"聚划算特卖店"
                ]
                seller = random.choice(seller_names)
                gradients = CATEGORY_GRADIENTS[cat]
                image_url = f"https://via.placeholder.com/300x300/{gradients[0]}/{gradients[1]}/text/{name[:6]}"
                image_url = image_url.replace(" ", "%20")
                trend_score = round(random.uniform(50, 100), 1)
                fee_rate = PLATFORM_FEE[platform]
                profit_margin = round((1 - fee_rate - 0.1) * 100, 1)  # 假设10%其他成本
                url = f"https://www.{platform}.com/product/{pid}"
                created_at = (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
                
                products.append((
                    pid, name, platform, cat, price, original_price,
                    sales_count, rating, seller, url, image_url,
                    trend_score, profit_margin, created_at
                ))
                pid += 1
        # 确保每平台50条
        while len([p for p in products if p[2] == platform]) < 50:
            if pid > 300:
                break
            cat = random.choice(CATEGORIES)
            templates = PRODUCT_TEMPLATES[cat]
            name = random.choice(templates) + f" 特惠款"
            lo, hi = (50, 800)
            price = round(random.uniform(lo, hi), 1)
            original_price = round(price * random.uniform(1.1, 1.5), 1)
            sales_count = random.randint(100, 50000)
            rating = round(random.uniform(4.2, 5.0), 1)
            seller = random.choice(["特惠工厂店", "折扣专区", "品牌特卖"])
            gradients = CATEGORY_GRADIENTS[cat]
            image_url = f"https://via.placeholder.com/300x300/{gradients[0]}/{gradients[1]}/text/Sale"
            trend_score = round(random.uniform(50, 100), 1)
            fee_rate = PLATFORM_FEE[platform]
            profit_margin = round((1 - fee_rate - 0.1) * 100, 1)
            url = f"https://www.{platform}.com/product/{pid}"
            created_at = (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
            products.append((
                pid, name, platform, cat, price, original_price,
                sales_count, rating, seller, url, image_url,
                trend_score, profit_margin, created_at
            ))
            pid += 1
    
    return products[:300]


def init_seed_data(db_path=None):
    """初始化种子数据"""
    if db_path is None:
        db_path = DB_PATH
    db_path = os.path.abspath(db_path)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 创建表
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            platform TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            original_price REAL,
            sales_count INTEGER DEFAULT 0,
            rating REAL DEFAULT 5.0,
            seller TEXT,
            url TEXT,
            image_url TEXT,
            trend_score REAL DEFAULT 0,
            profit_margin REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            session_id TEXT DEFAULT 'default',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            ua TEXT,
            path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 检查是否已有数据
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        products = generate_products()
        c.executemany("""
            INSERT INTO products (id, name, platform, category, price, original_price,
                sales_count, rating, seller, url, image_url, trend_score, profit_margin, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, products)
        print(f"已插入 {len(products)} 条种子数据")
    else:
        print("数据库已有数据，跳过种子数据插入")
    
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_seed_data()
