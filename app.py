
import os, sys, platform, textwrap
import streamlit as st

st.set_page_config(page_title="Streamlit Debug App", layout="wide")
st.title("Streamlit Cloud Debug — Are we in the right place?")

st.subheader("Environment")
st.write({
    "python_version": sys.version,
    "platform": platform.platform(),
    "cwd": os.getcwd(),
    "__file__": __file__,
})

st.subheader("Repo file tree (top-level, sorted)")
try:
    files = sorted(os.listdir("."))
    st.write(files)
except Exception as e:
    st.error(f"Cannot listdir('.'): {e}")

# Show contents of common entry points if present
candidates = ["streamlit_app.py", "app.py", "first_dynamic_model.py", "requirements.txt", "sample_first_panel.csv"]
st.subheader("Peek at common files (first 1000 chars)")
for c in candidates:
    if os.path.exists(c):
        st.markdown(f"**{c}**")
        try:
            if c.endswith(".csv"):
                with open(c, "r", encoding="utf-8", errors="ignore") as f:
                    st.code(f.read(400))
            else:
                with open(c, "r", encoding="utf-8", errors="ignore") as f:
                    st.code(f.read(1000))
        except Exception as e:
            st.error(f"Error reading {c}: {e}")
    else:
        st.write(f"{c} — not found")

st.divider()
st.info(textwrap.dedent(\"\"\"
Next steps:
1) If you don't see `streamlit_app.py` or `app.py` above, your app is pointed to the wrong folder.
2) Put your app file at the repo root or set 'Main file path' to the correct subfolder path (e.g., `main/streamlit_app.py`).
3) After fixing, set the Main file to your real app and redeploy.
\"\"\"))
