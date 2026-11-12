# OduwaCoin Social Posts

Automated daily Instagram content for [@oduwacoin](https://www.instagram.com/oduwacoin/): one image (1080x1350) and one Reel (1080x1920, 12s) per day.

Themes rotate daily across staking pool promos, OduwaPay and gift vouchers, education and news, and OWC price updates. OWC prices come only from CoinGecko (`ids=oduwa-coin`).

Media in `media/YYYY-MM-DD/` is served through GitHub Pages so Instagram's Graph API can fetch it.

```bash
python3 generate.py --date 2026-11-12          # renders image.jpg, reel.mp4, meta.json
pplx credentials run <graph handle> -- python3 publish.py --date 2026-11-12
```

Fonts: Montserrat and Lato (SIL Open Font License, see `fonts/`).
