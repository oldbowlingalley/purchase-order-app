
import streamlit as st
import pandas as pd
from datetime import datetime

st.title("Purchase Order Creator")

# Session state for persistent item list
if 'items' not in st.session_state:
    st.session_state['items'] = []

# Supplier and date (entered once)
supplier = st.text_input("Supplier Name").strip().replace(" ", "")
date = st.date_input("Purchase Date", datetime.today())

# Item input section
st.subheader("Add Item")

description = st.text_input("Item Description")
cost = st.number_input("Item Cost (£)", min_value=0.0, step=0.01, format="%.2f")
location = st.text_input("Location", value="Location").strip().replace(" ", "")

if st.button("Add Item"):
    if description and cost > 0:
        item_number = len(st.session_state['items']) + 1
        date_str = date.strftime("%d%m%y")
        sku = f"{date_str}-{item_number}-{int(cost)}-{location}-{supplier}".replace(" ", "")
        st.session_state['items'].append({
            "Item No.": item_number,
            "Description": description,
            "Cost (£)": cost,
            "Location": location,
            "Supplier": supplier,
            "Date": date.strftime("%Y-%m-%d"),
            "SKU": sku
        })
        st.success(f"Added item {item_number}")
    else:
        st.warning("Please enter a description and cost.")

# Display current PO
if st.session_state['items']:
    st.subheader("Current Purchase Order")
    df = pd.DataFrame(st.session_state['items'])
    st.dataframe(df)

    # Save to CSV
    filename = f"PO-{date.strftime('%d%m%y')}-{supplier}.csv"
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", data=csv, file_name=filename, mime='text/csv')

    # Option to reset
    if st.button("Start New Purchase Order"):
        st.session_state['items'] = []
        st.experimental_rerun()
