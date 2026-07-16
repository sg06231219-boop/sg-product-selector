# -*- coding: utf-8 -*-
"""SG选品助手 v1.3.0 - 多平台智能选品工具"""
import os, json, sqlite3, csv, io, random
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

BASE = Path(__file__).parent
DB_PATH = BASE / "data" / "selector.db"
STATIC_DIR = BASE / "static"
VERSION = "1.2.0"

app = FastAPI(title="SG选品助手", version=VERSION, docs_url="/docs", redoc_url="/redoc")

# ======== 工具 ========
def ok(data=None, msg="ok"):
    return {"code": 0, "data": data, "msg": msg}

def fail(msg="error", code=1):
    return {"code": code, "data": None, "msg": msg}

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

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

@app.on_event("startup")
def startup():
    init_db()

@app.middleware("http")
async def track(request: Request, call_next):
    path = request.url.path
    if not path.startswith("/api") and not path.startswith("/static"):
        conn = None
        try:
            conn = get_db()
            conn.execute("INSERT INTO visitors(ip,ua,path,created_at) VALUES(?,?,?,?)",
                         (request.client.host, request.headers.get("user-agent","")[:200], path, datetime.now().isoformat()))
            conn.commit()
        except: pass
        finally:
            if conn: conn.close()
    return await call_next(request)

# ======== 页面 ========
@app.get("/", response_class=HTMLResponse)
def index():
    html = (STATIC_DIR / "index.html").read_bytes().decode("utf-8")
    return HTMLResponse(content=html, media_type="text/html; charset=utf-8")

@app.get("/admin", response_class=HTMLResponse)
def admin():
    html = (STATIC_DIR / "admin.html").read_bytes().decode("utf-8")
    return HTMLResponse(content=html, media_type="text/html; charset=utf-8")

@app.get("/admin.html", response_class=HTMLResponse)
def admin_html():
    html = (STATIC_DIR / "admin.html").read_bytes().decode("utf-8")
    return HTMLResponse(content=html, media_type="text/html; charset=utf-8")

# ======== 公共API ========
@app.get("/api/v1/health")
def health():
    return ok({"status":"ok","version":VERSION,"timestamp":datetime.now().isoformat()})

@app.get("/api/v1/stats")
def stats():
    conn = get_db(); c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    fav_count = c.execute("SELECT COUNT(*) FROM favorites").fetchone()[0]
    visitor_count = c.execute("SELECT COUNT(*) FROM visitors").fetchone()[0]
    avg_price = c.execute("SELECT ROUND(AVG(price),1) FROM products").fetchone()[0] or 0
    plat_counts = {row[0]: row[1] for row in c.execute("SELECT platform,COUNT(*) FROM products GROUP BY platform")}
    cat_counts = {row[0]: row[1] for row in c.execute("SELECT category,COUNT(*) FROM products GROUP BY category")}
    conn.close()
    return ok({
        "total_products": total, "favorites": fav_count, "visitors": visitor_count,
        "product_count": total, "favorite_count": fav_count, "visitor_count": visitor_count,
        "avg_price": avg_price,
        "platforms": plat_counts, "categories": cat_counts,
        "platform_stats": plat_counts, "category_stats": cat_counts,
        "version": VERSION
    })

@app.get("/api/v1/platforms")
def platforms():
    return ok([{"name":p,"fee_rate":PLATFORM_FEES.get(p,0.03)} for p in PLATFORMS])

@app.get("/api/v1/categories")
def categories():
    return ok(CATEGORIES)

@app.get("/api/v1/products")
def products(platform: str = Query(""), category: str = Query(""), keyword: str = Query(""),
             sort: str = Query("sales"), page: int = Query(1), page_size: int = Query(20)):
    page_size = min(page_size, 100)  # ??100?/?
    conn = get_db(); c = conn.cursor()
    sql = "SELECT * FROM products WHERE 1=1"
    args = []
    if platform and platform != "全部": sql += " AND platform=?"; args.append(platform)
    if category and category != "全部": sql += " AND category=?"; args.append(category)
    if keyword: sql += " AND name LIKE ?"; args.append(f"%{keyword}%")
    sort_map = {"price":"price ASC","price_desc":"price DESC","sales":"sales_count DESC","profit":"profit_margin DESC","trend":"trend_score DESC","rating":"rating DESC"}
    sql += f" ORDER BY {sort_map.get(sort,'sales_count DESC')}"
    total = c.execute(f"SELECT COUNT(*) FROM ({sql})", args).fetchone()[0]
    offset = (page-1)*page_size
    sql += f" LIMIT {page_size} OFFSET {offset}"
    rows = [dict(r) for r in c.execute(sql, args)]
    conn.close()
    return ok({"list": rows, "total": total, "total_pages": (total+page_size-1)//page_size,
               "page": page, "page_size": page_size})

