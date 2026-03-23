"""
Hedos — hedonic scorer for Spanish RSS feeds
Outputs data.json for the frontend
Requires: pip3 install feedparser requests
"""

import feedparser
import re
import csv
import json
import os
from datetime import datetime, timezone

FEEDS = [
    # España — centro / izquierda
    ("El País",           "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada"),
    ("elDiario.es",       "https://www.eldiario.es/rss/"),
    ("Público",           "https://www.publico.es/rss/"),
    # España — centro / derecha
    ("El Mundo",          "https://e00-elmundo.uecdn.es/elmundo/rss/portada.xml"),
    ("ABC",               "https://www.abc.es/rss/feeds/abc_EspanaEspana.xml"),
    ("El Confidencial",   "https://rss.elconfidencial.com/espana/"),
    # España — autogestionados / alternativos
    ("El Salto",          "https://www.elsaltodiario.com/rss"),
    ("Diagonal",          "https://www.diagonalperiodico.net/rss.xml"),
    # España — libertario / liberal
    ("Libre Mercado",     "https://www.libremercado.com/rss/"),
    # Internacional — neutrales
    ("BBC Mundo",         "https://feeds.bbci.co.uk/mundo/rss.xml"),
    ("DW Español",        "https://rss.dw.com/rdf/rss-es-all"),
    ("France 24 ES",      "https://www.france24.com/es/rss"),
    # Latinoamérica — mainstream
    ("Infobae",           "https://www.infobae.com/feeds/rss/"),
    ("La Nación AR",      "https://www.lanacion.com.ar/arc/outboundfeeds/rss/"),
    ("El Universal MX",   "https://www.eluniversal.com.mx/rss.xml"),
    ("La Jornada MX",     "https://www.jornada.com.mx/rss/edicion.xml"),
    ("El Tiempo CO",      "https://www.eltiempo.com/rss/portada.xml"),
    # Latinoamérica — alternativos / comunitarios
    ("Desinformémonos",   "https://desinformemonos.org/feed/"),
    ("Resumen Latinoam.", "https://www.resumenlatinoamericano.org/feed/"),
]

def load_lexicon(path="afinn_es.csv"):
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
    except FileNotFoundError:
        print("afinn_es.csv not found")
    return lexicon

def tokenize(text):
    text = text.lower()
    text = re.sub(r"[^a-záéíóúüñ\s]", " ", text)
    return [w.strip() for w in text.split() if len(w.strip()) > 2]

def score_text(tokens, lexicon):
    scored = [(w, lexicon[w]) for w in tokens if w in lexicon]
    if not scored:
        return None, []
    mean = sum(s for _, s in scored) / len(scored)
    hedonic = 5 + mean * 0.8
    return round(hedonic, 2), scored

def fetch_all(feeds):
    articles = []
    for name, url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title   = entry.get("title", "")
                summary = entry.get("summary", "")
                text    = title + " " + summary
                articles.append((name, title[:80], text))
        except Exception as e:
            print(f"Error fetching {name}: {e}")
    return articles

def main():
    now = datetime.now(timezone.utc)
    print(f"── Hedos {now.strftime('%Y-%m-%d %H:%M UTC')} ──")

    lexicon = load_lexicon()
    if not lexicon:
        return

    articles = fetch_all(FEEDS)
    all_scored  = []
    all_words   = {}
    per_source  = {}
    scored_articles = []

    for source, title, text in articles:
        tokens = tokenize(text)
        score, matched = score_text(tokens, lexicon)
        if score:
            all_scored.append(score)
            per_source.setdefault(source, []).append(score)
            for w, s in matched:
                all_words[w] = s
            scored_articles.append({
                "source": source,
                "title": title,
                "score": score,
                "words": [{"word": w, "score": s} for w, s in matched[:5]]
            })

    if not all_scored:
        print("No scores computed.")
        return

    global_score = round(sum(all_scored) / len(all_scored), 2)

    sorted_words = sorted(all_words.items(), key=lambda x: x[1])
    top_neg = [{"word": w, "score": s} for w, s in sorted_words[:8]]
    top_pos = [{"word": w, "score": s} for w, s in sorted_words[-8:][::-1]]

    source_avgs = {
        source: round(sum(scores) / len(scores), 2)
        for source, scores in per_source.items()
    }

    # Load existing history or start fresh
    history_path = "data.json"
    history = []
    if os.path.exists(history_path):
        with open(history_path, encoding="utf-8") as f:
            try:
                existing = json.load(f)
                history = existing.get("history", [])
            except Exception:
                history = []

    # Keep last 168 entries (7 days × 24 hours)
    history.append({
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "score": global_score
    })
    history = history[-168:]

    output = {
        "generated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "global_score": global_score,
        "articles_scored": len(all_scored),
        "words_matched": len(all_words),
        "top_negative": top_neg,
        "top_positive": top_pos,
        "per_source": source_avgs,
        "articles": scored_articles[:15],
        "history": history
    }

    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Global score: {global_score} / 9.0")
    print(f"Articles: {len(all_scored)} · Words: {len(all_words)}")
    print(f"Saved to {history_path}")

if __name__ == "__main__":
    main()
