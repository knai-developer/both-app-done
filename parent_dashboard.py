#type:ignore
import streamlit as st
import pandas as pd
from datetime import datetime
from parent_database import (
    get_student_fee_summary, 
    get_payment_history, 
    record_payment_request,
    get_payment_requests,
    export_payment_history_csv
)

def show_fee_summary(student_id):
    """Display fee summary for student"""
    summary = get_student_fee_summary(student_id)
    
    if not summary:
        st.error("Student fee details not found")
        return
    
    st.subheader(f"📚 {summary['student_name']} - Class {summary['class']}")
    
    # Fee breakdown
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Monthly Fee", f"₹{summary['monthly_fee']}")
    
    with col2:
        st.metric("Admission Fee", f"₹{summary['admission_fee']}")
    
    with col3:
        st.metric("Annual Fee", f"₹{summary['annual_fee']}")
    
    with col4:
        st.metric("Total Yearly Due", f"₹{summary['total_yearly_due']}")
    
    # Payment status
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Received", f"₹{summary['total_received']}", delta=f"{summary['percentage_paid']}%")
    
    with col2:
        st.metric("Balance Due", f"₹{summary['balance_due']}")
    
    with col3:
        status_color = "🟢" if summary['balance_due'] == 0 else "🟡" if summary['balance_due'] < 5000 else "🔴"
        st.metric("Status", status_color, delta="Paid" if summary['balance_due'] == 0 else "Pending")
    
    # Progress bar
    st.divider()
    progress = summary['percentage_paid'] / 100
    st.progress(progress, text=f"Payment Progress: {summary['percentage_paid']}%")

def show_payment_history(student_id):
    """Display payment history"""
    st.subheader("💳 Payment History")
    
    history = get_payment_history(student_id)
    
    if not history:
        st.info("No payment history found")
        return
    
    # Create DataFrame
    df = pd.DataFrame(history)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date', ascending=False)
    
    # Display table
    st.dataframe(
        df[['date', 'amount', 'payment_method', 'reference', 'remarks']].rename(
            columns={
                'date': 'Date',
                'amount': 'Amount (₹)',
                'payment_method': 'Method',
                'reference': 'Reference',
                'remarks': 'Remarks'
            }
        ),
        use_container_width=True,
        hide_index=True
    )
    
    # Download button
    csv_data = export_payment_history_csv(student_id)
    st.download_button(
        label="📥 Download Payment History",
        data=csv_data,
        file_name=f"payment_history_{student_id}.csv",
        mime="text/csv"
    )

def show_real_cash_details(student_id):
    """Display real cash payment details"""
    st.subheader("💰 Real Cash Payment Details")
    
    summary = get_student_fee_summary(student_id)
    
    if not summary:
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"""
        **Amount Due: ₹{summary['balance_due']}**
        
        Total Yearly Fee: ₹{summary['total_yearly_due']}
        Already Paid: ₹{summary['total_received']}
        """)
    
    with col2:
        st.warning(f"""
        **Payment Methods:**
        
        💵 Cash: Direct to school office
        🏦 Bank Transfer: Contact admin
        📱 Online: Via payment gateway
        """)
    
    st.divider()
    
    # School contact info
    st.subheader("📞 School Contact Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Office Hours:**")
        st.write("Monday - Friday: 9:00 AM - 4:00 PM")
        st.write("Saturday: 9:00 AM - 1:00 PM")
    
    with col2:
        st.write("**Contact Details:**")
        st.write("📧 Email: admin@school.com")
        st.write("📱 Phone: +91-XXXXXXXXXX")
        st.write("📍 Address: School Address Here")

def show_payment_setup(student_id, parent_email):
    """Display payment setup and request options"""
    st.subheader("🔧 Payment Setup & Request")
    
    summary = get_student_fee_summary(student_id)
    
    if not summary or summary['balance_due'] == 0:
        st.success("✅ All fees are paid! No payment required.")
        return
    
    st.info(f"Amount Due: ₹{summary['balance_due']}")
    
    # Payment type selection
    payment_type = st.radio(
        "Select Payment Type:",
        ["Monthly Payment", "Annual Payment", "Full Payment", "Custom Amount"]
    )
    
    # Calculate amount based on type
    if payment_type == "Monthly Payment":
        amount = summary['monthly_fee']
        description = f"Monthly fee for {summary['student_name']}"
    elif payment_type == "Annual Payment":
        amount = summary['monthly_fee'] * 12
        description = f"Annual fee for {summary['student_name']}"
    elif payment_type == "Full Payment":
        amount = summary['balance_due']
        description = f"Full outstanding balance for {summary['student_name']}"
    else:
        amount = st.number_input("Enter Amount (₹):", min_value=0, value=summary['balance_due'])
        description = f"Custom payment for {summary['student_name']}"
    
    # Payment method
    payment_method = st.selectbox(
        "Select Payment Method:",
        ["Cash", "Bank Transfer", "Online Payment", "Cheque"]
    )
    
    # Additional notes
    notes = st.text_area("Additional Notes (Optional):", placeholder="Any special instructions...")
    
    # Submit button
    if st.button("📤 Request Payment", use_container_width=True):
        if amount > 0:
            request_id = record_payment_request(
                student_id,
                parent_email,
                amount,
                payment_type,
                payment_method
            )
            st.success(f"✅ Payment request submitted! Request ID: {request_id}")
            st.info(f"School will contact you at {parent_email} to confirm payment details.")
        else:
            st.error("Please enter a valid amount")

def show_pending_requests(student_id):
    """Show pending payment requests"""
    st.subheader("⏳ Pending Payment Requests")
    
    requests = get_payment_requests(student_id)
    
    if not requests:
        st.info("No pending payment requests")
        return
    
    for req in requests:
        if req['status'] == 'pending':
            with st.container(border=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Request ID:** {req['request_id']}")
                    st.write(f"**Amount:** ₹{req['amount']}")
                
                with col2:
                    st.write(f"**Type:** {req['payment_type']}")
                    st.write(f"**Method:** {req['payment_method']}")
                
                with col3:
                    st.write(f"**Status:** 🟡 {req['status'].upper()}")
                    st.write(f"**Requested:** {req['requested_at']}")
