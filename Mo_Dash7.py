import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from sellcell_data import get_all_devices, get_sellcell_price

# -------------------------------
# CONFIG
# -------------------------------
JSON_KEY_FILE = "mo-the-chatbot-77d49f77ea5c.json"  # Path to your downloaded JSON key
SHEET_NAME = "ProlificIDs"             # Name of your Google Sheet

# -------------------------------
# Helper: Save data to Google Sheet
# -------------------------------
def save_to_google_sheet(prolific_id, device, decision, working):
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEY_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).sheet1
    sheet.append_row([prolific_id, device, decision, working])
    st.success("✅ Data saved to Google Sheet!")

# -------------------------------
# Session state setup
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

st.title("♻️ Device Sustainability ChatBot")

# -------------------------------
# Step 0: Device selection
# -------------------------------
if st.session_state.step == 0:
    devices = sorted(get_all_devices())
    device_choice = st.selectbox("📱 What device do you have?", [""] + devices)

    if st.button("Confirm Device") and device_choice != "":
        st.session_state.device = device_choice
        st.session_state.step = 1
        st.rerun()

# -------------------------------
# Step 1: Working / Not working
# -------------------------------
elif st.session_state.step == 1:
    st.write(f"🔋 Does your **{st.session_state.device}** power on and hold a charge?")
    working_choice = st.radio("Select one:", ["Yes", "No"], index=0)

    if st.button("Confirm Status") and working_choice:
        st.session_state.working = working_choice
        st.session_state.step = 2
        st.rerun()

# -------------------------------
# Step 2: Show resale value immediately if working
# -------------------------------
elif st.session_state.step == 2:
    device = st.session_state.device
    working = st.session_state.working

    if working == "Yes":
        # Show highest resale price
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

        # Ask what they want to do next
        decision_choice = st.radio(
            "What would you like to do with your device?",
            ["Resell", "Donate", "Recycle"]
        )
        if st.button("Confirm Choice") and decision_choice:
            st.session_state.decision = decision_choice
            st.session_state.step = 3
            st.rerun()

    else:
        # Device not working → only recycle
        st.info("⚠️ Since your device is not working, resale or donation may not be possible.")
        st.session_state.decision = "Recycle"
        st.session_state.step = 3
        st.rerun()

# -------------------------------
# Step 3: Wipe instructions with two buttons
# -------------------------------
elif st.session_state.step == 3 and not st.session_state.wipe_done:
    device = st.session_state.device
    decision = st.session_state.decision
    os_type = "ios" if "iphone" in device.lower() else "android"

    st.markdown(f"🔒 Before you {decision.lower()} your device, please wipe it securely:")
    if os_type == "ios":
        st.markdown(
            "- Disable Find My: [Apple Guide](https://support.apple.com/guide/icloud/remove-devices-and-items-from-find-my-mmdc23b125f6/icloud)\n"
            "- Factory Reset: [Erase iPhone Guide](https://support.apple.com/en-us/109511)"
        )
    else:
        st.markdown(
            "- Wipe instructions: [Android Guide](https://support.google.com/android/answer/6088915?hl=en)"
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ I’ve wiped my device"):
            st.session_state.wipe_done = True
            st.rerun()
    with col2:
        if st.button("⚠️ I was unable to wipe"):
            st.session_state.unable_to_wipe_message = True

    # Show the warning if user clicked "I was unable to wipe"
    if st.session_state.unable_to_wipe_message:
        st.warning(
            "⚠️ Sometimes it becomes too difficult or impossible to erase your data. "
            "The phone may be non-functional. In these situations, you will have to decide for yourself "
            "if you feel comfortable recycling or donating phones."
        )
        if st.button("✅ Proceed anyway"):
            st.session_state.wipe_done = True
            st.rerun()

# -------------------------------
# Step 4: Show decision-specific links after wiping
# -------------------------------
elif st.session_state.step == 3 and st.session_state.wipe_done and not st.session_state.links_done:
    device = st.session_state.device
    decision = st.session_state.decision

    st.markdown("🌍 Here are the links for your chosen action:")

    if decision == "Resell":
        st.markdown(
            f"- Resell your **{device}**: [BackMarket](https://www.backmarket.com), [Gazelle](https://www.gazelle.com)"
        )
    elif decision == "Donate":
        st.markdown(
            f"- Donate your **{device}**: "
            f"[Goodwill near me](https://www.google.com/maps/search/Goodwill+near+me), "
            f"[Salvation Army near me](https://www.google.com/maps/search/Salvation+Army+near+me)"
        )
    elif decision == "Recycle":
        st.markdown(
            f"- Recycle your **{device}**: [BestBuy Recycling](https://www.google.com/maps/search/BestBuy+near+me)"
        )

    if st.button("✅ Done viewing links"):
        st.session_state.links_done = True
        st.session_state.step = 4
        st.rerun()

# -------------------------------
# Step 5: Prolific ID
# -------------------------------
elif st.session_state.step == 4 and st.session_state.prolific_id is None:
    prolific_id_input = st.text_input("🎯 Please enter your Prolific ID to finish:", key="prolific_id_input")

    if prolific_id_input:
        save_to_google_sheet(
            prolific_id_input,
            st.session_state.device,
            st.session_state.decision,
            st.session_state.working,
        )
        st.session_state.prolific_id = prolific_id_input
        st.success(
            f"🎉 Thank you! Your Prolific ID **{prolific_id_input}** has been recorded. Have a sustainable day!"
        )

# -------------------------------
# Step 6: Already submitted
# -------------------------------
elif st.session_state.prolific_id is not None:
    st.success(f"✅ You already submitted Prolific ID: {st.session_state.prolific_id}")
