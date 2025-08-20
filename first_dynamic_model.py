# ---------- Executive summary + margin-to-threshold gauge ----------

def summarize(ft, rag, series, AGd, GAu, ARu, RAd):
    """
    ft: latest F_t (float)
    rag: latest RAG label ("Green"/"Amber"/"Red")
    series: pandas Series of F_t over time
    returns: dict with summary, trend, margins, and next decision line
    """
    # 1) Trend over last ~3 months (fallback to last step)
    if len(series) >= 4:
        delta = float(series.iloc[-1] - series.iloc[-4])
        per_month = delta / 3.0
    elif len(series) >= 2:
        delta = float(series.iloc[-1] - series.iloc[-2])
        per_month = delta
    else:
        per_month, delta = 0.0, 0.0

    if per_month < -0.01:
        trend_word = "improving"
        trend_icon = "📉"
    elif per_month > 0.01:
        trend_word = "worsening"
        trend_icon = "📈"
    else:
        trend_word = "stable"
        trend_icon = "➖"

    # 2) Decide next relevant threshold & margin
    if rag == "Green":
        next_line = "Leave Green (GA↑)"
        margin = float(GAu - ft)  # positive = room to stay Green
        risk_level = "low" if margin > 0.05 else "watch"
        chip = "🟢 Green"
    elif rag == "Amber":
        # distance to Red and back to Green
        to_red   = float(ARu - ft)
        to_green = float(ft - AGd)
        # Which decision is closer?
        if abs(to_red) < abs(to_green):
            next_line, margin = "Enter Red (AR↑)", to_red
        else:
            next_line, margin = "Back to Green (AG↓)", to_green
        risk_level = "elevated"
        chip = "🟡 Amber"
    else:  # Red
        next_line = "Leave Red (RA↓)"
        margin = float(ft - RAd)  # positive = still above RA↓
        risk_level = "high"
        chip = "🔴 Red"

    # 3) Normalize a simple progress gauge to the next line
    #    (0 = line reached/past, 1 = comfortable distance)
    if rag == "Green":
        denom = max(GAu - 0.0, 1e-6)
        pct = max(0.0, min(1.0, (GAu - ft) / denom))
    elif rag == "Amber" and next_line.startswith("Enter Red"):
        denom = max(ARu - AGd, 1e-6)
        pct = max(0.0, min(1.0, (ARu - ft) / denom))
    elif rag == "Amber":  # back to green
        denom = max(ARu - AGd, 1e-6)
        pct = max(0.0, min(1.0, (ft - AGd) / denom))
    else:  # Red
        denom = max(1.0 - RAd, 1e-6)
        pct = max(0.0, min(1.0, (ft - RAd) / denom))

    return {
        "chip": chip,
        "trend_icon": trend_icon,
        "trend_word": trend_word,
        "per_month": per_month,
        "next_line": next_line,
        "margin": margin,
        "risk_level": risk_level,
        "pct_to_line": pct,
    }

last = sim.iloc[-1]
ft  = float(last["F_t"])
rag = str(last["RAG"])

summary = summarize(
    ft, rag, sim["F_t"],
    AGd, GAu, ARu, RAd
)

# ----- One-line executive summary -----
if summary["risk_level"] == "low":
    st.success(f"{summary['chip']}: {summary['trend_icon']} {summary['trend_word']}. "
               f"Margin to {summary['next_line']}: {summary['margin']:+.03f}")
elif summary["risk_level"] == "elevated":
    st.warning(f"{summary['chip']}: {summary['trend_icon']} {summary['trend_word']}. "
               f"Closest decision: {summary['next_line']} (margin {summary['margin']:+.03f})")
else:
    st.error(f"{summary['chip']}: {summary['trend_icon']} {summary['trend_word']}. "
             f"Next objective: {summary['next_line']} (need {abs(summary['margin']):.03f})")

