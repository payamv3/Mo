import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from sellcell_data import get_all_devices, get_sellcell_price

# Force page scroll to top on rerun
st.markdown("""
    <script>
        window.parent.document.querySelector('section.main').scrollTo(0, 0);
    </script>
""", unsafe_allow_html=True)

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

st.title("♻️ Hi, I'm Mo - The Sustainable Electronics Assistant")

# -------------------------------
# Step 0: Device selection
# -------------------------------
if st.session_state.step == 0:
    st.markdown('Hello and welcome! I am Mo, your guide for making sustainable choices with smartphones you no longer use at home. We will work together to find the best option, whether that is reselling, donating, or recycling your device. If you experience a timeout, just refresh the page. You will be done when all your questions are answered and you have entered your Prolific ID.')
    devices = sorted(get_all_devices())
    st.markdown("📱To get started, could you tell me about a smartphone that you are no longer using?")
    device_choice = st.selectbox("You can start typing the model of the smartphone, e.g. iPhone SE or Samsung Galaxy, etc.", [""] + devices)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Confirm Device") and device_choice != "":
            st.session_state.device = device_choice
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("📵 My phone is not in the list"):
            st.session_state.device = "Unlisted Model"
            st.session_state.step = 1  # go to working check
            st.rerun()

# -------------------------------
# Step 1: Working / Not working
# -------------------------------
elif st.session_state.step == 1:
    if st.button("⬅️ Back"):
        st.session_state.step = 0
        st.rerun()

    st.write(f"🔋 Does your **{st.session_state.device}** power on and does the battery last for daily use?")
    working_choice = st.radio("Select one:", ["Yes", "No/I do not know"], index=0)

    if st.button("Continue") and working_choice:
        st.session_state.working = working_choice
        st.session_state.step = 2
        st.rerun()

# -------------------------------
# Step 2: Resale/Donate/Recycle info
# -------------------------------
elif st.session_state.step == 2:
    if st.button("⬅️ Back"):
        st.session_state.step = 1
        st.rerun()

    device = st.session_state.device
    working = st.session_state.working

    if device == "Unlisted Model" and working == "Yes":
        st.warning("📵 Your phone is not listed as a sellable model, so resale is not available. You can donate or recycle it.")

    # Try resale price if listed and working
    if working == "Yes" and device != "Unlisted Model":
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

    st.markdown("### 💡 Here are your options:")

    if working == "Yes" and device != "Unlisted Model":
        show_resell = True
        show_donate = True
    elif device == "Unlisted Model":
        show_resell = False  # C) Unlisted + working → no resell
        show_donate = True
    else:
        show_resell = True
        show_donate = False

    if show_resell:
        st.markdown("**Resell:** You could earn some cash by selling your old phone.")
        st.markdown( f"**It’s easy to resell, either vendor will send you a box with prepaid postage.**")
        st.markdown(
            f"Try the following websites to get an estimate of your smartphone's current worth:  \n"
            f'- [BackMarket](https://www.backmarket.com/en-us/buyback/home) \n'
            f'- [Gazelle](https://www.gazelle.com/trade-in)\n'
        )
        st.markdown("Upon receiving the phone, the vendor will check battery condition, if it turns on, and if data has been wiped. If there are issues, they will likely adjust the offered price")

    if show_donate:
        st.markdown(
            f"**Donate:** Your used phone may not fetch a high price, but if still working and holding a charge, donating gives it a new life. "
            f"You can try donating your device, for example at:  \n"
            f"- [Goodwill](https://www.google.com/maps/search/Goodwill+near+me) \n"
            f"- [Salvation Army](https://www.google.com/maps/search/Salvation+Army+near+me)"
        )

    st.markdown(
        f"**Recycle:** If your phone does not work or if you do not want to resell or donate, you can bring it for recycling, for example at:  \n"
        f"- [Best Buy](https://www.google.com/maps/search/BestBuy+near+me)"
    )

    # Choice options
    if working == "Yes" and device != "Unlisted Model":
        decision_options = ["Resell", "Donate", "Recycle"]
    elif device == "Unlisted Model":
        decision_options = ["Donate","Recycle"]
    else:
        decision_options = ["Resell", "Recycle"]

    decision_choice = st.radio("What option would you like to explore for your device?", decision_options)

    if st.button("Confirm Choice") and decision_choice:
        st.session_state.decision = decision_choice
        # Non-working phones show warning first
        if working != "Yes":
            st.session_state.unable_to_wipe_message = True
            st.session_state.wipe_done = False
            st.session_state.step = 3
            st.rerun()
        else:
            st.session_state.step = 3
            st.rerun()

