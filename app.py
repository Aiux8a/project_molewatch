import base64
import math
from pathlib import Path

import requests
import streamlit as st

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
  .mw-hero img { width: 110px; height: 110px; object-fit: contain; margin-bottom: .3rem; }
  .mw-hero .mw-name { font-size: 2.6rem; display: block; }
  .mw-lede {
    font-family: 'Fraunces', Georgia, serif;
    font-size: 1.35rem;
    line-height: 1.4;
    max-width: 30rem;
    margin: 1rem auto 0 !important;
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

  /* aperture -------------------------------------------------------- */
  .mw-scope { display: flex; justify-content: center; margin: .5rem 0 1.75rem; }

  .mw-arc { transform: rotate(-90deg); }
  .mw-arc .track { fill: none; stroke: var(--rule); stroke-width: 6; }
  .mw-arc .value { fill: none; stroke-width: 6; stroke-linecap: round; }
  .mw-arc .tick  { stroke: var(--ink); stroke-width: 3; stroke-linecap: round; }

  @media (prefers-reduced-motion: no-preference) {
    .mw-arc .value { animation: mw-draw 900ms cubic-bezier(.25,.9,.3,1) both; }
    @keyframes mw-draw { from { stroke-dashoffset: var(--circ); } }
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
  [data-testid="stFileUploader"] label p { text-align: center; }

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
      Photograph a mole and find out whether it's worth showing to a doctor.
    </p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="mw-section">
      <h3>What it does</h3>
      MoleWatch looks at a photo of a single mole and gives one of two answers:
      worth showing to a doctor, or keep an eye on it. It never says what a
      lesion is, because naming a diagnosis is a doctor's job and usually needs
      a biopsy.
    </div>

    <div class="mw-section">
      <h3>How the two answers are decided</h3>
      The training data labels seven kinds of lesion. MoleWatch sorts them into
      two groups, and answers with the group rather than the lesion.

      <div class="mw-group" style="--swatch: var(--notice)">
        <h4>Worth showing to a doctor</h4>
        <ul>
          <li>Melanoma</li>
          <li>Basal cell carcinoma</li>
          <li>Actinic keratosis and Bowen's disease</li>
        </ul>
      </div>

      <div class="mw-group" style="--swatch: var(--calm)">
        <h4>Keep an eye on it</h4>
        <ul>
          <li>Melanocytic nevus &mdash; an ordinary mole</li>
          <li>Benign keratosis</li>
          <li>Dermatofibroma</li>
          <li>Vascular lesion</li>
        </ul>
      </div>
    </div>

    <div class="mw-section">
      <h3>What it learned from</h3>
      10,015 dermatoscopic photographs from the HAM10000 collection, taken in
      dermatology clinics in Austria and Australia. Each lesion was labelled by
      a specialist and most labels were confirmed by biopsy. About one mole in
      five needed a doctor's attention, so the model has seen many more ordinary
      moles than worrying ones.
    </div>

    <div class="mw-section">
      <h3>Why it errs towards sending you to a doctor</h3>
      A model that says &ldquo;fine&rdquo; too readily misses cancers. Since a
      missed melanoma costs far more than an unnecessary appointment, the
      decision point was deliberately set low &mdash; catching more of the
      lesions that matter, and accepting more false alarms in exchange. Most of
      those false alarms are benign keratosis, which resembles melanoma closely
      enough that dermatologists confuse the two.
    </div>

    <div class="mw-section">
      <h3>Where it struggles</h3>
      The training photos were taken through a dermatoscope &mdash; a lit
      magnifying lens pressed against the skin. An ordinary phone photo looks
      different enough that MoleWatch is less reliable on one. It has also never
      seen your skin, your history, or what the mole looked like last month.
    </div>
    """, unsafe_allow_html=True)


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

    if image_bytes:
        with st.spinner("Looking at it"):
            try:
                response = requests.post(
                    API_URL,
                    files={"file": (image_name, image_bytes, image_type)},
                    timeout=30,
                )
            except requests.RequestException:
                response = None

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

_, nav_a, nav_b, _ = st.columns([1, 1.2, 1.2, 1])

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
