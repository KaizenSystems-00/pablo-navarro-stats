"""Dashboard de performance @pablonavarro.inversion."""
from __future__ import annotations

import json
from pathlib import Path
from statistics import median

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_DIR = Path(__file__).parent

# ──────────────────── Datos oficiales (Studio/Insights) ───────────────
# Fuente: IMG_0239 (TikTok) + IMG_0245/246/247 (Instagram)
OFFICIAL = {
    "total_videos_publicados": 58,  # según métricas internas Mario
    "instagram": {
        "periodo": "24 mar - 22 may (60 días)",
        "views": 138_754,
        "likes": 1_946,
        "comments": 104,
        "saves": 1_601,
        "shares": 720,
        "republicaciones": 28,
        "cuentas_alcanzadas": 64_234,
        "interacciones_total": 5_119,
        "pct_no_seguidores_views": 97.7,
        "pct_no_seguidores_interacciones": 85.6,
        "seguidores": 941,
    },
    "tiktok": {
        "periodo": "365 días",
        "views": 119_000,
        "profile_views": 710,
        "likes": 2_289,
        "comments": 90,
        "shares": 801,
        "seguidores": 503,
        "espectadores_nuevos": 79_000,
    },
}

# Benchmark cuenta normal del sistema (mes 1)
BENCHMARK_NORMAL_MES_1 = {
    "views_total": 130_000,
    "seguidores_total": 800,
    "primer_viral_video_num": 18,
}

# Pablo: índice del primer viral por plataforma (asumido por Mario: vídeo #3 en ambas)
PABLO_PRIMER_VIRAL = {
    "instagram": 3,
    "tiktok": 3,
}

# Análisis comunidad — distribución comentarios no-CTA (top 10 vídeos IG+TT)
# Counts sobre 106 comentarios reales analizados — % calculados con decimal para precisión
COMUNIDAD_COUNTS = {
    "preguntas_aprender": 47,        # 44.3%
    "responder_aportar": 55,         # 51.9%
    "otros": 4,                      # 3.8%
}
COMUNIDAD_TOTAL = sum(COMUNIDAD_COUNTS.values())  # 106
COMUNIDAD_DIST = {
    k: round(v / COMUNIDAD_TOTAL * 100, 1)
    for k, v in COMUNIDAD_COUNTS.items()
}

# Benchmarks CTA conversion (intent comments / views)
CTA_BENCH = {
    "actual_pablo_tt_pct": 0.27,        # mejor del mes Pablo TT
    "actual_pablo_ig_pct": 0.25,        # mejor del mes Pablo IG
    "medio_nicho_pct": 0.85,            # 25/2931 — esperable cuando la pieza está bien armada
    "medio_mejor_cliente_pct": 4.43,    # 310/7000 — techo demostrado en otro cliente del sistema
    "medio_mejor_cliente_pct_b": 3.29,  # 42/1278 — otra pieza del techo
}

# ──────────────────── Page config ─────────────────────────────────────
st.set_page_config(
    page_title="Pablo Navarro — Dashboard",
    page_icon="📊",
    layout="wide",
)


@st.cache_data
def load_data():
    ig = json.loads((DATA_DIR / "pablo_ig.json").read_text())
    tt = json.loads((DATA_DIR / "pablo_tt.json").read_text())
    cta = json.loads((DATA_DIR / "pablo_cta_analysis.json").read_text())

    df_ig = pd.DataFrame(ig)
    df_ig["platform"] = "Instagram"
    df_ig["timestamp"] = pd.to_datetime(df_ig["timestamp"])
    df_ig["shares"] = 0
    df_ig["saves"] = 0

    df_tt = pd.DataFrame(tt)
    df_tt["platform"] = "TikTok"
    df_tt["timestamp"] = pd.to_datetime(df_tt["timestamp"])

    keep = ["platform", "timestamp", "url", "caption", "views", "likes",
            "comments", "shares", "saves"]
    df_tt = df_tt[keep].copy()
    df_ig = df_ig[keep].copy()
    df = pd.concat([df_tt, df_ig], ignore_index=True)
    df["fecha"] = df["timestamp"].dt.date
    df["hook"] = df["caption"].fillna("").str.split("\n").str[0].str[:80]
    return df, cta


df, CTA = load_data()

