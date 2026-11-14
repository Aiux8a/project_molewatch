import base64
import io
import math
from pathlib import Path

import numpy as np
import requests
import streamlit as st
from PIL import Image

API_URL = "https://molewatch-app-259840576181.europe-west1.run.app/predict"

ASSETS = Path("assets")
MASCOT = ASSETS / "mole.png"
EXAMPLE = ASSETS / "example.jpg"

st.set_page_config(
    page_title="MoleWatch",
    page_icon=str(MASCOT) if MASCOT.exists() else "🔎",
    layout="centered",
)

# ----------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Work+Sans:wght@400;500&display=swap');

  :root {
    --paper:  #F4F0E9;   /* warm paper, off the mascot's background */
    --card:   #FFFFFF;
    --ink:    #3A322C;   /* his dark fur, not black */
    --muted:  #7D7067;
    --calm:   #6E7F5B;   /* the moss at his feet */
    --notice: #A9752F;   /* his tweed and the brass of the lens */
    --rule:   #E3DCD0;
  }

  .stApp { background: var(--paper); }
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { max-width: 44rem; padding-top: 3rem; padding-bottom: 4rem; }

  html, body, .stApp, .stMarkdown, .stButton, [data-testid="stFileUploader"] {
    font-family: 'Work Sans', system-ui, sans-serif;
    color: var(--ink);
  }
  /* Streamlit draws icons with Material Symbols ligatures — don't restyle them */
  [data-testid="stIconMaterial"] {
    font-family: 'Material Symbols Rounded' !important;
  }

  /* masthead ------------------------------------------------------- */
  .mw-head {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: .75rem;
    margin-bottom: .35rem;
  }
  .mw-head img { width: 52px; height: 52px; object-fit: contain; }
  .mw-name {
    font-family: 'Fraunces', Georgia, serif;
    font-weight: 600;
    font-size: 2rem;
    letter-spacing: -0.015em;
    line-height: 1;
  }

  /* landing --------------------------------------------------------- */
  .mw-hero { text-align: center; margin-bottom: 1.2rem; }
  .mw-hero img { width: 108px; height: 108px; object-fit: contain; margin-bottom: .3rem; }
  .mw-hero .mw-name { font-size: 2.6rem; display: block; }
  .mw-lede {
    font-family: 'Fraunces', Georgia, serif;
    font-size: 1.35rem;
    line-height: 1.4;
    max-width: 30rem;
    margin: 1rem auto 2rem !important;
    text-align: center;
  }

  .mw-section {
    max-width: 34rem;
    margin: 0 auto 1.8rem !important;
    color: var(--muted);
    line-height: 1.7;
    font-size: .95rem;
  }
  .mw-section h3 {
    font-family: 'Work Sans', sans-serif;
    font-size: .95rem;
    font-weight: 500;
    color: var(--ink);
    margin: 0 0 .35rem;
  }
  [data-testid="stExpander"] {
    max-width: 34rem;
    margin: 1.5rem auto 0 !important;
    border: none;
    border-top: 1px solid var(--rule);
    background: transparent;
  }
  [data-testid="stExpander"] p,
  [data-testid="stExpander"] li {
    color: var(--muted);
    font-size: .88rem;
    line-height: 1.65;
  }
  [data-testid="stExpander"] strong { color: var(--ink); font-weight: 500; }
  [data-testid="stExpander"] summary { font-size: .9rem; }

  .mw-group { margin-top: 1.1rem; }
  .mw-group h4 {
    font-family: 'Work Sans', sans-serif;
    font-size: .92rem;
    font-weight: 500;
    color: var(--ink);
    margin: 0 0 .4rem;
    display: flex;
    align-items: center;
    gap: .5rem;
  }
  .mw-group h4::before {
    content: "";
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex: none;
    background: var(--swatch);
  }
  .mw-group ul { margin: 0; padding-left: 1.3rem; }
  .mw-group li { padding: .12rem 0; }

  /* keep the two tabs side by side on a phone — Streamlit wraps them by default */
  @media (max-width: 640px) {
    [data-testid="stHorizontalBlock"] {
      flex-wrap: nowrap !important;
      gap: .4rem !important;
    }
    [data-testid="stColumn"] { min-width: 0 !important; }
    [data-testid="stButton"] button { font-size: .92rem; padding: .4rem 0; }
    .block-container { padding-left: 1rem; padding-right: 1rem; }
  }

  /* nav ------------------------------------------------------------- */
  .mw-nav-rule {
    max-width: 24rem;
    margin: 0 auto 2.5rem;
    border-bottom: 1px solid var(--rule);
  }

  [data-testid="stButton"] { text-align: center; }
  [data-testid="stButton"] button,
  [data-testid="stButton"] button:focus,
  [data-testid="stButton"] button:active {
    font-family: 'Work Sans', sans-serif !important;
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    color: var(--muted) !important;
    font-weight: 400;
    padding: .4rem .2rem;
    letter-spacing: .01em;
  }
  [data-testid="stButton"] button:hover { color: var(--ink) !important; }

  /* the active tab — both old and new Streamlit naming */
  [data-testid="stButton"] button[kind="primary"],
  [data-testid="stButton"] button[data-testid="stBaseButton-primary"] {
    color: var(--ink) !important;
    font-weight: 500;
    border-bottom: 2px solid var(--notice) !important;
  }

  /* searching ------------------------------------------------------- */
  .mw-search { text-align: center; margin: 2.5rem 0 1rem; }
  .mw-search img { width: 76px; height: 76px; object-fit: contain; }
  .mw-search p {
    color: var(--muted);
    font-size: .9rem;
    margin-top: .4rem !important;
  }

  .mw-search { text-align: center; margin: 1.5rem 0 1rem; }
  .mw-search p { color: var(--muted); font-size: .9rem; margin-top: .4rem !important; }

  /* aperture -------------------------------------------------------- */
  .mw-scope { display: flex; justify-content: center; margin: .5rem 0 1.75rem; }

  .mw-arc { transform: rotate(-90deg); }
  .mw-arc .track { fill: none; stroke: var(--rule); stroke-width: 6; }
  .mw-arc .value { fill: none; stroke-width: 6; stroke-linecap: round; }
  .mw-arc .tick  { stroke: var(--ink); stroke-width: 3; stroke-linecap: round; }

  @keyframes mw-draw { from { stroke-dashoffset: var(--circ); } }
  .mw-arc .value { animation: mw-draw 900ms cubic-bezier(.25,.9,.3,1) both; }

  @media (prefers-reduced-motion: reduce) {
    .mw-arc .value { animation: none; }
  }

  /* verdict --------------------------------------------------------- */
  .mw-verdict {
    font-family: 'Fraunces', Georgia, serif;
    font-size: 1.6rem;
    font-weight: 600;
    line-height: 1.25;
    letter-spacing: -0.01em;
    text-align: center;
    margin-bottom: .7rem;
  }
  .mw-body {
    text-align: center;
    color: var(--muted);
    line-height: 1.65;
    max-width: 30rem;
    margin: 0 auto 1.5rem !important;
  }
  .mw-score {
    text-align: center;
    color: var(--muted);
    font-size: .85rem;
    padding-top: 1.1rem;
    border-top: 1px solid var(--rule);
    max-width: 30rem;
    margin: 0 auto !important;
  }

  [data-testid="stFileUploader"] {
    max-width: 30rem;
    margin: 0 auto !important;
  }
  [data-testid="stFileUploader"] label,
  [data-testid="stFileUploader"] label p,
  [data-testid="stFileUploader"] label div { text-align: center; width: 100%; }

  .mw-foot {
    padding-top: 1.1rem;
    border-top: 1px solid var(--rule);
    color: var(--muted);
    font-size: .82rem;
    line-height: 1.6;
    text-align: center;
    max-width: 36rem;
    margin: 3.5rem auto 0 !important;
  }
