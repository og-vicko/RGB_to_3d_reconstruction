import streamlit as st

st.markdown("""
    <style>
        /* Remove inner white background */
        div[data-testid="stFileDropzone"] {
            background-color: #1e1e24 !important; /* Dark background */
            border: 2px dashed #555 !important; /* Optional: Adjust border color */
            border-radius: 10px !important; /* Smooth corners */
        }

        /* Change text and icon color to match dark theme */
        div[data-testid="stFileDropzone"] * {
            color: white !important;
        }

        /* Darken the 'Browse files' button */
        button[kind="secondary"] {
            background-color: #101014 !important;
            color: white !important;
            border-radius: 5px !important;
        }
    </style>
""", unsafe_allow_html=True)

# Streamlit app UI
st.title("Streamlit Demo")

st.subheader("Upload an image")
uploaded_file = st.file_uploader("Choose a file", type=["jpg", "png", "jpeg"])

if uploaded_file:
    st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