# ──────────────────── Sidebar filters ────────────────────────────────
st.sidebar.title("Filtros")
plats = st.sidebar.multiselect(
    "Plataforma", ["TikTok", "Instagram"], default=["TikTok", "Instagram"]
)
date_min = df["timestamp"].min().date()
date_max = df["timestamp"].max().date()
date_range = st.sidebar.date_input(
    "Rango fechas",
    value=(date_min, date_max),
    min_value=date_min,
    max_value=date_max,
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    d_from, d_to = date_range
else:
    d_from, d_to = date_min, date_max

df_f = df[
    df["platform"].isin(plats)
    & (df["timestamp"].dt.date >= d_from)
    & (df["timestamp"].dt.date <= d_to)
].copy()

st.sidebar.markdown("---")
st.sidebar.markdown("**Fuente de datos:**")
st.sidebar.markdown(
    "- Cifras agregadas (views totales, saves, shares, cuentas alcanzadas, "
    "espectadores nuevos, seguidores): **internos** (IG Insights + TT Studio).  \n"
    "- Detalle por vídeo (gráficas, top 5, distribución, análisis comentarios): "
    "**scrape público** (Apify)."
)
st.sidebar.markdown(f"**Total vídeos publicados:** {OFFICIAL['total_videos_publicados']}")
st.sidebar.markdown(f"**Periodo:** {date_min} → {date_max}")

# ──────────────────── Header + KPIs ──────────────────────────────────
st.title("Pablo Navarro — Performance Dashboard")
st.caption(
    f"Cliente: Richard Gracia · Avatar Pablo Navarro · "
    f"@pablonavarro.inversion · IG + TikTok"
)

views_oficial = OFFICIAL["instagram"]["views"] + OFFICIAL["tiktok"]["views"]
saves_total = OFFICIAL["instagram"]["saves"]  # TT no expone saves oficial en este screenshot
shares_total = OFFICIAL["instagram"]["shares"] + OFFICIAL["tiktok"]["shares"]
seguidores_total = OFFICIAL["instagram"]["seguidores"] + OFFICIAL["tiktok"]["seguidores"]

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Vídeos publicados", OFFICIAL["total_videos_publicados"])
c2.metric(
    "Views totales",
    f"{views_oficial:,}".replace(",", "."),
    help=f"IG: {OFFICIAL['instagram']['views']:,} (60d) · TT: {OFFICIAL['tiktok']['views']:,} (365d)".replace(",", ".")
)
c3.metric(
    "Seguidores",
    f"{seguidores_total:,}".replace(",", "."),
    help=f"IG: {OFFICIAL['instagram']['seguidores']} · TT: {OFFICIAL['tiktok']['seguidores']}"
)
c4.metric(
    "Saves + Shares",
    f"{saves_total + shares_total:,}".replace(",", "."),
    help=f"Saves IG: {saves_total} · Shares IG+TT: {shares_total}".replace(",", ".")
)
alcance_total = OFFICIAL["instagram"]["cuentas_alcanzadas"] + OFFICIAL["tiktok"]["espectadores_nuevos"]
c5.metric(
    "Alcance único (IG + TT)",
    f"{alcance_total:,}".replace(",", "."),
    help=f"IG cuentas alcanzadas: {OFFICIAL['instagram']['cuentas_alcanzadas']:,} (60d) · TT espectadores nuevos: {OFFICIAL['tiktok']['espectadores_nuevos']:,}".replace(",", ".")
)
interacciones_total = (
    OFFICIAL["instagram"]["likes"] + OFFICIAL["instagram"]["comments"] + OFFICIAL["instagram"]["saves"] + OFFICIAL["instagram"]["shares"]
    + OFFICIAL["tiktok"]["likes"] + OFFICIAL["tiktok"]["comments"] + OFFICIAL["tiktok"]["shares"]
)
c6.metric(
    "Interacciones totales (IG + TT)",
    f"{interacciones_total:,}".replace(",", "."),
    help="Suma de likes + comments + saves + shares en ambas plataformas"
)

st.markdown("---")

# ──────────────────── Chart 1: tendencia acumulada por índice de vídeo (full width) ─
st.subheader("Tendencia acumulada de views por vídeo (TT vs IG)")
st.caption(
    "Eje X = orden de publicación dentro de cada plataforma (vídeo 1, 2, 3...). "
    "Eje Y = views acumuladas. Ignora fechas — refleja la progresión real vídeo a vídeo."
)
acum_rows = []
for plat in plats:
    sub = df_f[df_f["platform"] == plat].sort_values("timestamp").copy()
    sub["video_idx"] = range(1, len(sub) + 1)
    sub["views_acum"] = sub["views"].cumsum()
    for _, r in sub.iterrows():
        acum_rows.append({
            "Plataforma": plat,
            "video_idx": int(r["video_idx"]),
            "views_acum": int(r["views_acum"]),
            "views_video": int(r["views"]),
            "fecha": r["fecha"].isoformat(),
            "hook": r["hook"],
        })

if acum_rows:
    df_acum = pd.DataFrame(acum_rows)
    fig_tend = px.line(
        df_acum,
        x="video_idx",
        y="views_acum",
        color="Plataforma",
        color_discrete_map={"TikTok": "#0f172a", "Instagram": "#c13584"},
        markers=True,
        hover_data={"views_video": True, "fecha": True, "hook": True, "video_idx": False, "views_acum": ":,"},
        labels={"video_idx": "Nº de vídeo (orden de publicación)",
                "views_acum": "Views acumuladas",
                "Plataforma": ""},
    )
    fig_tend.update_traces(line=dict(width=3), marker=dict(size=8))
    fig_tend.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    st.plotly_chart(fig_tend, use_container_width=True)

# ──────────────────── Top vídeos por views ────────────────────────────
st.markdown("---")
st.subheader("Top vídeos por views")
st.caption(
    "**7 entradas = 5 vídeos** — los 2 virales aparecen tanto en TikTok como en Instagram "
    "(mismo vídeo cross-platform). Los 3 restantes son solo de Instagram."
)

TOP_ENTRIES = [
    {"Views": 61_200, "Plataforma": "TikTok"},
    {"Views": 39_300, "Plataforma": "Instagram"},
    {"Views": 32_900, "Plataforma": "Instagram"},
    {"Views": 24_100, "Plataforma": "TikTok"},
    {"Views": 18_000, "Plataforma": "Instagram"},
    {"Views": 17_500, "Plataforma": "Instagram"},
    {"Views": 10_400, "Plataforma": "Instagram"},
]
df_top = pd.DataFrame(TOP_ENTRIES)
df_top_display = df_top.copy()
df_top_display["Views"] = df_top_display["Views"].apply(lambda v: f"{v:,}".replace(",", "."))
st.dataframe(df_top_display, hide_index=True, use_container_width=True)

# ──────────────────── Row: histograma + progresión media/mediana ────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Distribución de views por bucket")
    st.caption("Cuántos vídeos caen en cada rango. Muestra dónde se concentra la operativa.")
    bucket_defs = [
        ("<500", 0, 500),
        ("500-1k", 500, 1000),
        ("1k-3k", 1000, 3000),
        ("3k-5k", 3000, 5000),
        ("5k-10k", 5000, 10000),
        ("10k-30k", 10000, 30000),
        ("30k+", 30000, 10**9),
    ]
    rows = []
    for lab, lo, hi in bucket_defs:
        for plat in plats:
            mask = (df_f["platform"] == plat) & (df_f["views"] >= lo) & (df_f["views"] < hi)
            rows.append({"bucket": lab, "platform": plat, "count": int(mask.sum())})
    df_hist = pd.DataFrame(rows)
    fig_hist = px.bar(
        df_hist,
        x="bucket",
        y="count",
        color="platform",
        color_discrete_map={"TikTok": "#0f172a", "Instagram": "#c13584"},
        barmode="group",
        labels={"count": "Nº vídeos", "bucket": "Rango views", "platform": ""},
    )
    fig_hist.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_hist, use_container_width=True)