</style>
""", unsafe_allow_html=True)


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


# Minimum share of the frame that must look like skin before we'll send the
# photo to the model. The model only knows dermatoscopic lesion images, so it
# returns a confident score for anything at all — a face, a pet, a wall. This
# catches the obvious cases; it is a crude guard, not a classifier.
SKIN_FLOOR = 0.40


def skin_fraction(data: bytes) -> float:
    """Roughly what share of the image looks like skin."""
    img = Image.open(io.BytesIO(data)).convert("RGB").resize((160, 160))
    a = np.asarray(img).astype(float)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    spread = a.max(-1) - a.min(-1)

    skin = (r > 40) & (g > 20) & (b > 10) & (r > b) & (r >= g) & (spread > 10)
    return float(skin.mean())


MASCOT_B64 = b64(MASCOT.read_bytes()) if MASCOT.exists() else None


def mascot_img(cls: str = "") -> str:
    if not MASCOT_B64:
        return ""
    return f'<img src="data:image/png;base64,{MASCOT_B64}" alt="" class="{cls}">'


# ----------------------------------------------------------------------
# Landing
# ----------------------------------------------------------------------

def landing():
    st.markdown("""
    <p class="mw-lede">
      Photograph a mole. Find out whether it's worth showing to a doctor.
    </p>

    <div class="mw-section">
      MoleWatch gives one of two answers &mdash; <b>worth showing to a
      doctor</b>, or <b>keep an eye on it</b>. It won't tell you what something
      is. Only a doctor can do that, and usually only after a biopsy.
    </div>

    <div class="mw-section">
      It was trained on clinical photographs taken through a dermatoscope, so
      treat anything it says with caution, and take a mole that worries you to a
      doctor whatever this page tells you.
    </div>
    """, unsafe_allow_html=True)

    with st.expander("What's behind it"):
        st.markdown("""
