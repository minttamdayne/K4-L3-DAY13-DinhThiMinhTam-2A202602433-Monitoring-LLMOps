"""Local six-panel dashboard backed by data/logs.jsonl.

Run with: streamlit run scripts/dashboard.py
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "data" / "logs.jsonl"
CONFIG_PATH = ROOT / "config" / "dashboard.yaml"


@st.cache_data(ttl=30)
def load_data() -> tuple[pd.DataFrame, dict]:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))["dashboard"]
    rows = [json.loads(line) for line in LOG_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame["ts"] = pd.to_datetime(frame["ts"], utc=True, errors="coerce")
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=config["time_range_minutes"])
        frame = frame[frame["ts"] >= cutoff].copy()
    return frame, config


def threshold(panel: dict) -> str:
    t = panel["threshold"]
    return f"Threshold: {t['aggregation']} {t['operator']} {t['value']} {panel['unit']}"


st.set_page_config(page_title="Day 13 Monitoring & LLMOps", layout="wide")
st.title("K4-L3A Day 13 Monitoring & LLMOps")
st.caption("Source: data/logs.jsonl · rolling time range: 60 minutes · refresh: 30 seconds")

try:
    df, dashboard = load_data()
except FileNotFoundError:
    st.error("data/logs.jsonl chưa tồn tại. Chạy API và scripts/load_test.py trước.")
    st.stop()

panels = {panel["id"]: panel for panel in dashboard["panels"]}
responses = df[df.get("event", pd.Series(dtype=str)) == "response_sent"] if not df.empty else df
requests = df[df.get("event", pd.Series(dtype=str)) == "request_received"] if not df.empty else df
failures = df[df.get("event", pd.Series(dtype=str)) == "request_failed"] if not df.empty else df

left, right = st.columns(2)
with left:
    p = panels["latency"]
    st.subheader(p["title"])
    if not responses.empty:
        values = responses["latency_ms"].dropna()
        ttft = responses["ttft_ms"].dropna()
        st.metric("P50 / P95 / P99 (ms)", f"{values.quantile(.50):.0f} / {values.quantile(.95):.0f} / {values.quantile(.99):.0f}")
        st.metric("TTFT P95 (ms)", f"{ttft.quantile(.95):.0f}")
        st.line_chart(responses.set_index("ts")[["latency_ms", "ttft_ms"]])
    st.caption(f"Unit: {p['unit']} · {threshold(p)}")

with right:
    p = panels["traffic"]
    st.subheader(p["title"])
    st.metric("Requests", len(requests))
    st.metric("Rate (requests/min)", f"{len(requests) / max(1, dashboard['time_range_minutes']):.2f}")
    if not requests.empty:
        st.bar_chart(requests.set_index("ts").resample("1min").size())
    st.caption(f"Unit: {p['unit']} · {threshold(p)}")

left, right = st.columns(2)
with left:
    p = panels["errors"]
    st.subheader(p["title"])
    error_rate = len(failures) / max(1, len(requests)) * 100
    retrieval = responses["tool_success"].dropna().astype(bool).mean() * 100 if "tool_success" in responses else 0
    st.metric("Error rate", f"{error_rate:.2f}%")
    st.metric("Retrieval success", f"{retrieval:.2f}%")
    if not failures.empty and "error_type" in failures:
        st.dataframe(failures["error_type"].value_counts().rename("count"))
    st.caption(f"Unit: {p['unit']} · {threshold(p)}")

with right:
    p = panels["cost"]
    st.subheader(p["title"])
    total = responses["cost_usd"].sum() if "cost_usd" in responses else 0
    st.metric("Total cost", f"${total:.4f}")
    if not responses.empty:
        st.bar_chart(responses.set_index("ts")["cost_usd"].resample("1min").sum())
    st.caption(f"Unit: {p['unit']} · {threshold(p)}")

left, right = st.columns(2)
with left:
    p = panels["tokens"]
    st.subheader(p["title"])
    st.metric("Input tokens", f"{responses.get('tokens_in', pd.Series(dtype=float)).sum():.0f}")
    st.metric("Output tokens", f"{responses.get('tokens_out', pd.Series(dtype=float)).sum():.0f}")
    st.caption(f"Unit: {p['unit']} · {threshold(p)}")

with right:
    p = panels["quality"]
    st.subheader(p["title"])
    quality = responses["quality_score"].mean() if "quality_score" in responses and not responses.empty else 0
    st.metric("Mean quality proxy", f"{quality:.2f}")
    st.progress(float(max(0, min(1, quality))))
    st.caption(f"Unit: {p['unit']} · SLO line: {p['threshold']['value']}")
