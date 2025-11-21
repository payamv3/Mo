import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from sellcell_data import get_all_devices, get_sellcell_price

st.markdown(
    """
    <style>
    html, body, [class*="css"]  {
        font-size: 20px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------------
# Google Sheets helper
# -------------------------------
def get_google_sheet(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    sa_info = st.secrets["google_service_account"]  # Use Streamlit Secrets
    creds = ServiceAccountCredentials.from_json_keyfile_dict(sa_info, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1
    return sheet

def save_to_google_sheet(prolific_id, device, decision, working):
    sheet = get_google_sheet("ProlificIDs")
    sheet.append_row([prolific_id, device, decision, working])
    st.success("✅ Data saved to Google Sheet!")

# -------------------------------
# Session state
# -------------------------------
if "step" not in st.session_state:
    st.session_state.step = 0
if "device" not in st.session_state:
    st.session_state.device = None
if "working" not in st.session_state:
    st.session_state.working = None
if "decision" not in st.session_state:
    st.session_state.decision = None
if "wipe_done" not in st.session_state:
    st.session_state.wipe_done = False
if "links_done" not in st.session_state:
    st.session_state.links_done = False
if "unable_to_wipe_message" not in st.session_state:
    st.session_state.unable_to_wipe_message = False
if "prolific_id" not in st.session_state:
    st.session_state.prolific_id = None

st.title("♻️ Mo - The Sustainable Electronics Assistant")

# -------------------------------
# Step 0: Device selection
# -------------------------------
if st.session_state.step == 0:
    st.markdown('Hello and welcome! I am Mo, your guide for making sustainable choices with smartphones you no longer use at home. We will work together to find the best option, whether that is reselling, donating, or recycling your device. If you experience a timeout, just refresh the page. You will be done when all your questions are answered and you have entered your Prolific ID.')
    devices = sorted(get_all_devices())
    device_choice = st.selectbox("📱To get started, could you tell me about the smartphone you would like advice on?", [""] + devices)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Confirm Device") and device_choice != "":
            st.session_state.device = device_choice
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("📵 My phone is not in the list"):
            st.session_state.device = "Unlisted Model"
            st.session_state.working = "No Info"
            st.session_state.step = 2
            st.rerun()

# -------------------------------
# Step 1: Working / Not working
# -------------------------------
elif st.session_state.step == 1:
    st.write(f"🔋 Does your **{st.session_state.device}** power on and does the battery last for daily use?")
    working_choice = st.radio("Select one:", ["Yes", "No/I do not know"], index=0)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Confirm Status") and working_choice:
            st.session_state.working = working_choice
            st.session_state.step = 2
            st.rerun()
    with col2:
        if st.button("⬅️ Back"):
            st.session_state.step = 0
            st.rerun()

# -------------------------------
# Step 2: Show resale value + enriched info
# -------------------------------
elif st.session_state.step == 2:
    device = st.session_state.device
    working = st.session_state.working

    if device == "Unlisted Model":
        st.warning("📵 Your phone is not listed as a sellable model, so your options are donating or recycling.")
        working = "No"  # Disable resale path

    elif working == "Yes":
        conditions = ["Mint", "Good", "Fair", "Poor"]
        max_price = 0
        for cond in conditions:
            try:
                price_data = get_sellcell_price(device, cond)
                if price_data and price_data.get("price") and price_data["price"] > max_price:
                    max_price = price_data["price"]
            except Exception:
                continue

        if max_price > 0:
            st.success(f"💰 Your **{device}** can fetch up to **${max_price}** on resale!")
        else:
            st.info(f"ℹ️ Could not find resale price for {device}.")

    else:
        st.info("⚠️ Since your device is not working, resale or donation may not be possible.")

    st.markdown("### 💡 Here are your options:")

    if working == "Yes" and device != "Unlisted Model":
        st.markdown("**Resell:** You could earn some cash by selling your old phone if it is in working condition, and it can hold charge for a day's use.")
        st.markdown(
            f"The vendor will make you an offer assuming the battery is in good shape. They will check the battery upon receiving the phone and If it turns out that the battery is in poor condition, they will likely adjust the price. Try the following websites to get an estimate of your smartphone's current worth  \n"
            f'- [BackMarket](https://www.backmarket.com/en-us/buyback/home) (click "Trade-in" on uppe
