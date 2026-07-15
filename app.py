# -*- coding: utf-8 -*-
"""SG选品助手 v1.0.0 - 多平台智能选品工具"""
import os, json, sqlite3, csv, io, time, random, hashlib
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import FastAPI, Request, Query, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).parent
DB_PATH = BASE / "data" / "selector.db"
STATIC_DIR = BASE / "static"
VERSION = "1.0.0"

app = FastAPI(title="SG选品助手", version=VERSION, docs_url="/docs", redoc_url="/redoc")

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, platform TEXT, category TEXT,
        price REAL, original_price REAL, sales_count INTEGER,
        rating REAL, seller TEXT, url TEXT, image_url TEXT,
        trend_score REAL, profit_margin REAL, created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS favorites(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER, session_id TEXT, created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS visitors(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT, ua TEXT, path TEXT, created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS price_history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER, price REAL, date TEXT
    )""")
    r = c.execute("SELECT COUNT(*) FROM products").fetchone()
    if r[0] == 0:
        seed_products(c)
    conn.commit()
    conn.close()

PLATFORMS = ["淘宝","京东","拼多多","闲鱼","1688","抖音电商"]
CATEGORIES = ["电子数码","服装鞋帽","家居生活","食品零食","美妆个护","手机数码","母婴用品","运动户外"]
PLATFORM_FEES = {"淘宝":0.03,"京东":0.05,"拼多多":0.02,"闲鱼":0.01,"1688":0.005,"抖音电商":0.05}

PRODUCT_TEMPLATES = {
    "电子数码": ["小米Redmi Note 13 Pro 5G手机","华为FreeBuds Pro 3无线耳机","罗技G304无线鼠标","小米手环8 Pro","联想ThinkPad E14笔记本","JBL Flip 6蓝牙音箱","ANKER 65W氮化镓充电器","小米电视6 55寸4K","大疆Mini 3航拍无人机","索尼WH-1000XM5头戴耳机"],
    "服装鞋帽": ["南极人男士纯棉T恤","优衣库AIRism速干衣","李宁运动短裤","安踏跑步鞋男","波司登羽绒服","海澜之家商务衬衫","回力帆布鞋","蕉内凉感内裤","太平鸟卫衣","斯凯奇老爹鞋"],
    "家居生活": ["小米米家空气净化器4","美的电饭煲4L","南极人四件套","茶花收纳箱","九阳破壁机","小米智能台灯","飞利浦电动牙刷","苏泊尔不粘锅","米家扫地机器人","南极人记忆枕"],
    "食品零食": ["三只松鼠坚果礼盒","百草味肉脯","良品铺子零食大礼包","元气森林气泡水","螺霸王螺蛳粉","王小卤卤味","认养一头牛纯牛奶","钟薛高冰淇淋","周黑鸭鸭脖","好欢螺螺蛳粉"],
    "美妆个护": ["完美日记口红","花西子散粉","珀莱雅精华液","欧莱雅面膜","自然堂水乳套装","colorkey唇釉","薇诺娜防晒霜","橘朵眼影盘","百雀羚面霜","韩束红胶囊精华"],
    "手机数码": ["iPhone 15 Pro Max 256G","iPad Air 5 64G","Apple Watch S9","三星Galaxy S24 Ultra","一加12 16+512","realme GT5 Pro","iQOO 12 Pro","魅族21 Note","努比亚Z60 Ultra","Redmi K70 Pro"],
    "母婴用品": ["帮宝适纸尿裤L码","飞鹤星飞帆奶粉","babycare湿巾","好孩子婴儿车","布鲁可大颗粒积木","贝亲奶瓶","安儿宝辅食碗","子初婴儿面霜","可优比睡袋","费雪摇铃"],
    "运动户外": ["李宁羽毛球拍","迪卡侬瑜伽垫","Keep跳绳","阿迪达斯足球","探路者登山包","骆驼冲锋衣","匹克态极跑鞋","尤尼克斯网球拍","北面帐篷","挪客睡袋"],
}

SELLERS = ["官方旗舰店","品牌直销","源头工厂","专营店","正品保障","工厂直供","品牌授权店","精选好店","优质卖家","实力商家"]

def seed_products(c):
    pid = 1
    for plat in PLATFORMS:
        for cat in CATEGORIES:
            names = PRODUCT_TEMPLATES[cat]
            for i in range(6):
                name = names[i % len(names)]
                if i >= len(names):
                    name = f"{name} {random.choice(['2024新款','升级版','套装','优惠装','礼盒装','官方标配'])}"
                base_price = random.randint(15, 1800)
                if plat in ("闲鱼","1688"):
                    base_price = int(base_price * 0.65)
                elif plat in ("京东","抖音电商"):
                    base_price = int(base_price * 1.1)
                orig_price = int(base_price * random.uniform(1.1, 1.5))
                sales = random.randint(50, 50000)
                if plat == "闲鱼":
                    sales = random.randint(5, 2000)
                rating = round(random.uniform(4.2, 4.9), 1)
                seller = random.choice(SELLERS)
                trend = round(random.uniform(30, 98), 1)
                profit = round(random.uniform(8, 45), 1)
                url = f"https://example.com/{plat}/{pid}"
                img = f"https://picsum.photos/seed/p{pid}/300/300"
                created = (datetime.now() - timedelta(days=random.randint(0,60))).isoformat()
                c.execute("INSERT INTO products(name,platform,category,price,original_price,sales_count,rating,seller,url,image_url,trend_score,profit_margin,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (name,plat,cat,base_price,orig_price,sales,rating,seller,url,img,trend,profit,created))
                for d in range(30, 0, -1):
                    p = base_price + random.randint(-50, 50)
                    c.execute("INSERT INTO price_history(product_id,price,date) VALUES(?,?,?)",
                              (pid, p, (datetime.now()-timedelta(days=d)).strftime("%Y-%m-%d")))
                pid += 1

@app.on_event("startup")
def startup():
    init_db()

@app.middleware("http")
async def track(request: Request, call_next):
    path = request.url.path
    if not path.startswith("/api") and not path.startswith("/static") and not path.startswith("/admin"):
        try:
            conn = get_db()
            conn.execute("INSERT INTO visitors(ip,ua,path,created_at) VALUES(?,?,?,?)",
                         (request.client.host, request.headers.get("user-agent","")[:200], path, datetime.now().isoformat()))
            conn.commit()
            conn.close()
        except: pass
    return await call_next(request)

@app.get("/", response_class=HTMLResponse)
def index():
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)

@app.get("/api/v1/health")
def health():
    return {"status":"ok","version":VERSION,"timestamp":datetime.now().isoformat()}

@app.get("/api/v1/stats")
def stats():
    conn = get_db()
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    fav_count = c.execute("SELECT COUNT(*) FROM favorites").fetchone()[0]
    visitor_count = c.execute("SELECT COUNT(*) FROM visitors").fetchone()[0]
    plat_counts = {row[0]: row[1] for row in c.execute("SELECT platform,COUNT(*) FROM products GROUP BY platform")}
    cat_counts = {row[0]: row[1] for row in c.execute("SELECT category,COUNT(*) FROM products GROUP BY category")}
    conn.close()
    return {"total_products":total,"favorites":fav_count,"visitors":visitor_count,
            "platforms":plat_counts,"categories":cat_counts,"version":VERSION}

@app.get("/api/v1/platforms")
def platforms():
    return [{"name":p,"fee_rate":PLATFORM_FEES.get(p,0.03)} for p in PLATFORMS]

@app.get("/api/v1/categories")
def categories():
    return CATEGORIES

@app.get("/api/v1/products")
def products(platform: str = Query(""), category: str = Query(""), keyword: str = Query(""),
             sort: str = Query("sales"), page: int = Query(1), page_size: int = Query(20)):
    conn = get_db()
    c = conn.cursor()
    sql = "SELECT * FROM products WHERE 1=1"
    args = []
    if platform: sql += " AND platform=?"; args.append(platform)
    if category: sql += " AND category=?"; args.append(category)
    if keyword: sql += " AND name LIKE ?"; args.append(f"%{keyword}%")
    sort_map = {"price":"price ASC","sales":"sales_count DESC","profit":"profit_margin DESC","trend":"trend_score DESC","rating":"rating DESC"}
    sql += f" ORDER BY {sort_map.get(sort,'sales_count DESC')}"
    total = c.execute(f"SELECT COUNT(*) FROM ({sql})", args).fetchone()[0]
    offset = (page-1)*page_size
    sql += f" LIMIT {page_size} OFFSET {offset}"
    rows = [dict(r) for r in c.execute(sql, args)]
    conn.close()
    return {"items":rows,"total":total,"page":page,"page_size":page_size,"pages":(total+page_size-1)//page_size}

@app.get("/api/v1/products/{pid}")
def product_detail(pid: int):
    conn = get_db()
    c = conn.cursor()
    r = c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    if not r: raise HTTPException(404,"商品不存在")
    history = [dict(h) for h in c.execute("SELECT * FROM price_history WHERE product_id=? ORDER BY date", (pid,))]
    conn.close()
    return {**dict(r), "price_history": history}

@app.get("/api/v1/hot")
def hot(platform: str = Query(""), category: str = Query(""), limit: int = Query(20)):
    conn = get_db()
    c = conn.cursor()
    sql = "SELECT * FROM products WHERE 1=1"
    args = []
    if platform: sql += " AND platform=?"; args.append(platform)
    if category: sql += " AND category=?"; args.append(category)
    sql += " ORDER BY sales_count DESC LIMIT ?"
    args.append(limit)
    rows = [dict(r) for r in c.execute(sql, args)]
    conn.close()
    return {"items": rows}

@app.get("/api/v1/compare")
def compare(keyword: str = Query(...)):
    conn = get_db()
    c = conn.cursor()
    rows = [dict(r) for r in c.execute(
        "SELECT * FROM products WHERE name LIKE ? ORDER BY platform, price", (f"%{keyword}%",))]
    by_plat = {}
    for r in rows:
        p = r["platform"]
        if p not in by_plat: by_plat[p] = []
        by_plat[p].append(r)
    all_prices = [r["price"] for r in rows]
    conn.close()
    return {"keyword":keyword,"results":by_plat,"all_items":rows,
            "min_price":min(all_prices) if all_prices else 0,
            "max_price":max(all_prices) if all_prices else 0,
            "avg_price":round(sum(all_prices)/len(all_prices),2) if all_prices else 0,
            "count":len(rows)}

@app.post("/api/v1/profit")
def profit_calc(data: dict):
    cost = float(data.get("cost_price",0))
    sell = float(data.get("sell_price",0))
    plat = data.get("platform","淘宝")
    fee_rate = PLATFORM_FEES.get(plat, 0.03)
    shipping = float(data.get("shipping_cost",0))
    fee = sell * fee_rate
    gross = sell - cost - fee
    net = gross - shipping
    margin = round(net/sell*100, 1) if sell > 0 else 0
    return {"cost_price":cost,"sell_price":sell,"platform":plat,"fee_rate":fee_rate,
            "platform_fee":round(fee,2),"shipping_cost":shipping,
            "gross_profit":round(gross,2),"net_profit":round(net,2),
            "profit_margin":margin}

@app.get("/api/v1/trends")
def trends(keyword: str = Query(""), days: int = Query(30)):
    conn = get_db()
    c = conn.cursor()
    if keyword:
        row = c.execute("SELECT id,name FROM products WHERE name LIKE ? LIMIT 1", (f"%{keyword}%",)).fetchone()
        if not row:
            conn.close(); return {"keyword":keyword,"history":[],"message":"未找到匹配商品"}
        pid, pname = row[0], row[1]
        history = [dict(h) for h in c.execute(
            "SELECT date,price FROM price_history WHERE product_id=? ORDER BY date LIMIT ?", (pid,days))]
        conn.close()
        return {"keyword":keyword,"product_id":pid,"product_name":pname,"history":history}
    history = []
    base = random.randint(100,500)
    for d in range(days, 0, -1):
        base += random.randint(-20, 20)
        base = max(50, base)
        history.append({"date":(datetime.now()-timedelta(days=d)).strftime("%Y-%m-%d"),"price":base})
    conn.close()
    return {"keyword":keyword or "综合趋势","history":history}

@app.get("/api/v1/favorites")
def get_favorites(session_id: str = Query("default")):
    conn = get_db()
    c = conn.cursor()
    rows = [dict(r) for r in c.execute(
        """SELECT p.*, f.id as fav_id FROM favorites f JOIN products p ON f.product_id=p.id 
        WHERE f.session_id=? ORDER BY f.created_at DESC""", (session_id,))]
    conn.close()
    return {"items": rows}

@app.post("/api/v1/favorites")
def add_favorite(data: dict):
    conn = get_db()
    c = conn.cursor()
    pid = data.get("product_id")
    sid = data.get("session_id","default")
    existing = c.execute("SELECT id FROM favorites WHERE product_id=? AND session_id=?", (pid,sid)).fetchone()
    if existing:
        conn.close(); return {"status":"exists"}
    c.execute("INSERT INTO favorites(product_id,session_id,created_at) VALUES(?,?,?)",
              (pid,sid,datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return {"status":"added"}

@app.delete("/api/v1/favorites/{fav_id}")
def del_favorite(fav_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM favorites WHERE id=?", (fav_id,))
    conn.commit()
    conn.close()
    return {"status":"deleted"}

@app.get("/api/v1/export")
def export_csv(platform: str = Query(""), category: str = Query(""), sort: str = Query("sales")):
    conn = get_db()
    c = conn.cursor()
    sql = "SELECT name,platform,category,price,original_price,sales_count,rating,seller,trend_score,profit_margin FROM products WHERE 1=1"
    args = []
    if platform: sql += " AND platform=?"; args.append(platform)
    if category: sql += " AND category=?"; args.append(category)
    sort_map = {"price":"price ASC","sales":"sales_count DESC","profit":"profit_margin DESC","trend":"trend_score DESC"}
    sql += f" ORDER BY {sort_map.get(sort,'sales_count DESC')}"
    rows = c.execute(sql, args).fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["商品名称","平台","分类","价格","原价","销量","评分","卖家","趋势分","利润率"])
    for r in rows:
        writer.writerow([r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],r[8],r[9]])
    content = output.getvalue()
    return Response(content=content, media_type="text/csv",
                    headers={"Content-Disposition":"attachment; filename=products.csv"})

@app.get("/admin", response_class=HTMLResponse)
def admin():
    html = (STATIC_DIR / "admin.html").read_text(encoding="utf-8")
    return HTMLResponse(html)

@app.get("/api/v1/admin/stats")
def admin_stats():
    conn = get_db()
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    fav = c.execute("SELECT COUNT(*) FROM favorites").fetchone()[0]
    vis = c.execute("SELECT COUNT(*) FROM visitors").fetchone()[0]
    today_vis = c.execute("SELECT COUNT(*) FROM visitors WHERE date(created_at)=date('now')").fetchone()[0]
    plat = {row[0]:row[1] for row in c.execute("SELECT platform,COUNT(*) FROM products GROUP BY platform")}
    conn.close()
    return {"products":total,"favorites":fav,"visitors":vis,"today_visitors":today_vis,"by_platform":plat}

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT",8000)))