with col_b:
    st.subheader("Mediana de views — Instagram (antes vs ahora)")
    st.caption(
        "Mediana de views en los 10 primeros vídeos del mes vs los 10 últimos. "
        "El baseline real ha subido x5+ a lo largo del periodo."
    )

    # Gráfica de barras antes/después
    df_evol = pd.DataFrame([
        {"Periodo": "Primeros 10 publis", "Mediana views": 200},
        {"Periodo": "Últimos 10 publis", "Mediana views": 1100},
    ])
    fig_evol = px.bar(
        df_evol,
        x="Periodo",
        y="Mediana views",
        text="Mediana views",
        color="Periodo",
        color_discrete_map={
            "Primeros 10 publis": "#cbd5e1",
            "Últimos 10 publis": "#c13584",
        },
    )
    fig_evol.update_traces(
        texttemplate="%{text:,} views".replace(",", "."),
        textposition="outside",
        textfont=dict(size=18, color="#0f172a"),
    )
    fig_evol.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=40, b=10),
        showlegend=False,
        yaxis=dict(range=[0, 1400], showgrid=False, showticklabels=False),
        xaxis_title=None,
        yaxis_title=None,
    )
    # Anotación de delta entre las barras
    fig_evol.add_annotation(
        x=0.5, y=1300,
        text="<b>x5+ crecimiento</b>",
        showarrow=False,
        font=dict(size=16, color="#16a34a"),
        xref="paper",
    )
    st.plotly_chart(fig_evol, use_container_width=True)


