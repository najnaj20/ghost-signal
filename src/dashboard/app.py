"""Streamlit dashboard (FR-6). Run: streamlit run src/dashboard/app.py

Reads the real SQLite data through the same functions the API uses, so both apply the evidence rule.
"""
import sys
from html import escape
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # streamlit runs this file as a script

import pandas as pd
import streamlit as st

from src.api.main import COMPONENTS, entity, feed, unwatch, watch, watchlist
from src.db import connect

st.set_page_config(page_title="Ghost Signal", page_icon=":ghost:", layout="wide")
st.markdown("""<style>
h1, h2, h3 {color: #ff8c1a !important;}
a {color: #b48cff !important;}
.ev {border-left: 3px solid #ff8c1a; padding: 0.4rem 0.8rem; margin: 0.6rem 0; background: #1a1a24;}
.ev small {color: #a8a4b8;}
</style>""", unsafe_allow_html=True)


def con():
    return closing(connect())


st.title("Ghost Signal")
st.caption("Faint topics starting to move across news, papers, and forums. Ranked by Ghost Score, not by time. "
           "Every signal links to its evidence. Research tool only: no predictions, no trading advice.")

with con() as c:
    items = feed(c, 200)
    watched = {w["id"] for w in watchlist(c)}

if not items:
    st.warning("No scored entities in data/ghost-signal.db. Run the collector, extractor, and scorer first.")
    st.stop()


def table(rows):
    return pd.DataFrame([{"Ghost Score": r["ghost_score"], "Entity": r["name"], "Type": r["type"],
                          **{k.capitalize(): r["components"][k] for k in COMPONENTS},
                          "Mentions": r["mention_count"], "Watched": r["id"] in watched} for r in rows])


tab_feed, tab_watch = st.tabs(["Feed", f"Watchlist ({len(watched)})"])

with tab_feed:
    st.subheader("Feed")
    st.caption(f"Scores from {items[0]['score_date']}. Above 70 means Rising from the grave. Click a row.")
    pick = st.dataframe(table(items), hide_index=True, width="stretch", on_select="rerun",
                        selection_mode="single-row", height=420,
                        column_config={"Ghost Score": st.column_config.NumberColumn(format="%.1f")})
    rows = pick.selection.rows
    chosen = items[rows[0]] if rows else items[0]  # no click yet: show the top signal

    with con() as c:
        e = entity(c, chosen["id"])
    assert e, "feed item must resolve"  # chosen comes from feed(), so entity() finds it
    st.subheader(f"{e['name']} ({e['type']})")
    if e["label"]:
        st.markdown(f"**{e['label']}**")
    cols = st.columns(5)
    cols[0].metric("Ghost Score", e["ghost_score"])
    for col, k in zip(cols[1:], COMPONENTS):
        col.metric(k.capitalize(), e["components"][k])
    st.caption(f"First seen {e['first_seen_at']}. {e['mention_count']} mentions. "
               "Weights: novelty 0.4, velocity 0.3, corroboration 0.2, weirdness 0.1.")

    if e["id"] in watched:
        if st.button("Remove from watchlist", key=f"rm{e['id']}"):
            with con() as c:
                unwatch(c, e["id"])
            st.rerun()
    elif st.button("Add to watchlist", key=f"add{e['id']}"):
        with con() as c:
            watch(c, e["id"])
        st.rerun()

    st.markdown("### Evidence chain (oldest first)")
    for d in e["evidence_chain"]:
        d = {k: escape(str(v or "")) for k, v in d.items()}  # titles and quotes come from external sources
        url = d["url"] if d["url"].startswith(("http://", "https://")) else "#"
        st.markdown(f"<div class='ev'><small>{d['published_at']} | {d['source_type']} | {d['source']}</small><br>"
                    f"<a href='{url}' target='_blank'>{d['title'] or url}</a><br>"
                    f"&ldquo;{d['evidence_quote']}&rdquo;</div>", unsafe_allow_html=True)
    if e["claims"]:
        st.markdown("### Relations")
        for r in e["claims"]:
            st.markdown(f"- {r['claim_text']} ({r['relation_label']}): \"{r['evidence_quote']}\" "
                        f"[source]({r['url']})")

with tab_watch:
    with con() as c:
        wl = watchlist(c)
    if not wl:
        st.info("Watchlist is empty. Pick an entity in the feed and press Add to watchlist.")
    for w in wl:
        a, b = st.columns([5, 1])
        comp = ", ".join(f"{k} {v}" for k, v in w["components"].items())
        a.markdown(f"**{w['name']}** ({w['type']}): Ghost Score {w['ghost_score']} ({comp}). "
                   f"Latest evidence: \"{w['latest_evidence']['evidence_quote']}\" "
                   f"[source]({w['latest_evidence']['url']})")
        if b.button("Remove", key=f"wrm{w['id']}"):
            with con() as c:
                unwatch(c, w["id"])
            st.rerun()
