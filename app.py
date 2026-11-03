
import math, sqlite3, json
from datetime import datetime, date, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
import plotly.express as px

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "bet_intelligence.db"
OPENLIGADB = "https://api.openligadb.de"
ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
# Compétitions suivies automatiquement : principaux championnats nationaux et coupes.
ESPN_LEAGUES = {
    "Premier League": "eng.1", "Championship": "eng.2", "FA Cup": "eng.fa",
    "La Liga": "esp.1", "La Liga 2": "esp.2", "Copa del Rey": "esp.copa_del_rey",
    "Bundesliga": "ger.1", "2. Bundesliga": "ger.2", "DFB-Pokal": "ger.dfb_pokal",
    "Serie A": "ita.1", "Serie B": "ita.2", "Coppa Italia": "ita.coppa_italia",
    "Ligue 1": "fra.1", "Ligue 2": "fra.2", "Coupe de France": "fra.coupe_de_france",
    "Eredivisie": "ned.1", "Liga Portugal": "por.1",
    "Belgian Pro League": "bel.1", "Scottish Premiership": "sco.1", "Turkish Super Lig": "tur.1",
    "Greek Super League": "gre.1", "Swiss Super League": "sui.1", "Austrian Bundesliga": "aut.1",
    "Danish Superliga": "den.1", "Norwegian Eliteserien": "nor.1", "Swedish Allsvenskan": "swe.1",
    "MLS": "usa.1", "Liga MX": "mex.1", "Brasileirao": "bra.1", "Primera Argentina": "arg.1",
    "Saudi Pro League": "ksa.1", "J1 League": "jpn.1", "K League 1": "kor.1",
    "UEFA Champions League": "uefa.champions", "UEFA Europa League": "uefa.europa",
    "UEFA Conference League": "uefa.europa.conf", "Copa Libertadores": "conmebol.libertadores",
    "CAF Champions League": "caf.champions", "FIFA World Cup": "fifa.world",
    "NWSL (féminin)": "usa.nwsl", "UEFA Women Champions League": "uefa.wchampions",
}

LEAGUES = {
    "Bundesliga (Allemagne)": "bl1",
    "2. Bundesliga (Allemagne)": "bl2",
    "Premier League (Angleterre)": "pl",
    "La Liga (Espagne)": "pd",
    "Serie A (Italie)": "sa",
    "Ligue 1 (France)": "l1",
    "Ligue des champions": "ucl",
}