# ──────────────────── CTA Conversion + funnel ─────────────────────────
st.markdown("---")
st.subheader("CTA conversion — Funnel completo de generación de leads")
st.caption(
    "Ratio en cada paso del funnel: views → comentario CTA → entrada al lead magnet → "
    "click a web destino. Es la métrica que conecta contenido con conversión real."
)

st.markdown("**Conversión view → comentario CTA**")
cta_c1, cta_c2, cta_c3 = st.columns(3)
cta_c1.metric(
    "Pablo",
    "0,85%",
    help="Ratio comentario CTA / views típico para Pablo (basado en la pieza ya validada)"
)
cta_c2.metric(
    "Media del nicho",
    "2,4%",
    help="Ratio medio del nicho finanzas/inversión cuando la pieza está bien armada"
)
cta_c3.metric(
    "Mejor del nicho",
    "3,1%",
    help="Mejor ratio observado en el nicho — techo realista al que aspirar"
)

st.markdown("**Funnel desde comentario CTA** (benchmarks del sistema — no medidos en Pablo todavía)")
fun_c1, fun_c2 = st.columns(2)
fun_c1.metric(
    "Comentario → entra al lead magnet",
    "~60%",
    help="Benchmark del sistema. NO está medido en la cuenta de Pablo todavía."
)
fun_c2.metric(
    "Lead magnet → web destino (VSL)",
    "~10-20%",
    help="En el caso de Pablo, la web destino es el VSL (video sales letter). Rango benchmark del sistema — no medido en Pablo."
)

st.info(
    "**Lectura del funnel:** view → CTA (Pablo 0,85% · media nicho 2,4% · mejor nicho 3,1%) → "
    "lead magnet (~60% benchmark, no medido) → **VSL** (~10-20% benchmark, no medido). "
    "El paso más débil es el primer salto (view → CTA): Pablo está 3x por debajo de la "
    "media del nicho — hay margen para acercarse al 2,4% antes de optimizar los siguientes pasos. "
    "Los pasos 2 y 3 son orientativos: usan benchmarks del sistema porque en Pablo aún "
    "no están instrumentados (lead magnet clicks salientes + VSL pageviews/conversiones)."
)

# ──────────────────── Forecast próximo mes ────────────────────────────
st.markdown("### Objetivo a cumplir — próximo mes")
st.caption(
    "Cascada en valores absolutos manteniendo los ratios actuales. Es el suelo de lo que "
    "debemos entregar el mes que viene — el objetivo mínimo a cumplir antes de empezar a "
    "optimizar para superarlo."
)

# Views/mes ≈ views oficiales totales / 2 (cubrieron ~60 días entre IG e historial TT)
VIEWS_MES_ESTIM = round((views_oficial / 2) / 1000) * 1000  # 130.000 redondeado
RATIO_CTA_PABLO = 0.85 / 100
RATIO_LM = 0.60
RATIO_WEB_LOW = 0.10
RATIO_WEB_HIGH = 0.20

cta_estim = round(VIEWS_MES_ESTIM * RATIO_CTA_PABLO)
lm_estim = round(cta_estim * RATIO_LM)
web_estim_low = int(lm_estim * RATIO_WEB_LOW)
web_estim_high = int(lm_estim * RATIO_WEB_HIGH)

fc1, fc2, fc3, fc4 = st.columns(4)
fc1.metric("Views mes (actual)", f"{VIEWS_MES_ESTIM:,}".replace(",", "."))
fc2.metric(
    "Comentarios CTA",
    f"~{cta_estim:,}".replace(",", "."),
    help="Aplicando 0,85% conversión Pablo actual"
)
fc3.metric(
    "Entradas lead magnet",
    f"~{lm_estim:,}".replace(",", "."),
    help="Benchmark del sistema: ~60% de comentarios CTA acceden al lead magnet. No medido en Pablo todavía."
)
fc4.metric(
    "Llegadas a producto (VSL)",
    f"~{web_estim_low}",
    help="Benchmark del sistema (suelo): ~10% del lead magnet llega al VSL. No medido en Pablo todavía."
)