@app.get("/api/v1/products/{pid}")
def product_detail(pid: int):
    conn = get_db(); c = conn.cursor()
    r = c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    if not r:
        conn.close()
        return fail("商品不存在")
    history = [dict(h) for h in c.execute("SELECT * FROM price_history WHERE product_id=? ORDER BY date", (pid,))]
    conn.close()
    return ok({**dict(r), "price_history": history})

@app.get("/api/v1/hot")
def hot(platform: str = Query(""), category: str = Query(""), limit: int = Query(20)):
    conn = get_db(); c = conn.cursor()
    sql = "SELECT * FROM products WHERE 1=1"
    args = []
    if platform and platform != "全部": sql += " AND platform=?"; args.append(platform)
    if category and category != "全部": sql += " AND category=?"; args.append(category)
    sql += " ORDER BY sales_count DESC LIMIT ?"
    args.append(limit)
    rows = [dict(r) for r in c.execute(sql, args)]
    conn.close()
    # 加 rank 和 trend_direction
    for i, r in enumerate(rows):
        r["rank"] = i + 1
        # ????id?????????
        td = ["up","up","up","flat","down"][r["id"] % 5]
        r["trend_direction"] = td
    return ok(rows)

@app.get("/api/v1/compare")
def compare(keyword: str = Query(...)):
    conn = get_db(); c = conn.cursor()
    rows = [dict(r) for r in c.execute(
        "SELECT * FROM products WHERE name LIKE ? ORDER BY platform, price", (f"%{keyword}%",))]
    if not rows:
        conn.close()
        return ok({"keyword":keyword,"results":[],"all_items":[],"min_price":0,"max_price":0,"avg_price":0,"count":0})
    all_prices = [r["price"] for r in rows]
    min_p = min(all_prices)
    for r in rows:
        r["is_lowest"] = (r["price"] == min_p)
    by_plat = {}
    for r in rows:
        p = r["platform"]
        if p not in by_plat: by_plat[p] = []
        by_plat[p].append(r)
    conn.close()
    return ok({
        "keyword": keyword,
        "results": rows,  # 扁平数组，前端直接遍历
        "by_platform": by_plat,
        "all_items": rows,
        "min_price": min_p,
        "max_price": max(all_prices),
        "avg_price": round(sum(all_prices)/len(all_prices), 2),
        "count": len(rows)
    })

@app.post("/api/v1/profit")
def profit_calc(data: dict):
    cost = float(data.get("cost_price", 0))
    sell = float(data.get("sell_price", 0))
    fee_rate = float(data.get("platform_fee_rate", 0.03))
    shipping = float(data.get("shipping_cost", 0))
    if sell <= 0:
        return fail("售价必须大于0")
    fee = round(sell * fee_rate, 2)
    gross = round(sell - cost - fee, 2)
    net = round(gross - shipping, 2)
    margin = round(net / sell * 100, 1) if sell > 0 else 0
    return ok({
        "cost_price": cost, "sell_price": sell,
        "platform_fee_rate": fee_rate, "platform_fee": fee,
        "shipping_cost": shipping,
        "gross_profit": gross, "net_profit": net,
        "profit_rate": margin, "profit_margin": margin
    })