# ----- Quick metrics -----
m1, m2, m3 = st.columns(3)
m1.metric("Current risk (Fₜ)", f"{ft:.02f}", f"{summary['per_month']:+.03f}/mo")
m2.metric("Next decision line", summary["next_line"])
m3.metric("Margin to line", f"{summary['margin']:+.03f}")

# ----- Simple gauge (distance to next line) -----
st.progress(int(round(summary["pct_to_line"] * 100)))
# ---------- Recommended actions (leadership-ready) ----------

NEAR = 0.03  # how close to a threshold counts as "near" (tune if you like)

def make_actions(ft, rag, per_month, AGd, GAu, ARu, RAd):
    actions = []

    # Helper booleans
    worsening = per_month >  0.01
    improving = per_month < -0.01
    near_leave_green = (rag == "Green") and ((GAu - ft) <= NEAR)
    near_enter_red   = (ARu - ft) <= NEAR  # works for Green/Amber
    near_back_green  = (rag == "Amber") and ((ft - AGd) <= NEAR)
    near_leave_red   = (rag == "Red")   and ((ft - RAd) <= NEAR)

    if rag == "Green":
        actions.append("Maintain baseline monitoring (monthly) and partner check-ins.")
        actions.append("Continue standard outreach cadence; keep navigator capacity warm.")
        if worsening or near_leave_green:
            actions.append("Pre-caution: +10% outreach (×1.10) for 2 months in top-need tracts.")
            actions.append("Light-touch eligibility texting to lift SNAP/WIC uptake +5% (×1.05).")
            actions.append("Set weekly review until risk is ≥0.05 below the Leave-Green line (GA↑).")

    elif rag == "Amber":
        actions.append("Activate heightened monitoring (weekly) and hotspot map for targeting.")
        actions.append("Increase outreach intensity +20% (×1.20) in top zip codes; reassign events to schools/clinics.")
        actions.append("Boost benefits navigation +10% (×1.10) completions using auto-booking/text nudges.")
        if worsening or near_enter_red:
            actions.append("Pre-stage surge: extend pantry hours, line up mobile distributions, pre-notify partners.")
        if improving or near_back_green:
            actions.append("Hold the line for 2 cycles; plan step-down if Fₜ < AG↓ for 2 consecutive months.")

    else:  # Red
        actions.append("Launch surge within 72 hours: extended pantry hours, mobile pop-ups, temp staffing.")
        actions.append("Targeted outreach +40% (×1.40) in top tracts; door-to-door or school-based events.")
        actions.append("Fast-track SNAP/WIC: goal +15% application completions in 30 days.")
        actions.append("Coordinate utilities/housing for shutoff & eviction prevention clinics.")
        actions.append("Daily monitoring; stand-down only after Fₜ < RA↓ for 2 consecutive months.")
        if improving and near_leave_red:
            actions.append("Plan Red→Amber transition: taper surge 25% while retaining navigator coverage.")

    return actions

actions = make_actions(
    ft=ft, rag=rag, per_month=summary["per_month"],
    AGd=AGd, GAu=GAu, ARu=ARu, RAd=RAd
)

st.subheader("Recommended actions")
for a in actions:
    st.markdown(f"- {a}")

# Optional: show a tiny action plan table leaders can screenshot
plan_rows = []
prio = 1
for a in actions:
    if "outreach" in a.lower():
        lever, target = "OutreachIntensity", "×1.10–×1.40 (by need)"
    elif "snap" in a.lower() or "wic" in a.lower() or "benefit" in a.lower():
        lever, target = "BenefitUptake", "+5–15% completions"
    elif "partner" in a.lower() or "mobile" in a.lower() or "pantry" in a.lower():
        lever, target = "CommunityPartnerCoverage", "+0.05–0.10 coverage"
    else:
        lever, target = "Governance/Monitoring", "Weekly / Daily"
    plan_rows.append({"Priority": prio, "Action": a, "Lever": lever, "Target": target})
    prio += 1

import pandas as pd
st.caption("Action plan (prioritized)")
st.dataframe(pd.DataFrame(plan_rows), use_container_width=True)
