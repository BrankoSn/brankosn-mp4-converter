# Brankosn MP4 Converter

Plak een link van YouTube, TikTok, Instagram (en honderden andere sites) en krijg een gewone `.mp4` (H.264 + AAC) of een MP3. Geen limiet, geen popups, geen account. Alles gebeurt op je eigen pc.

## Hoe het werkt

Een website kan zelf geen video's van andere sites ophalen. Daarom zijn er twee delen:

1. **Het scherm** (`index.html`): staat op GitHub Pages, of draait rechtstreeks vanuit de helper.
2. **De helper** (`server.py`): een klein programma op jouw pc (`127.0.0.1:8765`, alleen van binnenuit je eigen pc bereikbaar) dat [yt-dlp](https://github.com/yt-dlp/yt-dlp) gebruikt.

Het scherm toont rechtsboven of de helper online is.

## Gebruiken op een nieuwe pc

1. Download dit project (groene knop **Code → Download ZIP**) en pak het uit.
2. Dubbelklik **`start-windows.bat`** (Windows) of **`start-mac.command`** (Mac).
   - Python 3 moet geïnstalleerd zijn (https://www.python.org/downloads/, op Windows "Add to PATH" aanvinken).
   - De eerste keer haalt de helper zelf `yt-dlp` en `ffmpeg` op. Daarna wordt `yt-dlp` bij elke start bijgewerkt.
3. Laat dat venster open. Ga naar de GitHub-Pages-link of naar http://127.0.0.1:8765 en download.

Downloads komen in `Downloads/MP4-Downloader` (andere map: zet omgevingsvariabele `DL_OUT`).

## Browsers

- Chrome, Edge, Brave, Firefox: de GitHub-link werkt. Chrome kan één keer vragen of de site toegang tot je lokale netwerk mag krijgen: kies **Toestaan**.
- Safari blokkeert dat soms: open dan http://127.0.0.1:8765 (zelfde scherm).

## Beveiliging

- De helper luistert alleen op `127.0.0.1`.
- Alleen deze herkomsten mogen opdrachten sturen: de helper zelf en `https://brankosn.github.io`. Andere websites krijgen een 403. Eigen Pages-adres? Zet `DL_ORIGINS=https://jouwnaam.github.io`.
- Bestanden openen ("Toon in map") kan alleen binnen de downloadmap.

## Goed om te weten

- Gebruik het alleen voor video's van jezelf of waarvoor je toestemming hebt. De voorwaarden van YouTube, TikTok en Instagram staan downloaden meestal niet toe.
- 4K/1440p bij YouTube is meestal VP9, geen H.264. Het is wel een `.mp4`-bestand en speelt in VLC, Chrome en nieuwere Macs. Wil je maximale compatibiliteit (auto, oudere tv's), kies dan **1080p**: dat is H.264.
- Privé- of leeftijdsbeperkte video's: kies onderaan je browser bij **Browser-login**. De helper leest dan jouw login uit die browser.
- Dit is een nieuw ontwerp. Gaat een site stuk, dan is dat bijna altijd een verouderde yt-dlp: herstart de helper (die werkt zichzelf bij).

## Als app (aanbevolen, helper zit erin)

`dist/Brankosn MP4 Converter.app` (Mac) bevat scherm én helper in één venster: dubbelklik en klaar, geen aparte stap, geen Python nodig.
Bouwen: `python3 -m pip install --user pywebview pyinstaller imageio-ffmpeg`, daarna het PyInstaller-commando in `bouw-app.sh`.
Eerste keer op een andere Mac: rechtsklik op de app, **Open**, bevestig (de app is niet door Apple ondertekend).
Windows-versie (.exe) bouwen kan met dezelfde code, via GitHub Actions of op een Windows-pc (`pyinstaller ... app.py`).

## Downloadmap kiezen

Onderaan staat **Kies map**: kies waar je downloads komen. De keuze wordt onthouden.

## Telefoon-modus (galerij)

Een telefoon kan zelf geen video's ophalen. Daarom bedient je telefoon de laptop via je wifi:
1. Klik op **Telefoon**, zet de modus aan, scan de QR-code met je telefoon (zelfde wifi).
2. Plak een link en download. De laptop haalt de video op.
3. Tik op **BEWAAR**. iPhone: deel-icoon, dan *Bewaar video* (komt in Foto's). Android: komt in je galerij/Downloads.
Beveiliging: aparte poort, alleen apparaten in je eigen netwerk, pincode in de QR (cookie), geen toegang tot mapkiezer/instellingen. Alleen aan als jij het aanzet. Laptop moet aan blijven; buitenshuis kan via een VPN zoals Tailscale.

## Downloaden

- **Mac-app:** zie *Releases* (rechts op de GitHub-pagina), download `Brankosn-MP4-Converter-mac.zip`, pak uit, rechtsklik op de app, **Open**. (Apple Silicon.)
- **Webversie:** https://brankosn.github.io/brankosn-mp4-converter/ (helper moet draaien, zie hierboven).
- **Telefoon:** zie *Telefoon-modus*. Open de link op je telefoon en kies *Zet op beginscherm* voor een app-icoon.
