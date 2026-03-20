# Hedos — collective mood index

A hedonic thermometer for Spanish-language internet.

Every hour, RSS feeds from BBC Mundo, El País, and La Vanguardia are scanned. Words are matched against the AFINN-ES lexicon and averaged into a single score between 1 (negative) and 9 (positive).

## Live site

Hosted on GitHub Pages: `https://[your-username].github.io/hedos`

## How it works

1. GitHub Actions runs `hedos.py` every hour
2. The script fetches RSS feeds, scores each article, and saves `data.json`
3. `index.html` reads `data.json` and renders the dashboard

## Stack

- Python + feedparser
- AFINN-ES lexicon (2,100+ Spanish words)
- GitHub Actions (free hourly automation)
- GitHub Pages (free hosting)
- Vanilla HTML/CSS/JS

## Known limitations

- Small lexicon (2,100 words) — many articles go unscored
- No context awareness — "guerra" scores −2 regardless of meaning
- Sources are Spain/Latin America focused, not global
- Measures linguistic affect, not lived experience

## Setup

```bash
pip install feedparser requests
curl -L "https://raw.githubusercontent.com/jboscomendoza/rpubs/master/sentimientos_afinn/lexico_afinn.en.es.csv" -o afinn_es.csv
python hedos.py
```

## License

MIT