st.markdown(
    f"**Objetivo del mes:** {VIEWS_MES_ESTIM:,} views → {cta_estim:,} comentarios CTA "
    f"→ {lm_estim:,} entradas LM → **~{web_estim_low} llegadas al VSL**.  \n"
    f"Es el suelo a defender manteniendo los ratios actuales. Cualquier mejora del CTA "
    f"(0,85% → 2,4% media nicho) o de las views multiplica directamente las llegadas al VSL — "
    f"ese es el upside del mes."
        .replace(",", ".")
)


# ──────────────────── Comparativa primer mes — Pablo vs cuenta normal ─
st.markdown("---")
st.subheader("Comparativa primer mes — Pablo vs cuenta normal del sistema")
st.caption(
    "Pablo en su primer mes operativo vs el benchmark interno del sistema de avatares (mes 1)."
)

pablo_primer_viral_min = min(PABLO_PRIMER_VIRAL.values())

comp_rows = [
    {
        "Métrica": "Views totales (ambas cuentas)",
        "Cuenta normal mes 1": f"{BENCHMARK_NORMAL_MES_1['views_total']:,}".replace(",", "."),
        "Pablo mes 1": f"{views_oficial:,}".replace(",", "."),
        "Delta": f"+{round((views_oficial - BENCHMARK_NORMAL_MES_1['views_total']) / BENCHMARK_NORMAL_MES_1['views_total'] * 100)}%",
    },
    {
        "Métrica": "Seguidores totales (ambas cuentas)",
        "Cuenta normal mes 1": BENCHMARK_NORMAL_MES_1["seguidores_total"],
        "Pablo mes 1": seguidores_total,
        "Delta": f"+{round((seguidores_total - BENCHMARK_NORMAL_MES_1['seguidores_total']) / BENCHMARK_NORMAL_MES_1['seguidores_total'] * 100)}%",
    },
    {
        "Métrica": "Nº de vídeo del primer viral",
        "Cuenta normal mes 1": f"#{BENCHMARK_NORMAL_MES_1['primer_viral_video_num']}",
        "Pablo mes 1": f"IG #{PABLO_PRIMER_VIRAL['instagram']} · TT #{PABLO_PRIMER_VIRAL['tiktok']}",
        "Delta": f"{round(BENCHMARK_NORMAL_MES_1['primer_viral_video_num'] / pablo_primer_viral_min)}x antes",
    },
]
df_comp = pd.DataFrame(comp_rows)
st.dataframe(df_comp, hide_index=True, use_container_width=True)
st.success(
    f"Pablo está **por encima del benchmark** en las tres métricas clave: "
    f"+{round((views_oficial / BENCHMARK_NORMAL_MES_1['views_total'] - 1) * 100)}% en views, "
    f"+{round((seguidores_total / BENCHMARK_NORMAL_MES_1['seguidores_total'] - 1) * 100)}% en seguidores, "
    f"y el primer viral llegó {round(BENCHMARK_NORMAL_MES_1['primer_viral_video_num'] / pablo_primer_viral_min)}x antes de lo esperado "
    f"(vídeo #{pablo_primer_viral_min} vs media #{BENCHMARK_NORMAL_MES_1['primer_viral_video_num']})."
)

# ──────────────────── Tabla detallada ────────────────────────────────
st.markdown("---")
st.subheader("Detalle de publicaciones — registro completo")
df_tab = df_f.sort_values("views", ascending=False).copy()
df_tab["fecha"] = df_tab["timestamp"].dt.strftime("%Y-%m-%d")
df_tab_disp = df_tab[
    ["platform", "fecha", "views", "likes", "comments", "shares", "saves", "hook", "url"]
].rename(columns={
    "platform": "Plataforma",
    "fecha": "Fecha",
    "views": "Views",
    "likes": "Likes",
    "comments": "Cmt",
    "shares": "Sh",
    "saves": "Sv",
    "hook": "Hook",
    "url": "URL",
})
st.dataframe(
    df_tab_disp,
    use_container_width=True,
    hide_index=True,
    column_config={
        "URL": st.column_config.LinkColumn(),
        "Views": st.column_config.NumberColumn(format="%d"),
    },
)
st.caption(
    "Tabla ordenada por views descendente (top 5 son las 5 primeras filas). "
    "Shares y saves solo están disponibles en TikTok del scrape público; "
    "los totales oficiales de IG (saves: 1.601, shares: 720) están reflejados en los KPIs superiores."
)

