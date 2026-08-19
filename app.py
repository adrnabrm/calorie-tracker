import streamlit as st

st.set_page_config(
    page_title="Calorie Tracker",
    page_icon="🥗",
    layout="centered",
)

page = st.navigation(
    [
        st.Page(
            "pages/3_Daily_Summary.py",
            title="Daily Summary",
            icon=":material/today:",
            default=True,
        ),
        st.Page(
            "pages/1_Log_Food.py",
            title="Log Food",
            icon=":material/restaurant:",
        ),
        st.Page(
            "pages/2_Scan_Label.py",
            title="Scan Label",
            icon=":material/document_scanner:",
        ),
        st.Page(
            "pages/4_Weight_Tracker.py",
            title="Weight Tracker",
            icon=":material/monitor_weight:",
        ),
        st.Page(
            "pages/5_Goals_Settings.py",
            title="Goals & Settings",
            icon=":material/settings:",
        ),
    ]
)
page.run()
