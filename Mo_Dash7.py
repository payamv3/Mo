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
    sa_info = st.secrets["google_service_account"]
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

    # 🔙 BACK BUTTON
    if st.button("⬅️ Back"):
        st.session_state.step = 0
        st.session_state.device = None
        st.rerun()

    st.write(f"🔋 Does your **{st.session_state.device}** power on and does the battery last for daily use?")
    working_choice = st.radio("Select one:", ["Yes", "No/I do not know"], index=0)
    if st.button("Confirm Status") and working_choice:
        st.session_state.working = working_choice
        st.session_state.step = 2
        st.rerun()

# -------------------------------
# Step 2: Options (Resell / Donate / Recycle)
# -------------------------------
elif st.session_state.step == 2:

    # 🔙 BACK BUTTON
    if st.button("⬅️ Back"):
        st.session_state.step = 1
        st.session_state.working = None
        st.session_state.decision = None
        st.rerun()

    device = st.session_state.device
    working = st.session_state.working

    if device == "Unlisted Model":
        st.warning("📵 Your phone is not listed as a sellable model, so your options are donating or recycling.")
        working = "No"

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
        decision_options = ["Resell", "Donate", "Recycle"]
    else:
        decision_options = ["Donate", "Recycle"]

    decision_choice = st.radio(
        "What option would you like to explore for your device?",
        decision_options
    )

    if st.button("Confirm Choice") and decision_choice:
        st.session_state.decision = decision_choice
        st.session_state.step = 3
        st.rerun()

# -------------------------------
# Step 3: Wipe Instructions
# -------------------------------
elif st.session_state.step == 3 and not st.session_state.wipe_done:

    # 🔙 BACK BUTTON
    if st.button("⬅️ Back"):
        st.session_state.step = 2
        st.session_state.decision = None
        st.session_state.wipe_done = False
        st.session_state.unable_to_wipe_message = False
        st.rerun()

    device = st.session_state.device
    decision = st.session_state.decision

    st.markdown(f"🔒 Before you {decision.lower()} your device, please be sure to wipe your data")
    st.markdown(f"To remove data, see this guide:")

    if device == "Unlisted Model":
        st.markdown("#### For iPhones (iOS), this means disabling Find My on your device and then wiping it:")
        st.markdown("- Factory Reset: [Erase iPhone Guide](https://support.apple.com/en-us/109511)")
        st.markdown(f"Smart phones are usually linked to a user’s account, it cannot be used by someone else unless you remove it from list of devices owned.")
        st.markdown("- Disable Find My: [Apple Guide](https://support.apple.com/guide/icloud/remove-devices-and-items-from-find-my-mmdc23b125f6/icloud)\n")
        st.markdown("#### For Android phones:")
        st.markdown("- Factory Reset: [Erase Android Guide](https://support.google.com/android/answer/6088915?hl=en)")
        st.markdown(f"To remove from account:")
        st.markdown("- Android Account Removal: [Android Guide](https://support.google.com/accounts/answer/81987?hl=en&co=GENIE.Platform%3DAndroid)\n")
    else:
        os_type = "ios" if "iphone" in device.lower() else "android"
        if os_type == "ios":
            st.markdown("#### For iPhones (iOS):")
            st.markdown("- Factory Reset: [Erase iPhone Guide](https://support.apple.com/en-us/109511)")
            st.markdown("- Disable Find My: [Apple Guide](https://support.apple.com/guide/icloud/remove-devices-and-items-from-find-my-mmdc23b125f6/icloud)\n")
        else:
            st.markdown("#### For Android phones:")
            st.markdown("- Factory Reset: [Erase Android Guide](https://support.google.com/android/answer/6088915?hl=en)")
            st.markdown("- Account Removal: [Android Guide](https://support.google.com/accounts/answer/81987?hl=en&co=GENIE.Platform%3DAndroid)\n")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ I’ve wiped my device"):
            st.session_state.wipe_done = True
            st.rerun()
    with col2:
        if st.button("⚠️ I was unable to wipe"):
            st.session_state.unable_to_wipe_message = True

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
# Step 4: Show decision-specific links
# -------------------------------
elif st.session_state.step == 3 and st.session_state.wipe_done and not st.session_state.links_done:

    # 🔙 BACK BUTTON
    if st.button("⬅️ Back"):
        st.session_state.step = 3
        st.session_state.links_done = False
        st.rerun()

    device = st.session_state.device
    decision = st.session_state.decision

    st.markdown("🌍 Here are the links for your chosen action:")

    if decision == "Resell":
        st.markdown(
            f"- Resell your **{device}**: [BackMarket](https://www.backmarket.com/en-us/buyback/home), [Gazelle](https://www.gazelle.com/trade-in?_gl=...)"
        )
        st.markdown("By clicking one of the above websites:")
        st.markdown("You'll choose your model, receive a quote, get a prepaid box, and the phone will be inspected.")
    elif decision == "Donate":
        st.markdown(
            f"- Donate your **{device}**: [Goodwill](https://www.google.com/maps/search/Goodwill+near+me), [Salvation Army](https://www.google.com/maps/search/Salvation+Army+near+me)"
        )
    elif decision == "Recycle":
        st.markdown(f"- Recycle your **{device}**: [BestBuy Recycling](https://www.google.com/maps/search/BestBuy+near+me)")

    if st.button("✅ Done viewing links"):
        st.session_state.links_done = True
        st.session_state.step = 4
        st.rerun()

# -------------------------------
# Step 5: Prolific ID
# -------------------------------
elif st.session_state.step == 4 and st.session_state.prolific_id is None:

    # 🔙 BACK BUTTON
    if st.button("⬅️ Back"):
        st.session_state.step = 3
        st.session_state.links_done = False
        st.session_state.prolific_id = None
        st.rerun()

    prolific_id_input = st.text_input("🎯 Please enter your Prolific ID to finish:")

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
