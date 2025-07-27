import os
import asyncio
import logging
import aiohttp
from bs4 import BeautifulSoup
from telegram import Bot
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")  # مثال: @Predictmista

HEADERS = {"User-Agent": "Mozilla/5.0"}
bot = Bot(token=BOT_TOKEN)
sent_matches = set()
logging.basicConfig(level=logging.INFO)

async def fetch(session, url):
    try:
        async with session.get(url, headers=HEADERS, timeout=10) as response:
            return await response.text()
    except Exception as e:
        logging.error(f"خطأ في جلب {url}: {e}")
        return ""

async def parse_forebet(session):
    url = "https://www.forebet.com/en/football-tips/double-chance"
    html = await fetch(session, url)
    soup = BeautifulSoup(html, "html.parser")
    results = []
    matches = soup.select(".rcnt")[:10]
    for match in matches:
        try:
            team1 = match.select_one(".homeTeam").text.strip()
            team2 = match.select_one(".awayTeam").text.strip()
            pred = match.select_one(".tipsx").text.strip()
            key = f"Forebet|{team1} vs {team2}"
            results.append((key, f"🔵 Forebet\n{team1} vs {team2}\nتوقع: {pred}"))
        except:
            continue
    return results

async def parse_betensured(session):
    url = "https://www.betensured.com/predictions/2x"
    html = await fetch(session, url)
    soup = BeautifulSoup(html, "html.parser")
    results = []
    rows = soup.select("table tr")[1:10]
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 3:
            match = cols[0].text.strip()
            pred = cols[2].text.strip()
            key = f"Betensured|{match}"
            results.append((key, f"🟢 Betensured\n{match}\nتوقع: {pred}"))
    return results

async def parse_predictz(session):
    url = "https://www.predictz.com/predictions/doublechance/"
    html = await fetch(session, url)
    soup = BeautifulSoup(html, "html.parser")
    results = []
    rows = soup.select(".pred-row")[:10]
    for row in rows:
        try:
            teams = row.select_one(".pred-fixture").text.strip()
            pred = row.select_one(".pred-tip").text.strip()
            key = f"PredictZ|{teams}"
            results.append((key, f"🟣 PredictZ\n{teams}\nتوقع: {pred}"))
        except:
            continue
    return results

async def check_new_predictions():
    global sent_matches
    async with aiohttp.ClientSession() as session:
        tasks = await asyncio.gather(
            parse_forebet(session),
            parse_betensured(session),
            parse_predictz(session)
        )
        new_messages = []
        for site_results in tasks:
            for key, message in site_results:
                if key not in sent_matches:
                    sent_matches.add(key)
                    new_messages.append(message)

        for msg in new_messages:
            try:
                await bot.send_message(chat_id=CHANNEL_USERNAME, text=msg)
                logging.info(f"📤 أُرسلت: {msg.splitlines()[0]}")
                await asyncio.sleep(1)
            except Exception as e:
                logging.error(f"❌ فشل إرسال: {e}")

async def run_forever():
    while True:
        logging.info(f"🔁 تحقق جديد: {datetime.utcnow().strftime('%H:%M:%S')}")
        await check_new_predictions()
        await asyncio.sleep(600)  # كل 10 دقائق

if __name__ == "__main__":
    asyncio.run(run_forever())
