import discord
from discord.ext import tasks
import random
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import asyncio
import os
intents = discord.Intents.default()
intents.messages = True

TOKEN = #Discord Token
GUILD_ID = #Server ID
CHANNEL_ID = #Channel ID
client = discord.Client(intents=intents)

conferences = [
    "SODA", "FOCS", "CCC", "CRYPTO", "STOC", "COLT"
]

conference_years = {
    "SODA": list(range(1990, 2025)),
    "COLT": list(range(1988, 2024)),
    "STOC": list(range(1969, 2024)),
    "FOCS": list(range(1960, 2024)),
    "CCC": list(range(1986, 2024)),
    "CRYPTO": list(range(1981, 2024))
}

conference_urls = {
    "SODA": "https://dblp.org/db/conf/soda/soda{year}.html",
    "COLT": "https://dblp.org/db/conf/colt/colt{year}.html",
    "STOC": "https://dblp.org/db/conf/stoc/stoc{year}.html",
    "FOCS": "https://dblp.org/db/conf/focs/focs{year}.html",
    "CCC": "https://dblp.org/db/conf/coco/coco{year}.html",
    "CRYPTO": "https://dblp.org/db/conf/crypto/crypto{year}-1.html"
}

current_conference_index = 0
LAST_SENT_FILE = 'last_sent.json'

def get_random_paper(conference):
    year = random.choice(conference_years[conference])
    if conference != "COLT" and year < 2000:
        url_year = f"{str(year)[-2:]}"
    else:
        url_year = f"{year}"
    url = conference_urls[conference].format(year=url_year)

    if conference == "CRYPTO":
        part = random.choice(range(1, 6))
        url = url.replace("-1.html", f"-{part}.html")

    print(f"Fetching papers from URL: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    papers = soup.find_all('li', class_='entry')
    if not papers:
        print("No papers found, trying again.")
        return get_random_paper(conference)

    paper = random.choice(papers)
    title = paper.find('span', class_='title').text
    authors = ', '.join([author.text for author in paper.find_all('span', itemprop='author')])

    print(f"Selected Paper: {title}, Authors: {authors}")

    return {
        "title": title,
        "conference": conference,
        "authors": authors
    }

def load_last_sent():
    if os.path.exists(LAST_SENT_FILE):
        with open(LAST_SENT_FILE, 'r') as file:
            return json.load(file)
    return None

def save_last_sent(conference):
    last_sent = {
        'conference': conference,
        'timestamp': datetime.utcnow().isoformat()
    }
    with open(LAST_SENT_FILE, 'w') as file:
        json.dump(last_sent, file)

async def send_paper():
    global current_conference_index
    last_sent = load_last_sent()
    if last_sent:
        last_timestamp = datetime.fromisoformat(last_sent['timestamp'])
        time_since_last_sent = datetime.utcnow() - last_timestamp
        if time_since_last_sent < timedelta(hours=24):
            time_until_next_send = timedelta(hours=24) - time_since_last_sent
            print(f"Less than 24 hours since the last paper was sent. Sleeping for {time_until_next_send}.")
            await asyncio.sleep(time_until_next_send.total_seconds())

    conference = conferences[current_conference_index]
    paper = get_random_paper(conference)

    embed = discord.Embed(
        title=paper['title'],
        description=f"**Authors:** {paper['authors']}\n**Conference:** {paper['conference']}",
        color=discord.Color.blue()
    )

    channel = client.get_guild(GUILD_ID).get_channel(CHANNEL_ID)
    await channel.send(embed=embed)
    await channel.send(f"<@161658823948369921>, here is a paper for you from {paper['conference']}")

    print(f"Sent paper: {paper['title']}")

    save_last_sent(conference)
    current_conference_index = (current_conference_index + 1) % len(conferences)

    # Schedule next paper send in 24 hours
    print("Scheduling next paper send in 24 hours.")
    await asyncio.sleep(86400)
    await send_paper()

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await send_paper()

client.run(TOKEN)