@app.get("/api/v1/trends")
def trends(keyword: str = Query(""), days: int = Query(30)):
    conn = get_db(); c = conn.cursor()
    price_trend = []
    sales_trend = []
    # ?????hash?????????????????
    import hashlib
    seed = int(hashlib.md5(keyword.encode()).hexdigest()[:8], 16)
    trend_score = round(55 + (seed % 370) / 10, 1)  # 55.0 - 92.0
    if keyword:
        row = c.execute("SELECT id,name FROM products WHERE name LIKE ? LIMIT 1", (f"%{keyword}%",)).fetchone()
        if row:
            pid, pname = row[0], row[1]
            history = [dict(h) for h in c.execute(
                "SELECT date,price FROM price_history WHERE product_id=? ORDER BY date LIMIT ?", (pid, days))]
            price_trend = [{"date": h["date"], "price": h["price"]} for h in history]
            # 生成销量趋势（基于价格反推）
            base_sales = random.randint(100, 2000)
            for h in history:
                base_sales += random.randint(-100, 100)
                base_sales = max(50, base_sales)
                sales_trend.append({"date": h["date"], "sales": base_sales})
        else:
            # 未找到匹配，生成随机趋势
            base_p = random.randint(100, 500)
            base_s = random.randint(200, 1500)
            for d in range(days, 0, -1):
                base_p += random.randint(-15, 15); base_p = max(50, base_p)
                base_s += random.randint(-80, 80); base_s = max(50, base_s)
                dt = (datetime.now()-timedelta(days=d)).strftime("%Y-%m-%d")
                price_trend.append({"date": dt, "price": base_p})
                sales_trend.append({"date": dt, "sales": base_s})
    else:
        base_p = random.randint(100, 500)
        base_s = random.randint(200, 1500)
        for d in range(days, 0, -1):
            base_p += random.randint(-15, 15); base_p = max(50, base_p)
            base_s += random.randint(-80, 80); base_s = max(50, base_s)
            dt = (datetime.now()-timedelta(days=d)).strftime("%Y-%m-%d")
            price_trend.append({"date": dt, "price": base_p})
            sales_trend.append({"date": dt, "sales": base_s})
    conn.close()
    # 计算变化百分比
    if len(price_trend) >= 2:
        price_change_pct = round((price_trend[-1]["price"] - price_trend[0]["price"]) / price_trend[0]["price"] * 100, 1)
        sales_change_pct = round((sales_trend[-1]["sales"] - sales_trend[0]["sales"]) / sales_trend[0]["sales"] * 100, 1)
    else:
        price_change_pct = 0; sales_change_pct = 0
    # 建议
    if trend_score > 75 and sales_change_pct > 0:
        rec = "强烈推荐"
    elif trend_score > 60:
        rec = "值得关注"
    elif trend_score > 45:
        rec = "观望为主"
    else:
        rec = "谨慎入场"
    return ok({
        "keyword": keyword or "综合趋势",
        "trend_score": trend_score,
        "price_change_pct": price_change_pct,
        "sales_change_pct": sales_change_pct,
        "recommendation": rec,
        "price_trend": price_trend,
        "sales_trend": sales_trend,
        "history": price_trend  # 兼容
    })

# ======== 收藏 ========
@app.get("/api/v1/favorites")
def get_favorites(session_id: str = Query("default")):
    conn = get_db(); c = conn.cursor()
    rows = [dict(r) for r in c.execute(
        """SELECT p.*, f.id as fav_id FROM favorites f JOIN products p ON f.product_id=p.id
        WHERE f.session_id=? ORDER BY f.created_at DESC""", (session_id,))]
    conn.close()
    return ok(rows)

