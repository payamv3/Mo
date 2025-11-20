import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from sellcell_data import get_all_devices, get_sellcell_price

# -------------------------------------------------
# Google Sheets helper
# -------------------------------------------------
def get_google_sheet(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    sa_info = st.secrets["google_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(sa_info, scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1

def save_to_google_sheet(prolific_id, device, decision, working):
    sheet = get_google_sheet("ProlificIDs")
    sheet.append_row([prolific_id, device, decision, working])
    st.success("✅ Data saved to Google Sheet!")


# -------------------------------------------------
# Session State Defaults
# -------------------------------------------------
defaults = {
    "step": 0,
    "device": None,
    "working": None,
    "decision": None,
    "wipe_done": False,
    "unable_to_wipe_message": False,
    "links_done": False,
    "prolific_id": None,
    "back_request": False,
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


# -------------------------------------------------
# GLOBAL BACK HANDLER
# Runs before ANY rendering of steps
# -------------------------------------------------
if st.session_state.back_request:
    st.session_state.back_request = False  # clear click flag

    # Step 1 -> Step 0
    if st.session_state.step == 1:
        st.session_state.step = 0
        st.session_state.device = None

    # Step 2 -> Step 1
    elif st.session_state.step == 2:
        st.session_state.step = 1
        st.session_state.working = None
        st.session_state.decision = None

    # Step 3 (wipe instructions, not done yet) -> Step 2
    elif st.session_state.step == 3 and not st.session_state.wipe_done:
        st.session_state.step = 2
        st.session_state.wipe_done = False
        st.session_state.unable_to_wipe_message = False
        st.session_state.decision = None

    # Step 3 (wipe done but links not done) -> Step 3 parent
    elif st.session_state.step == 3 and st.session_state.wipe_done and not st.session_state.links_done:
        st.session_state.links_done = False
        st.session_state.step = 3

    # Step 4 (Prolific ID input) -> Step 3
    elif st.session_state.step == 4:
        st.session_state.prolific_id = None
        st.session_state.links_done = False
        st.session_state.step = 3

    st.rerun()


# -------------------------------------------------
# APP HEADER
# -------------------------------------------------
st.title("📱 Device Pathway Study")


# -------------------------------------------------
# STEP 0 — Select Device
# -------------------------------------------------
if st.session_state.step == 0:
    st.header("Which device are you checking?")
    devices = get_all_devices()
    selection = st.selectbox("Select your device:", devices)

    if st.button("Next"):
        st.session_state.device = selection
        st.session_state.step = 1
        st.rerun()


# -------------------------------------------------
# STEP 1 — Working or Not?
# -------------------------------------------------
elif st.session_state.step == 1:
    st.header("Is the device working?")

    if st.button("⬅️ Back"):
        st.session_state.back_request = True
        st.rerun()

    if st.button("Yes, it works"):
        st.session_state.working = "Working"
        st.session_state.step = 2
        st.rerun()

    if st.button("No, it does not work"):
        st.session_state.working = "Not Working"
        st.session_state.step = 2
        st.rerun()


# -------------------------------------------------
# STEP 2 — Decision: Resell / Donate / Recycle
# -------------------------------------------------
elif st.session_state.step == 2:
    st.header("What would you normally do with this device?")

    if st.button("⬅️ Back"):
        st.session_state.back_request = True
        st.rerun()

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("♻️ Recycle"):
            st.session_state.decision = "Recycle"
            st.session_state.step = 3
            st.rerun()
    with c2:
        if st.button("💝 Donate"):
            st.session_state.decision = "Donate"
            st.session_state.step = 3
            st.rerun()
    with c3:
        if st.button("💰 Resell"):
            st.session_state.decision = "Resell"
            st.session_state.step = 3
            st.rerun()


# -------------------------------------------------
# STEP 3A — Wipe Instructions (not done yet)
# -------------------------------------------------
elif st.session_state.step == 3 and not st.session_state.wipe_done:
    st.header("Wiping Instructions")

    if st.button("⬅️ Back"):
        st.session_state.back_request = True
        st.rerun()

    st.write("Please wipe your device following these instructions:")
    st.write("*[Insert wipe instructions here...]*")

    if st.button("I successfully wiped my device"):
        st.session_state.wipe_done = True
        st.session_state.step = 3
        st.rerun()

    if st.button("I cannot wipe my device"):
        st.session_state.unable_to_wipe_message = True
        st.session_state.step = 3
        st.rerun()


# -------------------------------------------------
# STEP 3B — Decision-specific Links (after wipe done)
# -------------------------------------------------
elif st.session_state.step == 3 and st.session_state.wipe_done and not st.session_state.links_done:

    if st.button("⬅️ Back"):
        st.session_state.back_request = True
        st.rerun()

    st.header("Next Steps")

    if st.session_state.decision == "Resell":
        price = get_sellcell_price(st.session_state.device)
        st.write(f"💰 Estimated Resale Value: **${price}**")
        st.write("Visit SellCell or another trusted marketplace.")

    elif st.session_state.decision == "Donate":
        st.write("💝 Suggested donation options:")
        st.write("- Local charities\n- Salvation Army\n- Goodwill")

    elif st.session_state.decision == "Recycle":
        st.write("♻️ Suggested recycling options:")
        st.write("- Best Buy Recycling\n- Local e-waste center")

    if st.button("Done reviewing"):
        st.session_state.links_done = True
        st.session_state.step = 4
        st.rerun()


# -------------------------------------------------
# STEP 4 — Enter Prolific ID
# -------------------------------------------------
elif st.session_state.step == 4:
    st.header("Enter your Prolific ID")

    if st.button("⬅️ Back"):
        st.session_state.back_request = True
        st.rerun()

    prolific_id = st.text_input("Your Prolific ID:")

    if st.button("Submit"):
        if prolific_id.strip() == "":
            st.error("Please enter your Prolific ID.")
        else:
            st.session_state.prolific_id = prolific_id
            save_to_google_sheet(
                prolific_id,
                st.session_state.device,
                st.session_state.decision,
                st.session_state.working,
            )
            st.success("🎉 Thank you! You are done.")
