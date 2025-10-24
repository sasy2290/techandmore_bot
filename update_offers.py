import os
import time
import json
import feedparser
from github import Github

# ========== CONFIGURAZIONE ==========
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER", "sasy2290")
REPO_NAME = os.getenv("REPO_NAME", "techandmore_bot")
RSS_FEED = os.getenv("RSS_FEED", "https://rss.app/feeds/kyCtM9o7gYBH76ia.xml")
AFFILIATE_TAG = os.getenv("AFFILIATE_TAG", "techandmore05-21")

# ========== FUNZIONE PRINCIPALE ==========
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

        # estrai immagine se presente
        if "media_content" in entry and len(entry.media_content) > 0:
            image = entry.media_content[0].get("url", "")

        # aggiungi tag affiliato se manca
        if "tag=" not in link:
            if "?" in link:
                link += f"&tag={AFFILIATE_TAG}"
            else:
                link += f"?tag={AFFILIATE_TAG}"

        offer = {
            "title": title,
            "price": price,
            "discount": discount,
            "image": image,
            "url": link
        }
        offers.append(offer)

    return offers

# ========== FUNZIONE AGGIORNA GITHUB ==========
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
        print("✅ File aggiornato con successo!")
    except Exception as e:
        # se non esiste, lo crea
        repo.create_file(
            path="offers.json",
            message="🆕 Creazione file offerte iniziale",
            content=json.dumps(content, indent=2, ensure_ascii=False)
        )
        print("🆕 File offers.json creato!")

# ========== CICLO AUTOMATICO ==========
def main():
    while True:
        try:
            offers = generate_offers_from_rss()
            if offers:
                update_github_file(offers)
            else:
                print("⚠️ Nessuna offerta trovata.")
        except Exception as e:
            print("❌ Errore:", e)

        print("⏳ Attendo 15 minuti prima del prossimo aggiornamento...\n")
        time.sleep(15 * 60)  # 15 minuti

if __name__ == "__main__":
    main()
