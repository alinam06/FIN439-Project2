"""Optional imports and source review shared by every dashboard section."""

from datetime import date
from zoneinfo import ZoneInfo

import streamlit as st

from src.data_workspace import load_workspace
from src.economic_signal import evaluate_signal
from src.stress_report import replay_bytes


def clear_session_files():
    for key in ("etf_upload", "signal_upload", "experiment_upload"):
        st.session_state.pop(key, None)
    st.session_state["data_import"] = "None"
    st.session_state["import_generation"] = st.session_state.get("import_generation", 0) + 1


def workspace_controls():
    with st.sidebar.expander("Advanced Data Management"):
        st.caption("Authorized repository files load automatically. Optional uploads override their matching "
                   "repository files for this session only. The app does not write uploaded files to disk.")
        choice = st.selectbox("Optional import", ("None", "ETF panel", "ALFRED archive", "Stress experiment"),
                              key="data_import")
        generation = st.session_state.get("import_generation", 0)

        def upload(label, suffix):
            return st.file_uploader(label, type=[suffix], key=f"{label}_{generation}")

        if choice == "ETF panel":
            prices = upload("Aligned adjusted prices", "csv")
            metadata = upload("Source metadata", "json")
            if prices is not None and metadata is not None:
                st.session_state["etf_upload"] = (prices.getvalue(), metadata.getvalue())
            else:
                st.caption("A complete pair replaces the current ETF source.")
        elif choice == "ALFRED archive":
            response = upload("ALFRED observations response", "json")
            manifest = upload("BAA10Y source manifest", "json")
            if response is not None and manifest is not None:
                st.session_state["signal_upload"] = (response.getvalue(), manifest.getvalue())
            else:
                st.caption("A complete pair replaces the current signal source.")
        elif choice == "Stress experiment":
            file = upload("Stress experiment JSON", "json")
            if file is not None:
                st.session_state["experiment_upload"] = file.getvalue()
        if any(key in st.session_state for key in ("etf_upload", "signal_upload", "experiment_upload")):
            st.button("Clear session imports", on_click=clear_session_files)

        data = load_workspace(etf_override=st.session_state.get("etf_upload"),
                              signal_override=st.session_state.get("signal_upload"))
        st.caption(f"ETF data · {data.etf_status}")
        st.caption(f"Credit signal · {data.signal_status}")
        reviewed = False
        if data.etf is not None:
            reviewed = st.checkbox("I reconciled the source, exchange dates, adjustments and distributions.",
                                   key=f"review_{data.etf.csv_hash}_{data.etf.metadata_hash}")
        signal_date = None
        if data.archive is not None:
            captured = data.archive.retrieved_at.astimezone(ZoneInfo("America/New_York")).date()
            signal_date = st.date_input("Signal decision date (end of day)",
                                        value=min(captured, data.archive.end, date.today()), max_value=date.today(),
                                        key=f"signal_date_{data.archive.fingerprint}")
    signal = evaluate_signal(data.archive, signal_date) if signal_date is not None else None
    return data, reviewed, signal_date, signal


def experiment_view():
    if "experiment_upload" not in st.session_state:
        return
    st.subheader("Imported experiment replay")
    st.caption("Uses the experiment’s recorded inputs. The active investor mandate is unchanged.")
    try:
        record = replay_bytes(st.session_state["experiment_upload"])
    except (ValueError, KeyError, TypeError, ArithmeticError, RecursionError) as error:
        st.warning(f"Experiment unavailable. {error}")
    else:
        st.json(record, expanded=False)
