import os, sys, streamlit as st, platform
st.title("Streamlit Debug")
st.write({"python": sys.version, "platform": platform.platform(), "cwd": os.getcwd()})
st.write("Files here:", sorted(os.listdir(".")))
