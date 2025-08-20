import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from first_dynamic_model import FirstDynamicModel

st.set_page_config(page_title="FIRST Dynamic System", layout="wide")
st.title("FIRST Dynamic System — Risk & RAG Simulator")

uploaded = st.file_uploader("Upload FIRST panel CSV", type=["csv"])
if uploaded is None:
    st.info("Using bundled sample_first_panel.csv")
    df = pd.read_csv("sample_first_panel.csv")
else:
    df = pd.read_csv(uploaded)

required_min = {"geo","date"}
if not required_min.issubset(df.columns):
    st.error("CSV must include at least: geo, date, plus *_Norm and intervention columns.")
    st.stop()

df["date"] = pd.to_datetime(df["date"])
geos = sorted(df["geo"].unique().tolist())
geo = st.selectbox("Geography", geos)

model = FirstDynamicModel()
df_geo = df[df["geo"] == geo].sort_values("date").reset_index(drop=True)
sim = model.simulate(df_geo)

st.subheader("Simulated (last 12 rows)")
st.dataframe(sim.tail(12))

fig, ax = plt.subplots()
ax.plot(sim["date"], sim["F_t"], label="F_t")
th = model.thresholds
ax.axhspan(0, th["AG_down"], alpha=0.1, label="Green band")
ax.axhspan(th["AG_down"], th["AR_up"], alpha=0.1, label="Amber band")
ax.axhspan(th["AR_up"], 1.0, alpha=0.1, label="Red band")
ax.set_ylim(0,1)
ax.set_title(f"Latent Risk over Time — {geo}")
ax.legend()
st.pyplot(fig)
