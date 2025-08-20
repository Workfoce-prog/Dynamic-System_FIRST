# --- FIRST Dynamic System: single-file Streamlit app ---
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# ---------------- Model ----------------
def _sigmoid(x): 
    return 1/(1+np.exp(-x))

class FirstDynamicModel:
    def __init__(self, alpha=0.75, lambda_ewma=0.35,
                 thresholds=None, betas=None, gammas=None):
        self.alpha = float(alpha)
        self.lambda_ewma = float(lambda_ewma)
        self.thresholds = thresholds or {
            "AG_down": 0.30, "GA_up": 0.38, "AR_up": 0.62, "RA_down": 0.54
        }
        self.betas = betas or {
            "Unemp_Norm": 1.0, "Evict_Norm": 0.8, "Food_Norm": 0.7,
            "Shutoff_Norm": 0.5, "Attendance_Norm": 0.4, "FRL_Norm": 0.6
        }
        self.gammas = gammas or {
            "BenefitUptake": 0.9, "OutreachIntensity": 0.6, "CommunityPartnerCoverage": 0.5
        }

    def composite_index(self, row: pd.Series) -> float:
        z = 0.0
        for k, b in self.betas.items():  z += b * float(row.get(k, 0.0))
        for k, g in self.gammas.items(): z -= g * float(row.get(k, 0.0))
        return float(_sigmoid(z))

    def next_F(self, f_prev: float, row: pd.Series) -> float:
        comp   = self.composite_index(row)
        f_tilde = (1 - self.lambda_ewma) * f_prev + self.lambda_ewma * comp
        f_next  = self.alpha * f_prev + (1 - self.alpha) * f_tilde
        return float(np.clip(f_next, 0.0, 1.0))

    def rag_transition(self, f: float, last: str) -> str:
        th = self.thresholds
        if last == "Red":   return "Amber" if f < th["RA_down"] else "Red"
        if last == "Green": return "Amber" if f > th["GA_up"] else "Green"
        if f > th["AR_up"]: return "Red"
        if f < th["AG_down"]: return "Green"
        return "Amber"

    def simulate(self, df: pd.DataFrame, f0: float|None=None, rag0: str="Amber") -> pd.DataFrame:
        out = df.copy().reset_index(drop=True)
        if out.empty:
            return out.assign(F_t=[], RAG=[])
        first_row = out.iloc[0]
        f_prev = self.composite_index(first_row) if f0 is None else float(f0)
        rag_prev = rag0
        F, RAG = [], []
        for _, row in out.iterrows():
            f_next = self.next_F(f_prev, row)
            rag = self.rag_transition(f_next, rag_prev)
            F.append(f_next); RAG.append(rag)
            f_prev, rag_prev = f_next, rag
        out["F_t"] = F; out["RAG"] = RAG
        return out

# ---------------- App ----------------
st.set_page_config(page_title="FIRST Dynamic System", layout="wide")
st.title("FIRST Dynamic System — Risk & RAG Simulator")

# Sidebar controls
st.sidebar.header("Model Settings")
alpha = st.sidebar.slider("Alpha (persistence)", 0.0, 1.0, 0.75, 0.01)
lam   = st.sidebar.slider("Lambda (EWMA toward composite)", 0.0, 1.0, 0.35, 0.01)
AGd   = st.sidebar.slider("Green if below (AG_down)", 0.0, 1.0, 0.30, 0.01)
GAu   = st.sidebar.slider("Leave Green if above (GA_up)", 0.0, 1.0, 0.38, 0.01)
ARu   = st.sidebar.slider("Enter Red if above (AR_up)", 0.0, 1.0, 0.62, 0.01)
RAd   = st.sidebar.slider("Leave Red if below (RA_down)", 0.0, 1.0, 0.54, 0.01)

# Data load: CSV upload or bundled fallback
uploaded = st.file_uploader("Upload FIRST panel CSV", type=["csv"])
df = None
if uploaded is not None:
    try:
        df = pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"Could not read uploaded CSV: {e}")

if df is None:
    # Try a bundled CSV if present; else synthesize 8 rows so the app shows something
    try:
        df = pd.read_csv("sample_first_panel.csv")
        st.info("Using bundled sample_first_panel.csv")
    except Exception:
        st.warning("No CSV found; showing a tiny synthetic sample.")
        dates = pd.date_range("2024-01-01", periods=8, freq="MS")
        rows = []
        for geo in ["Hennepin","Ramsey"]:
            bias = 0.02 if geo=="Hennepin" else -0.01
            for d in dates:
                base = float(0.5 + bias + 0.1*np.sin(2*np.pi*(d.month/12.0)))
                rows.append({
                    "geo": geo, "date": d.date().isoformat(),
                    "Unemp_Norm": float(np.clip(base + np.random.normal(0,0.07),0,1)),
                    "Evict_Norm": float(np.clip(0.45 + np.random.normal(0,0.08),0,1)),
                    "Food_Norm": float(np.clip(0.40 + np.random.normal(0,0.08),0,1)),
                    "Shutoff_Norm": float(np.clip(0.30 + np.random.normal(0,0.06),0,1)),
                    "Attendance_Norm": float(np.clip(0.35 + np.random.normal(0,0.07),0,1)),
                    "FRL_Norm": float(np.clip(0.55 + np.random.normal(0,0.06),0,1)),
                    "BenefitUptake": float(np.clip(0.40 + np.random.normal(0,0.03),0, 1)),
                    "OutreachIntensity": float(np.clip(0.50 + np.random.normal(0,0.04),0, 1)),
                    "CommunityPartnerCoverage": float(np.clip(0.60 + np.random.normal(0,0.03),0,1)),
                })
        df = pd.DataFrame(rows)

# Basic checks
required_min = {"geo","date"}
if not required_min.issubset(df.columns):
    st.error("CSV must include at least: geo, date, plus *_Norm and intervention columns.")
    st.stop()

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])
geos = sorted(df["geo"].astype(str).unique().tolist())
if not geos:
    st.error("No geographies found in 'geo' column.")
    st.stop()

geo = st.selectbox("Geography", geos)

# Run model
model = FirstDynamicModel(
    alpha=alpha, lambda_ewma=lam,
    thresholds={"AG_down":AGd,"GA_up":GAu,"AR_up":ARu,"RA_down":RAd}
)
df_geo = df[df["geo"] == geo].sort_values("date").reset_index(drop=True)
sim = model.simulate(df_geo)

st.subheader("Simulated (last 12 rows)")
st.dataframe(sim.tail(12))

# Plot F_t with bands
fig, ax = plt.subplots()
ax.plot(sim["date"], sim["F_t"], label="F_t")
ax.axhspan(0, AGd, alpha=0.1, label="Green band")
ax.axhspan(AGd, ARu, alpha=0.1, label="Amber band")
ax.axhspan(ARu, 1.0, alpha=0.1, label="Red band")
ax.set_ylim(0, 1)
ax.set_title(f"Latent Risk over Time — {geo}")
ax.legend()
st.pyplot(fig)

st.caption("Upload panel CSV with columns like Unemp_Norm, Evict_Norm, Food_Norm, Shutoff_Norm, Attendance_Norm, FRL_Norm, BenefitUptake, OutreachIntensity, CommunityPartnerCoverage.")
