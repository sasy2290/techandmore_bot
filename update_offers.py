import os
import time
import json
import feedparser
import requests
from github import Github

# ===== CONFIGURAZIONE =====
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER", "sasy2290")
REPO_NAME = os.getenv("REPO_NAME", "techandmore_bot")
RSS_FEED = os.getenv("RSS_FEED", "https://rss.app/feeds/kyCtM9o7gYBH76ia.xml")
AFFILIATE_TAG = os.getenv("AFFILIATE_TAG", "techandmore05-21")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL", "@techandmore")

SENT_FILE = "sent_offers.json"  # file locale per evitare duplicati

# ===== FUNZIONE: LEGGE RSS =====
def generate_offers_from_rss():
    print("🔄 Leggo feed RSS...")
    feed = feedparser.parse(RSS_FEED)
    offers = []

    for entry in feed.entries:
        title = entry.title
        link = entry.link
        image = ""
        price = ""
        discount = ""

        # immagine
        if "media_content" in entry and len(entry.media_content) > 0:
            image = entry.media_content[0].get("url", "")

        # aggiungi tag affiliato
        if "tag=" not in link:
            link += ("&" if "?" in link else "?") + f"tag={AFFILIATE_TAG}"

        offer = {
            "title": title.strip(),
            "price": price,
            "discount": discount,
            "image": image,
            "url": link
        }
        offers.append(offer)

    return offers


# ===== FUNZIONE: INVIA A TELEGRAM =====
def send_to_telegram(offer):
    try:
        text = f"🔥 <b>{offer['title']}</b>\n💸 <i>{offer['price']}</i>\n👉 <a href='{offer['url']}'>Acquista su Amazon</a>"
        payload = {
            "chat_id": TELEGRAM_CHANNEL,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data=payload
        )
        if response.status_code == 200:
            print(f"✅ Inviata su Telegram: {offer['title']}")
        else:
            print(f"⚠️ Errore Telegram ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ Errore invio Telegram: {e}")


# ===== FUNZIONE: AGGIORNA GITHUB =====
def update_github_file(content):
    print("📤 Aggiorno offers.json su GitHub...")
    g = Github(GITHUB_TOKEN)
    repo = g.get_user(REPO_OWNER).get_repo(REPO_NAME)

    try:
        file = repo.get_contents("offers.json")
        repo.update_file(
            path=file.path,
            message="🤖 Aggiornamento automatico offerte TechAndMore",
            content=json.dumps(content, indent=2, ensure_ascii=False),
            sha=file.sha
        )
        print("✅ File aggiornato su GitHub!")
    except Exception:
        repo.create_file(
            path="offers.json",
            message="🆕 Creazione iniziale file offerte",
            content=json.dumps(content, indent=2, ensure_ascii=False)
        )
        print("🆕 File offers.json creato su GitHub!")


# ===== FUNZIONE: SALVA / CARICA OFFERTE GIÀ INVIATE =====
def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_sent(sent):
    with open(SENT_FILE, "w", encoding="utf-8") as f:
        json.dump(sent, f, indent=2, ensure_ascii=False)


# ===== CICLO PRINCIPALE =====
def main():
    sent_offers = load_sent()

    while True:
        try:
            offers = generate_offers_from_rss()
            new_offers = []

            for offer in offers:
                if offer["title"] not in sent_offers:
                    new_offers.append(offer)
                    sent_offers.append(offer["title"])
                    send_to_telegram(offer)

            if new_offers:
                update_github_file(offers)
                save_sent(sent_offers)
                print(f"✅ {len(new_offers)} nuove offerte aggiunte e inviate!")
            else:
                print("ℹ️ Nessuna nuova offerta trovata.")

        except Exception as e:
            print(f"❌ Errore generale: {e}")

        print("⏳ Attendo 15 minuti prima del prossimo aggiornamento...\n")
        time.sleep(15 * 60)


if __name__ == "__main__":
    main()