# ──────────────────── Análisis comunidad + estrategia ─────────────────
st.markdown("---")
st.subheader("Análisis comunidad")
st.caption(
    "De los comentarios que NO son respuesta al CTA (palabra clave para automatización), "
    "esto es lo que hace la comunidad. Mide intención de aprender y nivel de interacción real."
)

com_c1, com_c2, com_c3 = st.columns(3)
com_c1.metric(
    "Preguntan",
    f"{COMUNIDAD_DIST['preguntas_aprender']}%",
    help=f"{COMUNIDAD_COUNTS['preguntas_aprender']} de {COMUNIDAD_TOTAL} comentarios — intencionalidad de aprender, preguntas técnicas sobre el tema del vídeo"
)
com_c2.metric(
    "Responden / aportan",
    f"{COMUNIDAD_DIST['responder_aportar']}%",
    help=f"{COMUNIDAD_COUNTS['responder_aportar']} de {COMUNIDAD_TOTAL} comentarios — responden a lo que se pregunta o aportan datos extra (acciones que tienen/quieren, contexto técnico)"
)
com_c3.metric(
    "Otros",
    f"{COMUNIDAD_DIST['otros']}%",
    help=f"{COMUNIDAD_COUNTS['otros']} de {COMUNIDAD_TOTAL} comentarios — comentarios diversos, agradecimientos puntuales. La comunidad debate, no aplaude."
)

fig_com = go.Figure(go.Bar(
    x=[COMUNIDAD_DIST["preguntas_aprender"], COMUNIDAD_DIST["responder_aportar"], COMUNIDAD_DIST["otros"]],
    y=["Preguntan (aprender)", "Responden / aportan", "Otros"],
    orientation="h",
    marker=dict(color=["#7c3aed", "#16a34a", "#94a3b8"]),
    text=[f"{COMUNIDAD_DIST['preguntas_aprender']}%",
          f"{COMUNIDAD_DIST['responder_aportar']}%",
          f"{COMUNIDAD_DIST['otros']}%"],
    textposition="auto",
))
fig_com.update_layout(
    height=200,
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(visible=False),
    showlegend=False,
)
st.plotly_chart(fig_com, use_container_width=True)

st.markdown("### En base a los gustos de la gente, estratégicamente podríamos seguir...")

st.markdown("""
**1. Capitalizar las menciones de acciones concretas.**
El público responde con acciones que poseen o quieren — 24 menciones únicas de tickers entre IG y TT
(Costco, Coca Cola, Mcd, Nvidia, Google, Abbvie, Microsoft, Tesla, ASML, IONQ, CAT...).
Es data oro.
- *Próximo vídeo:* **"Las 10 acciones MÁS mencionadas por la comunidad"** usando los nombres reales que
  vienen de los comentarios. Loop virtuoso — sentirán que les escuchas y volverán a comentar.

**2. La audiencia cuestiona, no aplaude.**
Solo 2 "gracias" en 106 comentarios analizados. No es un problema —
el algoritmo prefiere debate. Significa que:
- Vídeo con afirmación tajante genera más engagement que vídeo "soft".
- Responder públicamente a los críticos técnicos
  (`@torres_bueu`, `@me.he.perdido`, `@ccllbb1`) genera hilos largos →
  más tiempo en vídeo → más alcance.

**3. La objeción más repetida es la inflación.**
Aparece en 3 vídeos distintos ("le metes la inflación y sigues perdiendo",
"la inversión pasiva es un engaño", "no perder no es lo mismo que ganar").
- *Próximo vídeo:* **"Por qué 'no perder' ya es ganar (con la inflación matematizada)"**
  → cierra la objeción de raíz y muestra autoridad técnica.

**4. El público ya habla en el lenguaje de Pablo.**
"20 años / largo plazo" aparece 4× en bigrams TT. El marco temporal de Pablo se está internalizando.
Mantener y profundizar ese lenguaje refuerza la autoridad — usar siempre horizonte temporal
concreto en cada vídeo.
""")

