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

# Sidebar knobs
st.sidebar.header("Model Settings")
alpha = st.sidebar.slider("Alpha (persistence)", 0.0, 1.0, 0.75, 0.01)
lam = st.sidebar.slider("Lambda (EWMA toward composite)", 0.0, 1.0, 0.35, 0.01)
AG_down = st.sidebar.slider("Green if below (AG_down)", 0.0, 1.0, 0.30, 0.01)
GA_up   = st.sidebar.slider("Leave Green if above (GA_up)", 0.0, 1.0, 0.38, 0.01)
AR_up   = st.sidebar.slider("Enter Red if above (AR_up)", 0.0, 1.0, 0.62, 0.01)
RA_down = st.sidebar.slider("Leave Red if below (RA_down)", 0.0, 1.0, 0.54, 0.01)

model = FirstDynamicModel(alpha=alpha, lambda_ewma=lam,
                          thresholds={"AG_down":AG_down,"GA_up":GA_up,"AR_up":AR_up,"RA_down":RA_down})

df_geo = df[df["geo"] == geo].sort_values("date").reset_index(drop=True)
sim = model.simulate(df_geo)

st.subheader("Simulated (last 12 rows)")
st.dataframe(sim.tail(12))

# Plot
fig, ax = plt.subplots()
ax.plot(sim["date"], sim["F_t"], label="F_t")
ax.axhspan(0, AG_down, alpha=0.1, label="Green band")
ax.axhspan(AG_down, AR_up, alpha=0.1, label="Amber band")
ax.axhspan(AR_up, 1.0, alpha=0.1, label="Red band")
ax.set_ylim(0,1)
ax.set_title(f"Latent Risk over Time — {geo}")
ax.legend()
st.pyplot(fig)

st.caption("Tip: Upload your panel CSV with columns like Unemp_Norm, Evict_Norm, Food_Norm, Shutoff_Norm, Attendance_Norm, FRL_Norm, BenefitUptake, OutreachIntensity, CommunityPartnerCoverage.")
