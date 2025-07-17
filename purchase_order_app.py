import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import tempfile

# Supplier mapping
default_supplier_map = {
    "Ian Smith": "IS",
    "Furniture Smalls": "SH",
    "Leroy Lucas": "LL",
    "Stafford": "ST",
    "Stickney Carboot": "SK",
    "Hemswell Market": "HM",
    "Lincoln Antiques Fair": "LA",
    "Runway Monday": "RM",
    "Adam Handley": "AH",
    "Private Seller": "PR",
    "Other": "OT",
    "Hemswell Antique Centre": "HA"
}

st.title("Purchase Order Creator")

# Session state
if 'items' not in st.session_state:
    st.session_state['items'] = []

if 'supplier_map' not in st.session_state:
    st.session_state['supplier_map'] = default_supplier_map.copy()

if 'form_count' not in st.session_state:
    st.session_state['form_count'] = 0

# Add supplier
with st.expander("➕ Add New Supplier"):
    new_supplier_name = st.text_input("New Supplier Name")
    new_supplier_code = st.text_input("Code to use in SKU (e.g., JS)")
    if st.button("Add Supplier"):
        if new_supplier_name and new_supplier_code:
            st.session_state['supplier_map'][new_supplier_name] = new_supplier_code.upper()
            st.success(f"Added new supplier: {new_supplier_name} → {new_supplier_code.upper()}")
        else:
            st.warning("Please enter both name and code.")

# Supplier and date
supplier_display = st.selectbox("Supplier", list(st.session_state['supplier_map'].keys()))
supplier = st.session_state['supplier_map'][supplier_display]
date = st.date_input("Purchase Date", datetime.today())
date_display = date.strftime("%d/%m/%Y")
date_str = date.strftime("%d%m%Y")

# Show running total
if st.session_state['items']:
    total_cost = sum(item['Cost (£)'] for item in st.session_state['items'])
    st.markdown(f"### 🧮 Running Total: £{total_cost:,.2f}")

st.subheader("Add Item")

# Fresh widget keys each time
desc_key = f"desc_{st.session_state['form_count']}"
cost_key = f"cost_{st.session_state['form_count']}"

description = st.text_input("Item Description", key=desc_key)
cost = st.number_input("Item Cost (£)", min_value=0.0, step=1.0, format="%.0f", key=cost_key)
location = st.text_input("Location", value="Location").strip().replace(" ", "")

# Add item
if st.button("Add Item"):
    if description and cost > 0:
        item_number = len(st.session_state['items']) + 1
        sku = f"{date_str}-{item_number}-{int(cost)}-{location}-{supplier}"
        st.session_state['items'].append({
            "Item No.": item_number,
            "Description": description,
            "Cost (£)": cost,
            "Location": location,
            "Supplier": supplier_display,
            "Date": date_display,
            "SKU": sku
        })
        st.session_state['form_count'] += 1  # force new keys
        st.rerun()
    else:
        st.warning("Please enter a description and cost.")

# Display PO
if st.session_state['items']:
    st.subheader("Current Purchase Order")
    df = pd.DataFrame(st.session_state['items'])

    # Add total row (fixed: use None instead of "")
    total = df["Cost (£)"].sum()
    total_row = pd.DataFrame([{
        "Item No.": None,
        "Description": "TOTAL",
        "Cost (£)": total,
        "Location": "",
        "Supplier": "",
        "Date": "",
        "SKU": ""
    }])
    df_total = pd.concat([df, total_row], ignore_index=True)
    st.dataframe(df_total)

    # CSV download
    filename = f"PO-{date_str}-{supplier}.csv"
    csv = df_total.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", data=csv, file_name=filename, mime='text/csv')

    # PDF generation
    def generate_pdf(dataframe):
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.set_auto_page_break(auto=True, margin=10)
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Purchase Order - {supplier_display} - {date_display}", ln=True, align="C")
        pdf.ln(5)

        pdf.set_font("Arial", "B", 10)
        headers = ["Item No.", "Description", "Cost (£)", "Location", "Supplier", "Date", "SKU"]
        col_widths = [20, 60, 25, 30, 40, 30, 60]

        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 8, header, border=1)
        pdf.ln()

        pdf.set_font("Arial", "", 10)
        for _, row in dataframe.iterrows():
            row_data = [
                str(row["Item No."]) if row["Item No."] is not None else "",
                row["Description"],
                str(row["Cost (£)"]),
                row["Location"],
                row["Supplier"],
                row["Date"],
                row["SKU"]
            ]
            for i, item in enumerate(row_data):
                pdf.cell(col_widths[i], 8, str(item)[:30], border=1)
            pdf.ln()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf.output(tmpfile.name)
            return tmpfile.name

    pdf_path = generate_pdf(df_total)
    with open(pdf_path, "rb") as f:
        st.download_button("📄 Download PDF", data=f, file_name=f"PO-{date_str}-{supplier}.pdf", mime="application/pdf")

    # Remove last item
    if st.button("❌ Remove Last Item") and st.session_state['items']:
        removed = st.session_state['items'].pop()
        st.success(f"Removed: {removed['Description']} (£{removed['Cost (£)']})")
        st.rerun()

    # Reset
    if st.button("Start New Purchase Order"):
        st.session_state['items'] = []
        st.session_state['form_count'] = 0
        st.rerun()