# -------------------------------
# Step 3: Wipe instructions / warning
# -------------------------------
elif st.session_state.step == 3 and not st.session_state.wipe_done:
    if st.session_state.unable_to_wipe_message:
        if st.button("⬅️ Back"):
            st.session_state.unable_to_wipe_message = False
            st.session_state.step = 2
            st.rerun()
        st.warning(
            "⚠️ Sometimes it becomes too difficult or impossible to erase your data. "
            "The phone may be non-functional. In these situations, you will have to decide for yourself "
            "if you feel comfortable recycling or reselling phones."
        )
        if st.button("✅ Proceed anyway"):
            st.session_state.wipe_done = True
            st.rerun()
        st.stop()

    if st.button("⬅️ Back"):
        st.session_state.step = 2
        st.rerun()

    device = st.session_state.device
    decision = st.session_state.decision

    st.markdown(f"🔒 Before you {decision.lower()} your device, please be sure to wipe your data")
    st.markdown("To remove data, see this guide:")

    # Show guides
    if device == "Unlisted Model" or "iphone" in device.lower():
        st.markdown("#### For iPhones (iOS), disable Find My and then wipe:")
        st.markdown("- Remove device from Find My: [Apple Guide](https://support.apple.com/guide/icloud/remove-devices-and-items-from-find-my-mmdc23b125f6/icloud)")
        st.markdown("- Erase All Content and Settings: [Erase iPhone Guide](https://support.apple.com/en-us/109511)")
    else:
        st.markdown("#### For Android phones, remove from Google account and then wipe:")
        st.markdown("- Removing smartphone from account: [Android Guide](https://support.google.com/accounts/answer/81987?hl=en&co=GENIE.Platform%3DAndroid)")
        st.markdown("- Erase All Content and Settings: [Erase Android Guide](https://support.google.com/android/answer/6088915?hl=en)")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ I’ve wiped my device"):
            st.session_state.wipe_done = True
            st.rerun()
    with col2:
        if not st.session_state.unable_to_wipe_message:
            if st.button("⚠️ I was unable to wipe"):
                st.session_state.unable_to_wipe_message = True
                st.rerun()

# -------------------------------
# Step 4: Show decision-specific links
# -------------------------------
elif st.session_state.step == 3 and st.session_state.wipe_done and not st.session_state.links_done:
    if st.button("⬅️ Back"):
        st.session_state.step = 3
        st.session_state.wipe_done = False
        st.rerun()

    device = st.session_state.device
    decision = st.session_state.decision
    st.markdown("🌍 Here are the links for your chosen action:")

    if decision == "Resell":
        st.markdown(f"- Resell your **{device}**: [BackMarket](https://www.backmarket.com/en-us/buyback/home), [Gazelle](https://www.gazelle.com/trade-in)")
    elif decision == "Donate":
        st.markdown(f"- Donate your **{device}**: [Goodwill](https://www.google.com/maps/search/Goodwill+near+me), [Salvation Army](https://www.google.com/maps/search/Salvation+Army+near+me)")
    elif decision == "Recycle":
        st.markdown(f"- Recycle your **{device}**: [BestBuy](https://www.google.com/maps/search/BestBuy+near+me)")

    if st.button("✅ Done viewing links"):
        st.session_state.links_done = True
        st.session_state.step = 4
        st.rerun()

# -------------------------------
# Step 5: Prolific ID submission
# -------------------------------
elif st.session_state.step == 4 and st.session_state.prolific_id is None:
    prolific_id_input = st.text_input("🎯 Please enter your Prolific ID to finish:")
    if prolific_id_input:
        save_to_google_sheet(prolific_id_input, st.session_state.device, st.session_state.decision, st.session_state.working)
        st.session_state.prolific_id = prolific_id_input
        st.success(f"🎉 Thank you! Your Prolific ID **{prolific_id_input}** has been recorded. Have a sustainable day!")

# -------------------------------
# Step 6: Already submitted
# -------------------------------
elif st.session_state.prolific_id is not None:
    st.success(f"✅ You already submitted Prolific ID: {st.session_state.prolific_id}")
