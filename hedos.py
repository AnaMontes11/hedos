"""
Hedos — hedonic scorer for Spanish RSS feeds
Uses AFINN traducido al español (lexico_afinn.en.es.csv)
Requires: pip3 install feedparser requests
"""

import feedparser
import re
import csv
from datetime import datetime

# ── RSS FEEDS ──────────────────────────────────────────────────────────────
FEEDS = [
    ("BBC Mundo",     "https://feeds.bbci.co.uk/mundo/rss.xml"),
    ("El País",       "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada"),
    ("La Vanguardia", "https://www.lavanguardia.com/rss/home.xml"),
]

# ── LOAD LEXICON ───────────────────────────────────────────────────────────
def load_lexicon(path="afinn_es.csv"):
    """Parse AFINN ES csv and return {word: score} dict (-5 to +5)."""
    lexicon = {}
    try:
        with open(path, encoding="latin-1") as f:
            reader = csv.DictReader(f)
            for row in reader:
                word  = row["Palabra"].lower().strip()
                score = row["Puntuacion"].strip()
                if word and score:
                    try:
                        lexicon[word] = int(score)
                    except ValueError:
                        pass
        print(f"  Loaded {len(lexicon)} words from AFINN-ES")
    except FileNotFoundError:
        print("  afinn_es.csv not found")
    return lexicon

# ── TEXT UTILS ─────────────────────────────────────────────────────────────
def tokenize(text):
    text = text.lower()
    text = re.sub(r"[^a-záéíóúüñ\s]", " ", text)
    return [w.strip() for w in text.split() if len(w.strip()) > 2]

def score_text(tokens, lexicon):
    scored = [(w, lexicon[w]) for w in tokens if w in lexicon]
    if not scored:
        return None, []
    mean = sum(s for _, s in scored) / len(scored)
    # Convert -5/+5 to hedonic 1-9 scale
    hedonic = 5 + mean * 0.8
    return round(hedonic, 2), scored

# ── FETCH FEEDS ────────────────────────────────────────────────────────────
def fetch_all(feeds):
    articles = []
    for name, url in feeds:
        print(f"  Fetching {name}...")
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title   = entry.get("title", "")
                summary = entry.get("summary", "")
                text    = title + " " + summary
                articles.append((name, title[:60], text))
        except Exception as e:
            print(f"    Error: {e}")
    print(f"  Fetched {len(articles)} articles total\n")
    return articles

# ── MAIN ───────────────────────────────────────────────────────────────────
def main():
    print("\n── Hedos ─────────────────────────────────────────────────")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    print("Loading lexicon...")
    lexicon = load_lexicon()
    if not lexicon:
        return

    print("\nFetching feeds...")
    articles = fetch_all(FEEDS)

    print("Scoring...\n")

    all_scored = []
    all_words  = {}
    per_source = {}

    for source, title, text in articles:
        tokens = tokenize(text)
        score, matched = score_text(tokens, lexicon)
        if score:
            all_scored.append(score)
            per_source.setdefault(source, []).append(score)
            for w, s in matched:
                all_words[w] = s
            print(f"  [{source}]")
            print(f"  {title[:55]}")
            words_str = ", ".join(f"{w}({s:+d})" for w, s in matched[:4])
            print(f"  palabras: {words_str}")
            print(f"  → {score:.2f} / 9.0\n")

    if not all_scored:
        print("No scores computed — check feeds and lexicon.")
        return

    global_score = sum(all_scored) / len(all_scored)

    sorted_words = sorted(all_words.items(), key=lambda x: x[1])
    top_neg = sorted_words[:6]
    top_pos = sorted_words[-6:][::-1]

    print("─" * 56)
    print(f"  GLOBAL HEDONIC SCORE : {global_score:.2f} / 9.0")
    print(f"  Articles scored      : {len(all_scored)}")
    print(f"  Unique words matched : {len(all_words)}")
    print("─" * 56)

    print("\n  Palabras más negativas hoy:")
    for w, s in top_neg:
        bar = "█" * abs(s)
        print(f"    {w:<22} {s:+d}  {bar}")

    print("\n  Palabras más positivas hoy:")
    for w, s in top_pos:
        bar = "█" * abs(s)
        print(f"    {w:<22} {s:+d}  {bar}")

    print("\n  Por fuente:")
    for source, scores in per_source.items():
        avg = sum(scores) / len(scores)
        bar = "█" * int(avg)
        print(f"    {source:<20} {avg:.2f}  {bar}")

    print("\n── done ──────────────────────────────────────────────────\n")

if __name__ == "__main__":
    main()