@app.post("/api/v1/favorites")
def add_favorite(data: dict):
    conn = get_db(); c = conn.cursor()
    pid = data.get("product_id")
    sid = data.get("session_id", "default")
    existing = c.execute("SELECT id FROM favorites WHERE product_id=? AND session_id=?", (pid, sid)).fetchone()
    if existing:
        conn.close()
        return ok({"status": "exists"})
    c.execute("INSERT INTO favorites(product_id,session_id,created_at) VALUES(?,?,?)",
              (pid, sid, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return ok({"status": "added"})

@app.delete("/api/v1/favorites/{product_id}")
def del_favorite(product_id: int, session_id: str = Query("default")):
    conn = get_db(); c = conn.cursor()
    c.execute("DELETE FROM favorites WHERE product_id=? AND session_id=?", (product_id, session_id))
    conn.commit()
    conn.close()
    return ok({"status": "deleted"})

# ======== 导出 ========
@app.get("/api/v1/export")
def export_csv(platform: str = Query(""), category: str = Query(""), sort: str = Query("sales")):
    conn = get_db(); c = conn.cursor()
    sql = "SELECT name,platform,category,price,original_price,sales_count,rating,seller,trend_score,profit_margin FROM products WHERE 1=1"
    args = []
    if platform and platform != "全部": sql += " AND platform=?"; args.append(platform)
    if category and category != "全部": sql += " AND category=?"; args.append(category)
    sort_map = {"price":"price ASC","sales":"sales_count DESC","profit":"profit_margin DESC","trend":"trend_score DESC"}
    sql += f" ORDER BY {sort_map.get(sort,'sales_count DESC')}"
    rows = c.execute(sql, args).fetchall()
    conn.close()
    output = io.StringIO()
    output.write('\ufeff')  # BOM for Excel
    writer = csv.writer(output)
    writer.writerow(["商品名称","平台","分类","价格","原价","销量","评分","卖家","趋势分","利润率"])
    for r in rows:
        writer.writerow([r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],r[8],r[9]])
    content = output.getvalue()
    return Response(content=content, media_type="text/csv",
                    headers={"Content-Disposition":"attachment; filename=products.csv"})

# ======== 管理后台API ========
# Admin??????ADMIN_TOKEN?????????????
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")

@app.get("/api/v1/admin/stats")
def admin_stats():
    conn = get_db(); c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    fav = c.execute("SELECT COUNT(*) FROM favorites").fetchone()[0]
    vis = c.execute("SELECT COUNT(*) FROM visitors").fetchone()[0]
    today_vis = c.execute("SELECT COUNT(*) FROM visitors WHERE date(created_at)=date('now')").fetchone()[0]
    avg_price = c.execute("SELECT ROUND(AVG(price),1) FROM products").fetchone()[0] or 0
    plat = {row[0]:row[1] for row in c.execute("SELECT platform,COUNT(*) FROM products GROUP BY platform")}
    cat = {row[0]:row[1] for row in c.execute("SELECT category,COUNT(*) FROM products GROUP BY category")}
    conn.close()
    return ok({
        "product_count": total, "favorite_count": fav, "visitor_count": vis,
        "today_visitors": today_vis, "avg_price": avg_price,
        "by_platform": plat, "platform_stats": plat,
        "category_stats": cat
    })

@app.get("/api/v1/admin/products")
def admin_products(page: int = Query(1), page_size: int = Query(20)):
    page_size = min(page_size, 100)  # ??100?/?
    conn = get_db(); c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    offset = (page-1)*page_size
    rows = [dict(r) for r in c.execute(
        "SELECT * FROM products ORDER BY id DESC LIMIT ? OFFSET ?", (page_size, offset))]
    conn.close()
    return ok({"list": rows, "total": total})

@app.get("/api/v1/admin/visitors")
def admin_visitors(page: int = Query(1), page_size: int = Query(20)):
    page_size = min(page_size, 100)  # ??100?/?
    conn = get_db(); c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM visitors").fetchone()[0]
    offset = (page-1)*page_size
    rows = [dict(r) for r in c.execute(
        "SELECT * FROM visitors ORDER BY id DESC LIMIT ? OFFSET ?", (page_size, offset))]
    conn.close()
    return ok({"list": rows, "total": total})

@app.post("/api/v1/admin/products")
def admin_add_product(data: dict):
    conn = get_db(); c = conn.cursor()
    c.execute("""INSERT INTO products(name,platform,category,price,original_price,sales_count,rating,seller,url,image_url,trend_score,profit_margin,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (data.get("name",""), data.get("platform","淘宝"), data.get("category","电子数码"),
         float(data.get("price",0)), float(data.get("original_price",0)),
         int(data.get("sales_count",0)), float(data.get("rating",5.0)),
         data.get("seller",""), data.get("url",""), data.get("image_url",""),
         float(data.get("trend_score",50.0)), float(data.get("profit_margin",20.0)),
         datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return ok({"status": "created"})

@app.put("/api/v1/admin/products/{pid}")
def admin_update_product(pid: int, data: dict):
    conn = get_db(); c = conn.cursor()
    r = c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    if not r:
        conn.close()
        return fail("商品不存在")
    c.execute("""UPDATE products SET name=?,platform=?,category=?,price=?,original_price=?,sales_count=?,rating=?,seller=?,url=? WHERE id=?""",
        (data.get("name",r["name"]), data.get("platform",r["platform"]), data.get("category",r["category"]),
         float(data.get("price",r["price"])), float(data.get("original_price",r["original_price"])),
         int(data.get("sales_count",r["sales_count"])), float(data.get("rating",r["rating"])),
         data.get("seller",r["seller"]), data.get("url",r["url"]), pid))
    conn.commit()
    conn.close()
    return ok({"status": "updated"})

@app.delete("/api/v1/admin/products/{pid}")
def admin_delete_product(pid: int):
    conn = get_db(); c = conn.cursor()
    c.execute("DELETE FROM products WHERE id=?", (pid,))
    c.execute("DELETE FROM price_history WHERE product_id=?", (pid,))
    c.execute("DELETE FROM favorites WHERE product_id=?", (pid,))
    conn.commit()
    conn.close()
    return ok({"status": "deleted"})

# ======== 静态文件 ========
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
