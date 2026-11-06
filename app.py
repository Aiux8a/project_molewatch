import streamlit as st
import requests

API_URL = "https://molewatch-app-259840576181.europe-west1.run.app/predict"

st.title("MoleWatch")
st.caption("Not a diagnosis. Built and tested on dermatoscopic images.")

uploaded = st.file_uploader("Photo of a mole", type=["jpg", "jpeg", "png"])

if uploaded:
    st.image(uploaded, width=300)

    with st.spinner("Checking..."):
        r = requests.post(
            API_URL,
            files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)},
        )

    if r.status_code == 200:
        result = r.json()
        if result["is_suspicious"]:
            st.warning("This doesn't look like an ordinary mole. Worth showing a doctor.")
        else:
            st.info("This doesn't look like melanoma. Take another photo in a month and "
                    "compare. See a doctor if it grows, changes colour, bleeds or itches.")
    else:
            st.error(f"API returned {r.status_code}: {r.text}")
