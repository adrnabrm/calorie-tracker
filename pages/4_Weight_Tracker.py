from datetime import datetime
from zoneinfo import ZoneInfo

import altair as alt
import pandas as pd
import streamlit as st
from models.schemas import WeightLog
from services.db import delete_weight_log, get_all_weight_logs, upsert_weight_log

st.set_page_config(page_title="Weight Tracker", layout="centered")
st.title("Weight Tracker")


@st.dialog("Are you sure?")
def confirm_delete_weight(log_id: str, log_date: str, weight: float) -> None:
    st.write(f"Delete **{log_date}** ({weight:.1f} lbs)?")
    with st.container(horizontal=True):
        if st.button("Cancel", key="wt_del_cancel"):
            st.rerun()
        if st.button("Delete", type="primary", key="wt_del_ok"):
            delete_weight_log(log_id)
            st.rerun()


_today = datetime.now(ZoneInfo(st.context.timezone or "UTC")).date()

with st.form("weight_form"):
    log_date = st.date_input("Date", value=_today)
    weight = st.number_input(
        "Weight (lbs)",
        min_value=0.1,
        value=None,
        step=0.1,
        format="%.1f",
        placeholder="e.g. 180.0",
    )
    submitted = st.form_submit_button("Save")

if submitted:
    if weight is None:
        st.warning("Enter a weight.")
    else:
        upsert_weight_log(
            WeightLog(date=log_date.isoformat(), weight=float(weight))
        )
        st.success("Weight saved.")

logs = get_all_weight_logs()
if not logs:
    st.info("No weight logged yet.")
else:
    latest = logs[-1]
    latest_weight = float(latest["weight"])
    delta = None
    if len(logs) >= 2:
        delta = latest_weight - float(logs[-2]["weight"])
    st.metric(
        "Latest",
        f"{latest_weight:.1f} lbs",
        delta=None if delta is None else round(delta, 1),
        delta_color="inverse",
    )
    chart = (
        alt.Chart(
            pd.DataFrame(
                [{"date": row["date"], "weight": float(row["weight"])} for row in logs]
            )
        )
        .mark_line(point=True)
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y(
                "weight:Q",
                title="Weight (lbs)",
                scale=alt.Scale(domain=[150, 200], nice=False, zero=False),
            ),
        )
    )
    st.altair_chart(chart, width="stretch")
    st.subheader("Logged")
    to_delete = None
    for row in reversed(logs):
        w = float(row["weight"])
        with st.container(horizontal=True, vertical_alignment="center"):
            st.write(f"**{row['date']}** — {w:.1f} lbs")
            if st.button("Delete", key=f"del_{row['id']}"):
                to_delete = (row["id"], row["date"], w)
    if to_delete:
        confirm_delete_weight(*to_delete)
