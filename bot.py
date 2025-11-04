import os, asyncio, random
from telegram import Bot
from flask import Flask
from threading import Thread

app = Flask(__name__)
@app.get("/")
def home():
    return "TechAndMore Bot running (PA-API)"
def keep_alive():
    t = Thread(target=lambda: app.run(host="0.0.0.0", port=8080))
    t.daemon = True
    t.start()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@amazontechandmore")
POST_INTERVAL_HOURS = float(os.getenv("POST_INTERVAL_HOURS", 0.25))
MIN_DISCOUNT = int(os.getenv("MIN_DISCOUNT", 25))
CATEGORIES = os.getenv("CATEGORIES", "informatica,elettronica,smart home").split(",")
PAAPI_ACCESS_KEY = os.getenv("PAAPI_ACCESS_KEY", "")
PAAPI_SECRET_KEY = os.getenv("PAAPI_SECRET_KEY", "")
PAAPI_HOST = os.getenv("PAAPI_HOST", "webservices.amazon.it")
PAAPI_REGION = os.getenv("PAAPI_REGION", "eu-west-1")
PARTNER_TAG = os.getenv("PARTNER_TAG", "techandmor03f-21")
PARTNER_TYPE = os.getenv("PARTNER_TYPE", "Associates")

if not all([BOT_TOKEN, PAAPI_ACCESS_KEY, PAAPI_SECRET_KEY, PARTNER_TAG]):
    raise RuntimeError("Mancano segreti richiesti.")

bot = Bot(token=BOT_TOKEN)

import paapi5_python_sdk as paapi
from paapi5_python_sdk.api.default_api import DefaultApi
from paapi5_python_sdk.models.search_items_request import SearchItemsRequest
from paapi5_python_sdk.models.search_items_resource import SearchItemsResource

def init_paapi_client():
    config = paapi.Configuration(
        access_key=PAAPI_ACCESS_KEY,
        secret_key=PAAPI_SECRET_KEY,
        host=PAAPI_HOST,
        region=PAAPI_REGION,
    )
    return DefaultApi(paapi.ApiClient(config))
paapi_client = init_paapi_client()

def make_search_request(keywords, page=1, items_per_page=8):
    return SearchItemsRequest(
        partner_tag=PARTNER_TAG,
        partner_type=PARTNER_TYPE,
        marketplace="www.amazon.it",
        keywords=keywords,
        item_count=items_per_page,
        item_page=page,
        resources=[
            SearchItemsResource.ITEMINFO_TITLE,
            SearchItemsResource.OFFERS_LISTINGS_PRICE,
            SearchItemsResource.OFFERS_LISTINGS_SAVINGS,
            SearchItemsResource.IMAGES_PRIMARY_MEDIUM,
            SearchItemsResource.DETAILSPAGE_URL,
        ],
    )

def get_amazon_offers():
    offers = []
    keyword_pool = ["SSD NVMe","monitor 27","router wifi 6","webcam","powerbank","mouse gaming"]
    for kw in random.sample(keyword_pool, k=3):
        try:
            req = make_search_request(kw, page=1, items_per_page=6)
            res = paapi_client.search_items(req)
            if not res.search_result or not res.search_result.items: continue
            for it in res.search_result.items:
                title = it.item_info.title.display_value if it.item_info and it.item_info.title else "Prodotto"
                url = it.detail_page_url or ""
                price = None; discount_pct = 0
                if it.offers and it.offers.listings:
                    listing = it.offers.listings[0]
                    if listing.price and listing.price.display_amount:
                        price = listing.price.display_amount
                    if listing.savings and listing.savings.percentage:
                        discount_pct = int(listing.savings.percentage)
                if discount_pct and discount_pct < MIN_DISCOUNT: continue
                offers.append({
                    "title": title,
                    "price": price or "Vedi link",
                    "discount": discount_pct,
                    "url": url,
                    "image": (it.images.primary.medium.url if it.images and it.images.primary and it.images.primary.medium else None)
                })
        except Exception as e:
            print("[PA-API] Errore:", e)
    return offers[:4]

async def post_offer_async(o: dict):
    msg = f"💥 <b>{o['title']}</b>\n💸 <b>Prezzo:</b> {o['price']}"
    if o.get('discount'): msg += f" (-{o['discount']}%)"
    msg += f"\n🔗 <a href='{o['url']}'>Acquista su Amazon</a>"
    await bot.send_message(chat_id=CHANNEL_ID, text=msg, parse_mode="HTML")

async def loop_worker():
    print(f"🤖 TechAndMore Bot avviato. Frequenza: {POST_INTERVAL_HOURS} ore")
    while True:
        items = get_amazon_offers()
        for it in items:
            try:
                await post_offer_async(it)
                await asyncio.sleep(random.randint(8,15))
            except Exception as e:
                print("[Telegram] Errore invio:", e)
        print(f"[TechAndMore] Ciclo completato. Attesa {int(POST_INTERVAL_HOURS*60)} minuti...")
        await asyncio.sleep(int(POST_INTERVAL_HOURS*3600))

async def main_async():
    keep_alive()
    await loop_worker()
if __name__ == "__main__":
    asyncio.run(main_async())