**The data.** 10,015 photographs from the HAM10000 collection, taken in
dermatology clinics in Austria and Australia. Each lesion was labelled by a
specialist and most labels were confirmed by biopsy. About one mole in five
needed a doctor's attention, so the model has seen many more ordinary moles
than worrying ones.

**The two groups.** The data labels seven kinds of lesion. Melanoma, basal cell
carcinoma, and actinic keratosis and Bowen's disease are grouped as *worth
showing to a doctor*. Ordinary moles, benign keratosis, dermatofibroma and
vascular lesions are grouped as *keep an eye on it*.

**Why it errs towards sending you to a doctor.** A model that says "fine" too
readily misses cancers, and a missed melanoma costs far more than an
unnecessary appointment. The decision point was set low on purpose, catching
more of what matters and accepting more false alarms in exchange. Most of those
false alarms are benign keratosis, which resembles melanoma closely enough that
dermatologists confuse the two.

**Where it struggles.** A dermatoscope is a lit magnifying lens pressed against
the skin, and an ordinary phone photo looks different enough that MoleWatch is
less reliable on one. It has also never seen your skin, your history, or what
the mole looked like last month.
""")


# ----------------------------------------------------------------------
# Tool
# ----------------------------------------------------------------------

def aperture(img_b64: str, probability: float, threshold: float, elevated: bool) -> str:
    """Photo in a circular aperture, score traced as an arc around it."""
    r, size = 128, 300
    circ = 2 * math.pi * r
    colour = "var(--notice)" if elevated else "var(--calm)"

    angle = 2 * math.pi * threshold
    cx = cy = size / 2
    x1, y1 = cx + (r - 7) * math.cos(angle), cy + (r - 7) * math.sin(angle)
    x2, y2 = cx + (r + 14) * math.cos(angle), cy + (r + 14) * math.sin(angle)

    return f"""
    <div class="mw-scope">
      <svg class="mw-arc" width="{size}" height="{size}" viewBox="0 0 {size} {size}"
           style="--circ:{circ:.1f}">
        <defs>
          <clipPath id="mw-clip"><circle cx="{cx}" cy="{cy}" r="{r - 14}"/></clipPath>
        </defs>
        <image href="data:image/jpeg;base64,{img_b64}"
               x="{cx - r + 14}" y="{cy - r + 14}"
               width="{2 * (r - 14)}" height="{2 * (r - 14)}"
               preserveAspectRatio="xMidYMid slice"
               clip-path="url(#mw-clip)"
               transform="rotate(90 {cx} {cy})"/>
        <circle class="track" cx="{cx}" cy="{cy}" r="{r}"/>
        <circle class="value" cx="{cx}" cy="{cy}" r="{r}" stroke="{colour}"
                stroke-dasharray="{circ:.1f}"
                stroke-dashoffset="{circ * (1 - probability):.1f}"/>
        <line class="tick" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>
      </svg>
    </div>
    """


def tool():
    uploaded = st.file_uploader("Photo of a mole", type=["jpg", "jpeg", "png"])

    image_bytes = image_name = image_type = None

    if uploaded:
        image_bytes, image_name, image_type = uploaded.getvalue(), uploaded.name, uploaded.type
    elif EXAMPLE.exists() and st.button("Try an example photo"):
        image_bytes, image_name, image_type = EXAMPLE.read_bytes(), "example.jpg", "image/jpeg"

    if image_bytes and skin_fraction(image_bytes) < SKIN_FLOOR:
        st.markdown("""
        <p class="mw-verdict">That doesn't look like skin</p>
        <p class="mw-body">
          MoleWatch only reads close-up photos of a single mole, filling most of
          the frame. Try again with the camera closer in.
        </p>
        """, unsafe_allow_html=True)
        image_bytes = None

    if image_bytes:
        searching = st.empty()
        searching.markdown("""
        <div class="mw-search"><p>Looking at it</p></div>
        """, unsafe_allow_html=True)

        try:
            response = requests.post(
                API_URL,
                files={"file": (image_name, image_bytes, image_type)},
                timeout=30,
            )
        except requests.RequestException:
            response = None

        searching.empty()

        if response is None or response.status_code != 200:
            st.markdown("""
            <p class="mw-verdict">The model didn't answer</p>
            <p class="mw-body">
              Nothing is wrong with your photo. Wait a moment and upload it again.
            </p>
            """, unsafe_allow_html=True)
        else:
            result = response.json()
            probability = float(result["probability"])
            threshold = float(result["threshold"])
            elevated = bool(result["is_suspicious"])

            st.markdown(
                aperture(b64(image_bytes), probability, threshold, elevated),
                unsafe_allow_html=True,
            )

            if elevated:
                verdict = "Worth showing to a doctor"
                body = ("This photo has features MoleWatch associates with moles "
                        "that need checking. That isn't a diagnosis, and it isn't "
                        "urgent — book an appointment when it suits you.")
            else:
                verdict = "Nothing unusual in this photo"
                body = ("Keep an eye on it. Photograph it again in a month and "
                        "compare the two. See a doctor sooner if it grows, changes "
                        "colour, bleeds or itches.")

            st.markdown(f"""
            <p class="mw-verdict">{verdict}</p>
            <p class="mw-body">{body}</p>
            <p class="mw-score">
              Score {probability:.2f}, where anything above {threshold:.2f} is
              flagged for checking. The mark on the ring shows where that line sits.
            </p>
            """, unsafe_allow_html=True)

    st.markdown("""
    <p class="mw-foot">
      MoleWatch was trained on dermatoscopic images — the kind taken through a
      magnifying scope in a clinic — so ordinary phone photos are harder for it
      to read. It looks for three kinds of skin cancer, and it misses things.
      If a mole worries you, see a doctor whatever this page says.
    </p>
    """, unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Masthead, navigation, and whichever view is active
# ----------------------------------------------------------------------

st.markdown(f"""
<div class="mw-hero">
  {mascot_img()}
  <span class="mw-name">MoleWatch</span>
</div>
""", unsafe_allow_html=True)

page = st.session_state.get("page", "intro")

_, nav_a, nav_b, _ = st.columns([0.3, 1, 1, 0.3])

with nav_a:
    if st.button("Introduction", use_container_width=True,
                 type="primary" if page == "intro" else "secondary"):
        st.session_state.page = "intro"
        st.rerun()

with nav_b:
    if st.button("Upload a photo", use_container_width=True,
                 type="primary" if page == "upload" else "secondary"):
        st.session_state.page = "upload"
        st.rerun()

st.markdown('<div class="mw-nav-rule"></div>', unsafe_allow_html=True)

if page == "upload":
    tool()
else:
    landing()