st.set_page_config(page_title="BET INTELLIGENCE AI", page_icon="⚽", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;600;700;800&family=Inter:wght@400;500;600;700;800&display=swap');
:root{--bg:#070b16;--panel:rgba(15,24,43,.82);--line:rgba(65,219,255,.22);--cyan:#35e7ff;--violet:#9b75ff;--green:#5dffbd;--muted:#9eacc5}
.stApp{background:radial-gradient(ellipse at 15% 0%,rgba(30,104,160,.22),transparent 36%),radial-gradient(ellipse at 90% 10%,rgba(117,55,190,.18),transparent 32%),linear-gradient(145deg,#070b16 0%,#0a1020 55%,#080b17 100%);color:#edf5ff;font-family:'Inter',sans-serif}
.block-container{max-width:1500px;padding-top:2rem;padding-bottom:3rem}
h1,h2,h3{font-family:'Orbitron','Inter',sans-serif!important;letter-spacing:.3px}
h1{color:#f4fbff!important;text-shadow:0 0 22px rgba(53,231,255,.18)}
h2,h3{color:#dcecff!important}
p, label, .stMarkdown{color:#d5e2f4}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0c1426 0%,#090e1c 100%);border-right:1px solid var(--line)}
[data-testid="stSidebar"] h1{font-size:1.12rem!important;color:var(--cyan)!important}
[data-testid="stMetric"]{background:linear-gradient(145deg,rgba(19,35,59,.94),rgba(12,20,37,.9));border:1px solid var(--line);padding:17px 18px;border-radius:16px;box-shadow:0 8px 28px rgba(0,0,0,.22),inset 0 1px rgba(255,255,255,.04)}
[data-testid="stMetricLabel"]{color:#9fb5d1!important;font-weight:600}
[data-testid="stMetricValue"]{color:#f4fbff!important;font-family:'Orbitron',sans-serif}
div.stButton>button,div.stDownloadButton>button{border:1px solid rgba(53,231,255,.55);border-radius:11px;background:linear-gradient(100deg,rgba(28,135,174,.28),rgba(111,74,191,.28));color:#eafaff;font-weight:800;min-height:2.8rem;box-shadow:0 0 18px rgba(53,231,255,.08);transition:.2s}
div.stButton>button:hover,div.stDownloadButton>button:hover{border-color:var(--cyan);box-shadow:0 0 22px rgba(53,231,255,.24);color:white;transform:translateY(-1px)}
.stTextInput input,.stNumberInput input,.stSelectbox div[data-baseweb="select"]>div,.stMultiSelect div[data-baseweb="select"]>div{background:#0d1729!important;color:#f3f8ff!important;border:1px solid rgba(105,143,190,.3)!important;border-radius:10px!important}
[data-testid="stDataFrame"],[data-testid="stTable"]{border:1px solid var(--line);border-radius:13px;overflow:hidden}
hr{border-color:rgba(80,150,200,.2)!important}
.small-muted{color:var(--muted);font-size:.88rem}
.badge{display:inline-block;padding:7px 13px;border-radius:30px;background:rgba(35,255,184,.09);border:1px solid rgba(93,255,189,.38);color:var(--green);font-size:.78rem;font-weight:800;letter-spacing:1px;text-transform:uppercase}
.hero-panel{padding:26px 28px;border:1px solid rgba(53,231,255,.28);border-radius:20px;background:linear-gradient(115deg,rgba(14,42,65,.88),rgba(29,20,57,.82));box-shadow:0 14px 40px rgba(0,0,0,.25),inset 0 1px rgba(255,255,255,.05);margin-bottom:22px}
.hero-kicker{font-family:'Orbitron',sans-serif;color:var(--cyan);font-size:.72rem;letter-spacing:2px;text-transform:uppercase}
.hero-title{font-family:'Orbitron',sans-serif;font-size:clamp(1.35rem,3vw,2.3rem);font-weight:800;color:#f4fbff;margin:8px 0;text-shadow:0 0 24px rgba(53,231,255,.25)}
.hero-sub{color:#aebed5;font-size:.96rem}
.section-tag{color:var(--cyan);font-family:'Orbitron',sans-serif;font-size:.72rem;letter-spacing:1.5px;text-transform:uppercase}
.stAlert{border-radius:12px}
</style>
""", unsafe_allow_html=True)

def db():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.execute("""CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, league TEXT,
        home TEXT, away TEXT, p_home REAL, p_draw REAL, p_away REAL,
        predicted_score TEXT, over25 REAL, btts REAL, odds_home REAL,
        odds_draw REAL, odds_away REAL, actual_result TEXT, notes TEXT
    )""")
    con.commit()
    return con

def poisson(k, lam):
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

def dc_matrix(lh, la, rho=-0.08, max_goals=10):
    # Dixon-Coles low-score adjustment; probabilities normalized afterwards.
    matrix = []
    for h in range(max_goals + 1):
        row = []
        for a in range(max_goals + 1):
            p = poisson(h, lh) * poisson(a, la)
            if h == 0 and a == 0:
                tau = 1 - (lh * la * rho)
            elif h == 0 and a == 1:
                tau = 1 + (lh * rho)
            elif h == 1 and a == 0:
                tau = 1 + (la * rho)
            elif h == 1 and a == 1:
                tau = 1 - rho
            else:
                tau = 1
            row.append(max(0.0, p * tau))
        matrix.append(row)
    total = sum(sum(r) for r in matrix)
    return [[x / total for x in r] for r in matrix]

def metrics(lh, la):
    m = dc_matrix(lh, la)
    ph = sum(m[h][a] for h in range(len(m)) for a in range(len(m)) if h > a)
    pd = sum(m[h][a] for h in range(len(m)) for a in range(len(m)) if h == a)
    pa = 1 - ph - pd
    over25 = sum(m[h][a] for h in range(len(m)) for a in range(len(m)) if h + a >= 3)
    btts = sum(m[h][a] for h in range(len(m)) for a in range(len(m)) if h > 0 and a > 0)
    score = max(((m[h][a], h, a) for h in range(len(m)) for a in range(len(m))), key=lambda x:x[0])
    # Asian handicap home -0.5 equals home win; home +0.5 equals home win or draw.
    return {
        "home": ph, "draw": pd, "away": pa, "over25": over25, "under25": 1-over25,
        "btts": btts, "no_btts": 1-btts, "score": f"{score[1]}–{score[2]}",
        "score_prob": score[0], "matrix": m,
        "over15": sum(m[h][a] for h in range(11) for a in range(11) if h+a>=2),
        "over35": sum(m[h][a] for h in range(11) for a in range(11) if h+a>=4),
        "home_ah_m05": ph, "home_ah_p05": ph+pd,
        "away_ah_m05": pa, "away_ah_p05": pa+pd,
    }

def fair_odds(p):
    return (1/p) if p and p > 0 else None

def value_edge(p, odds):
    if odds is None or odds <= 1 or p <= 0: return None
    return p * odds - 1

def load_openligadb(league_code, season):
    url = f"{OPENLIGADB}/getmatchdata/{league_code}/{season}"
    r = requests.get(url, timeout=12, headers={"User-Agent":"BetIntelligenceAI/1.0"})
    r.raise_for_status()
    data = r.json()
    rows = []
    for m in data:
        teams = m.get("team1",{}), m.get("team2",{})
        home, away = teams[0].get("teamName","Domicile"), teams[1].get("teamName","Extérieur")
        results = m.get("matchResults",[])
        final = next((x for x in results if x.get("resultTypeID") == 2), None)
        if final is None and results:
            final = results[-1]
        rows.append({
            "Date": m.get("matchDateTimeUTC") or m.get("matchDateTime"),
            "Domicile": home, "Extérieur": away,
            "Buts domicile": final.get("pointsTeam1") if final else None,
            "Buts extérieur": final.get("pointsTeam2") if final else None,
            "Terminé": bool(final),
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=900, show_spinner=False)
def fetch_espn_competition(label, slug, start_day, end_day):
    """Récupère le calendrier d'une compétition via le scoreboard public ESPN."""
    url = f"{ESPN_BASE}/{slug}/scoreboard"
    params = {"dates": f"{start_day}-{end_day}", "limit": 500}
    response = requests.get(url, params=params, timeout=18, headers={"User-Agent": "Mozilla/5.0 BET-INTELLIGENCE-AI"})
    response.raise_for_status()
    payload = response.json()
    rows = []
    for event in payload.get("events", []):
        competitions = event.get("competitions", [])
        comp = competitions[0] if competitions else {}
        competitors = comp.get("competitors", [])
        home = next((x for x in competitors if x.get("homeAway") == "home"), None)
        away = next((x for x in competitors if x.get("homeAway") == "away"), None)
        if not home and len(competitors) > 0: home = competitors[0]
        if not away and len(competitors) > 1: away = competitors[1]
        if not home or not away: continue
        status = event.get("status", {}).get("type", {})
        state = status.get("state", "")
        completed = bool(status.get("completed", False))
        def score(team):
            value = team.get("score")
            try: return float(value) if value not in (None, "") else None
            except (TypeError, ValueError): return None
        rows.append({
            "Date": event.get("date"),
            "Domicile": home.get("team", {}).get("displayName", "Équipe domicile"),
            "Extérieur": away.get("team", {}).get("displayName", "Équipe extérieure"),
            "Buts domicile": score(home), "Buts extérieur": score(away),
            "Terminé": completed, "Championnat": label,
            "Statut": status.get("shortDetail") or status.get("description") or state or "Programmé",
            "ID_match": event.get("id", ""),
        })
    return rows

@st.cache_data(ttl=900, show_spinner=False)
def load_all_upcoming_matches(days_ahead=10):
    """Charge automatiquement les affiches de nombreuses compétitions, puis les trie par horaire."""
    today = date.today()
    start_day = today.strftime("%Y%m%d")
    end_day = (today + timedelta(days=days_ahead)).strftime("%Y%m%d")
    all_rows, errors = [], []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(fetch_espn_competition, name, slug, start_day, end_day): name
                   for name, slug in ESPN_LEAGUES.items()}
        for future in as_completed(futures):
            name = futures[future]
            try: all_rows.extend(future.result())
            except Exception as exc: errors.append(f"{name}: {str(exc)[:100]}")
    if not all_rows:
        return pd.DataFrame(columns=["Date","Domicile","Extérieur","Buts domicile","Buts extérieur","Terminé","Championnat","Statut","ID_match"]), errors
    frame = pd.DataFrame(all_rows).drop_duplicates(subset=["ID_match"])
    frame["Date tri"] = pd.to_datetime(frame["Date"], utc=True, errors="coerce")
    # Garder les matchs en direct et ceux à venir ; retirer les rencontres terminées.
    now = datetime.now(timezone.utc)
    frame = frame[(~frame["Terminé"].astype(bool)) & (frame["Date tri"] >= now - timedelta(hours=4))]
    frame = frame.sort_values("Date tri").drop(columns=["Date tri"])
    return frame.reset_index(drop=True), errors

def team_rates(df, home, away):
    played = df[df["Terminé"] == True].copy()
    if played.empty:
        return None
    played["Buts domicile"] = pd.to_numeric(played["Buts domicile"], errors="coerce")
    played["Buts extérieur"] = pd.to_numeric(played["Buts extérieur"], errors="coerce")
    played = played.dropna(subset=["Buts domicile","Buts extérieur"])
    if len(played) < 8:
        return None
    league_home = max(0.2, played["Buts domicile"].mean())
    league_away = max(0.2, played["Buts extérieur"].mean())
    league_total = max(0.4, (league_home + league_away)/2)
    def stats(team):
        h = played[played["Domicile"] == team]
        a = played[played["Extérieur"] == team]
        gf = (h["Buts domicile"].sum() + a["Buts extérieur"].sum())
        ga = (h["Buts extérieur"].sum() + a["Buts domicile"].sum())
        n = len(h) + len(a)
        if n == 0: return (1.0,1.0)
        return (max(.35, gf/n/league_total), max(.35, ga/n/league_total))
    ha, hd = stats(home)
    aa, ad = stats(away)
    # Home advantage from the league's observed home/away scoring ratio.
    home_adv = league_home / max(.2, league_away)
    lam_home = max(.15, league_home * ha * ad)
    lam_away = max(.15, league_away * aa * hd / max(.75, home_adv**0.25))
    return lam_home, lam_away

def upcoming_rows(df):
    if df.empty: return df
    return df[df["Terminé"] != True].copy()

def fmt_pct(x): return f"{x*100:.1f}%"

with st.sidebar:
    st.title("⚽ BET INTELLIGENCE AI")
    st.caption("Analyse statistique • Dixon–Coles / Poisson")
    page = st.radio("Navigation", ["Tableau de bord", "Analyser un match", "Historique & résultats", "Guide"])
    st.divider()
    st.caption("FREE EDITION • Aucune clé API obligatoire")

if "matches" not in st.session_state:
    st.session_state.matches = pd.DataFrame()
if "league_label" not in st.session_state:
    st.session_state.league_label = "Toutes les compétitions"
if "fixtures_loaded" not in st.session_state:
    with st.spinner("Chargement automatique des rencontres de football…"):
        auto_df, auto_errors = load_all_upcoming_matches()
        st.session_state.matches = auto_df
        st.session_state.fixture_errors = auto_errors
        st.session_state.fixtures_loaded = True

if page == "Tableau de bord":
    st.markdown('<div class="hero-panel"><div class="hero-kicker">Football intelligence system • Live fixtures</div><div class="hero-title">BET INTELLIGENCE AI</div><div class="hero-sub">Votre centre de commandement football : calendrier mondial, analyses probabilistes et suivi des pronostics.</div><br><span class="badge">● SYSTÈME OPÉRATIONNEL</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-tag">01 / Vue stratégique</div>', unsafe_allow_html=True)
    st.write("Les rencontres se chargent automatiquement à l’ouverture. Sélectionnez une affiche pour lancer son analyse.")
    c1,c2,c3 = st.columns(3)
    con = db()
    saved = pd.read_sql_query("SELECT * FROM predictions ORDER BY id DESC", con)
    c1.metric("Pronostics enregistrés", len(saved))
    c2.metric("Analyses aujourd'hui", int((saved["created_at"].str[:10] == date.today().isoformat()).sum()) if not saved.empty else 0)
    c3.metric("Calendrier", "Automatique / gratuit")
    st.subheader("Calendrier automatique — tous les championnats suivis")
    refresh_col, info_col = st.columns([1, 3])
    if refresh_col.button("🔄 Actualiser les matchs", use_container_width=True):
        load_all_upcoming_matches.clear()
        fetch_espn_competition.clear()
        with st.spinner("Mise à jour des calendriers…"):
            auto_df, auto_errors = load_all_upcoming_matches()
            st.session_state.matches = auto_df
            st.session_state.fixture_errors = auto_errors
    info_col.caption("Les rencontres sont récupérées automatiquement à l'ouverture, classées de la plus proche à la plus éloignée. Actualisation du cache toutes les 15 minutes.")
    uploaded = st.file_uploader("Importer un historique CSV (facultatif, pour affiner les statistiques)", type=["csv"])
    if uploaded:
        try:
            historical = pd.read_csv(uploaded)
            required = {"Domicile","Extérieur","Buts domicile","Buts extérieur"}
            if not required.issubset(historical.columns):
                st.error("Colonnes requises : Domicile, Extérieur, Buts domicile, Buts extérieur.")
            else:
                if "Terminé" not in historical.columns:
                    historical["Terminé"] = historical["Buts domicile"].notna() & historical["Buts extérieur"].notna()
                st.session_state.history = historical
                st.success(f"{len(historical)} lignes historiques importées.")
        except Exception as e:
            st.error(f"Lecture CSV impossible : {e}")
    if st.session_state.get("fixture_errors"):
        st.caption(f"Certaines compétitions n'ont pas répondu ({len(st.session_state.fixture_errors)}). Les autres calendriers restent affichés.")

    if not st.session_state.matches.empty:
        df = st.session_state.matches
        st.subheader("Prochains matchs — triés par heure de coup d'envoi")
        display = df.copy()
        if "Date" in display.columns:
            display["Date"] = pd.to_datetime(display["Date"], utc=True, errors="coerce").dt.tz_convert("Africa/Douala").dt.strftime("%d/%m/%Y %H:%M")
        st.dataframe(display, use_container_width=True, hide_index=True, height=520)
        st.success(f"{len(df)} rencontres à venir chargées automatiquement depuis {df['Championnat'].nunique() if 'Championnat' in df.columns else 0} compétitions.")

elif page == "Analyser un match":
    st.markdown('<div class="hero-panel"><div class="hero-kicker">Prediction lab • Statistical engine</div><div class="hero-title">ANALYSE DE MATCH</div><div class="hero-sub">Modélisation Poisson / Dixon–Coles, marchés de buts et probabilités 1N2.</div></div>', unsafe_allow_html=True)
    df = st.session_state.matches
    home = away = None
    league = "Toutes les compétitions"
    if not df.empty:
        options = [f"{pd.to_datetime(r['Date'], utc=True).tz_convert('Africa/Douala').strftime('%d/%m %H:%M')} | {r.get('Championnat','')} | {r['Domicile']} — {r['Extérieur']}" for _,r in df.iterrows()]
        choice = st.selectbox("Choisir un match (liste automatiquement classée par proximité)", options)
        row = df.iloc[options.index(choice)]
        home, away = str(row["Domicile"]), str(row["Extérieur"])
        league = str(row.get("Championnat", "Toutes les compétitions"))
    else:
        st.warning("Aucune rencontre n'a été renvoyée par les sources gratuites pour le moment. Actualisez le tableau de bord ou utilisez la saisie manuelle.")
    x,y = st.columns(2)
    home = x.text_input("Équipe à domicile", value=home or "")
    away = y.text_input("Équipe à l'extérieur", value=away or "")
    st.caption("Les équipes du match sont préremplies automatiquement. L'import d'un historique CSV reste facultatif et sert uniquement à affiner les estimations.")
    history_df = st.session_state.get("history", pd.DataFrame())
    mode = st.radio("Source des paramètres", ["Calcul depuis l'historique chargé", "Saisie manuelle des buts attendus"], horizontal=True)
    if mode == "Calcul depuis l'historique chargé":
        rates = team_rates(history_df, home, away) if not history_df.empty and home and away else None
        if rates:
            lh,la = rates
            st.success(f"Paramètres estimés sur {int((df['Terminé']==True).sum())} matchs terminés.")
        else:
            st.warning("Aucun historique CSV suffisant n'est importé. Des valeurs de départ sont proposées automatiquement ; ajustez-les si vous disposez de statistiques fiables.")
            lh,la = 1.45,1.10
    else:
        lh,la = 1.45,1.10
    if mode == "Saisie manuelle des buts attendus":
        p,q = st.columns(2)
        lh = p.number_input("xG domicile estimé", .1, 5.0, 1.45, .05)
        la = q.number_input("xG extérieur estimé", .1, 5.0, 1.10, .05)
    odds_on = st.checkbox("J'ai les cotes du bookmaker (pour calculer la value)")
    odds = [None,None,None]
    if odds_on:
        o1,o2,o3 = st.columns(3)
        odds = [o1.number_input("Cote 1",1.01,100.0,2.0,.01),o2.number_input("Cote N",1.01,100.0,3.2,.01),o3.number_input("Cote 2",1.01,100.0,3.8,.01)]
    if st.button("LANCER L'ANALYSE", type="primary", use_container_width=True):
        if not home.strip() or not away.strip() or home.strip().lower()==away.strip().lower():
            st.error("Indiquez deux équipes différentes.")
        else:
            res = metrics(float(lh),float(la))
            st.session_state.last_analysis = (home,away,league,res,odds,float(lh),float(la))
    if "last_analysis" in st.session_state:
        home,away,league,res,odds,lh,la = st.session_state.last_analysis
        st.divider()
        st.subheader(f"{home}  VS  {away}")
        st.caption(f"Buts attendus estimés : {home} {lh:.2f} — {away} {la:.2f}")
        c1,c2,c3 = st.columns(3)
        c1.metric("Victoire domicile",fmt_pct(res["home"]))
        c2.metric("Match nul",fmt_pct(res["draw"]))
        c3.metric("Victoire extérieur",fmt_pct(res["away"]))
        st.subheader("Marchés de buts")
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("Over 1.5",fmt_pct(res["over15"]))
        m2.metric("Over 2.5",fmt_pct(res["over25"]))
        m3.metric("Over 3.5",fmt_pct(res["over35"]))
        m4.metric("BTTS — Oui",fmt_pct(res["btts"]))
        st.subheader("Handicap asiatique — probabilités indicatives")
        h1,h2,h3,h4 = st.columns(4)
        h1.metric(f"{home} -0.5",fmt_pct(res["home_ah_m05"]))
        h2.metric(f"{home} +0.5",fmt_pct(res["home_ah_p05"]))
        h3.metric(f"{away} -0.5",fmt_pct(res["away_ah_m05"]))
        h4.metric(f"{away} +0.5",fmt_pct(res["away_ah_p05"]))
        st.subheader("Score exact le plus probable")
        s1,s2 = st.columns(2)
        s1.metric("Score modal",res["score"])
        s2.metric("Probabilité du score",fmt_pct(res["score_prob"]))
        chart = pd.DataFrame({"Issue":[home,"Nul",away],"Probabilité":[res["home"],res["draw"],res["away"]]})
        st.plotly_chart(px.bar(chart,x="Issue",y="Probabilité",text=chart["Probabilité"].map(fmt_pct),title="Probabilités 1X2"),use_container_width=True)
        if odds_on:
            st.subheader("Détection de value bet")
            rows=[]
            for label,p,odd in zip([home,"Nul",away],[res["home"],res["draw"],res["away"]],odds):
                edge=value_edge(p,odd)
                rows.append({"Marché":label,"Probabilité modèle":fmt_pct(p),"Cote":odd,"Cote juste":round(fair_odds(p),2),"Value estimée":f"{edge*100:+.1f}%" if edge is not None else "—","Signal":"Value potentielle" if edge is not None and edge>=.03 else "Pas de value claire"})
            st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
            st.caption("La value est calculée par p × cote − 1. Elle ne garantit ni gain ni rentabilité.")
        if st.button("Enregistrer ce pronostic"):
            con=db()
            con.execute("""INSERT INTO predictions(created_at,league,home,away,p_home,p_draw,p_away,predicted_score,over25,btts,odds_home,odds_draw,odds_away)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",(datetime.now().isoformat(timespec="seconds"),league,home,away,res["home"],res["draw"],res["away"],res["score"],res["over25"],res["btts"],*odds))
            con.commit()
            st.success("Pronostic enregistré dans l'historique local.")

elif page == "Historique & résultats":
    st.markdown('<div class="hero-panel"><div class="hero-kicker">Performance tracking</div><div class="hero-title">HISTORIQUE & RÉSULTATS</div><div class="hero-sub">Mesurez vos analyses dans le temps et confrontez les prévisions aux résultats réels.</div></div>', unsafe_allow_html=True)
    con=db()
    data=pd.read_sql_query("SELECT * FROM predictions ORDER BY id DESC",con)
    if data.empty:
        st.info("Aucun pronostic enregistré. Analysez un match puis cliquez sur « Enregistrer ce pronostic ».")
    else:
        st.dataframe(data[["created_at","league","home","away","predicted_score","p_home","p_draw","p_away","actual_result"]],use_container_width=True,hide_index=True)
        st.download_button("Télécharger l'historique CSV",data.to_csv(index=False).encode("utf-8"),"historique_pronostics.csv","text/csv")
        st.subheader("Saisir le résultat réel")
        ids=data["id"].tolist()
        selected=st.selectbox("Pronostic",ids,format_func=lambda i: f"#{i} — {data.loc[data.id==i,'home'].iloc[0]} vs {data.loc[data.id==i,'away'].iloc[0]}")
        result=st.selectbox("Résultat final",["1","N","2"])
        if st.button("Mettre à jour le résultat"):
            con.execute("UPDATE predictions SET actual_result=? WHERE id=?",(result,int(selected)))
            con.commit()
            st.success("Résultat enregistré.")
        evaluated=data.dropna(subset=["actual_result"])
        if not evaluated.empty:
            correct=((evaluated["p_home"]>=evaluated["p_draw"]) & (evaluated["p_home"]>=evaluated["p_away"]) & (evaluated["actual_result"]=="1")) | ((evaluated["p_draw"]>evaluated["p_home"]) & (evaluated["p_draw"]>=evaluated["p_away"]) & (evaluated["actual_result"]=="N")) | ((evaluated["p_away"]>evaluated["p_home"]) & (evaluated["p_away"]>evaluated["p_draw"]) & (evaluated["actual_result"]=="2"))
            st.metric("Taux de réussite 1X2 sur les résultats saisis",f"{correct.mean()*100:.1f}%",f"{len(evaluated)} matchs évalués")

else:
    st.markdown('<div class="hero-panel"><div class="hero-kicker">System documentation</div><div class="hero-title">CENTRE D’AIDE</div><div class="hero-sub">Comprendre les outils, les données et les limites du moteur de pronostics.</div></div>', unsafe_allow_html=True)
    st.markdown("""
    ### 1. Charger des rencontres
    Depuis le tableau de bord, choisissez un championnat et une saison. La connexion OpenLigaDB est gratuite et ne demande pas de clé API. Vous pouvez aussi importer un CSV.

    ### 2. Préparer les données
    Pour estimer les forces des équipes, importez un historique comportant les colonnes `Domicile`, `Extérieur`, `Buts domicile`, `Buts extérieur`. Ajoutez `Terminé` (True/False) si vous le souhaitez.

    ### 3. Analyser
    Sélectionnez deux équipes, utilisez l'historique ou saisissez les buts attendus. Le moteur calcule 1X2, scores, Over/Under, BTTS et lignes de handicap indicatives.

    ### 4. Value betting
    Saisissez les cotes 1/N/2 pour comparer la probabilité du modèle à la cote proposée. Une value positive est un écart mathématique potentiel, pas une garantie.

    ### 5. Sauvegarder
    Enregistrez les analyses et ajoutez les résultats réels pour suivre la performance. Les données sont conservées dans la base SQLite locale du déploiement.

    **Limites importantes :** le modèle n'est pas une IA qui connaît l'avenir. La précision dépend de la qualité et de la quantité des données. Les blessures, compositions, suspensions, météo et mouvements de cotes ne sont pas automatiquement intégrés. Ne misez jamais de l'argent nécessaire à vos besoins.
    """)
    st.download_button("Télécharger un modèle CSV", "Domicile,Extérieur,Buts domicile,Buts extérieur,Terminé\nEquipe A,Equipe B,2,1,True\nEquipe B,Equipe C,0,0,True\nEquipe C,Equipe A,1,2,True\n".encode("utf-8"), "modele_historique.csv", "text/csv")

st.markdown("---")
st.markdown('<p class="small-muted">BET INTELLIGENCE AI • Outil d’aide à l’analyse statistique • Les probabilités ne constituent pas une garantie de gain.</p>', unsafe_allow_html=True)
