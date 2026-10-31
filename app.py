import streamlit as st

st.title("MoleWatch")
st.caption("Not a diagnosis. Built and tested on dermatoscopic images.")

uploaded = st.file_uploader("Photo of a mole", type=["jpg", "jpeg", "png"])

if uploaded:
    st.image(uploaded, width=300)

    # fake until Fareedah's endpoint exists
    result = {"probability": 0.42, "level": "monitor"}

    if result["level"] == "refer":
        st.warning("This doesn't look like an ordinary mole. Worth showing a doctor.")
    else:
        st.info("This doesn't look like melanoma. Keep an eye on it and see a doctor if it changes.")
