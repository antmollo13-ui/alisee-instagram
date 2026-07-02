#!/usr/bin/env python3
"""Genera la caption Instagram dai dati di snapshot.json. Stampa su stdout.
Va eseguito nella cartella dove si trova snapshot.json."""
import json
from datetime import datetime, timedelta

MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]

H_START = 8   # prima ora mostrata nel forecast della giornata
H_END = 20    # ultima ora mostrata


def ore_giorno(forecast, day_str, h_start=H_START, h_end=H_END):
    """Righe orarie diurne di un dato giorno."""
    rows = []
    for r in forecast:
        d = r.get("date", "")
        if not d.startswith(day_str):
            continue
        try:
            hour = int(d[11:13])
        except ValueError:
            continue
        if h_start <= hour <= h_end:
            rows.append(r)
    return rows


def picco(rows):
    """Riga col vento previsto massimo tra quelle passate."""
    best = None
    for r in rows:
        if best is None or r.get("w_ai", 0) > best.get("w_ai", 0):
            best = r
    return best


def main():
    with open("snapshot.json", encoding="utf-8") as f:
        s = json.load(f)

    fc = s.get("forecast", [])
    upd = s.get("updated_at", "")
    today = upd[:10] if upd else (fc[0]["date"][:10] if fc else "")
    try:
        dt = datetime.fromisoformat(today)
        data_it = f"{dt.day} {MESI[dt.month - 1]}"
        tomorrow = (dt + timedelta(days=1)).strftime("%Y-%m-%d")
    except Exception:
        data_it, tomorrow = today, ""

    lines = [f"\U0001F32C️ ISCHITELLA · {data_it}", ""]

    st = s.get("station")
    if st:
        extra = ""
        if st.get("temperature") is not None:
            extra = f" · {round(st['temperature'])}°C"
        lines.append(
            f"Ora: {st['wind_speed']:.1f} kn "
            f"(raffiche {st['wind_gust']:.1f}) da {st['cardinal']}{extra}"
        )

    # forecast orario della giornata
    ore = ore_giorno(fc, today)
    if ore:
        lines.append("")
        lines.append("\U0001F4C5 Previsione di oggi:")
        for r in ore:
            lines.append(f"{r['date'][11:16]} · {round(r['w_ai'])} kn · {r['cardinal']}")

    # sguardo a domani
    if tomorrow:
        pm = picco(ore_giorno(fc, tomorrow))
        if pm:
            lines.append("")
            lines.append(f"Domani: fino a {round(pm['w_ai'])} kn ({pm['cardinal']})")

    m = s.get("metriche", {})
    mae = m.get("mae_oracle")
    if mae:
        line = f"\U0001F4CA Errore medio {mae:.1f} nodi"
        migl = m.get("migl_fin")
        if migl and migl > 0:
            line += f" · −{round(migl)}% vs modello di base"
        lines.append("")
        lines.append(line)

    lines.append("")
    lines.append("Previsioni calibrate sulla stazione a terra di Ischitella · modello ALISEE")
    lines.append("#kitesurf #windsurf #vela #ischitella #vento #meteo #previsionivento")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
