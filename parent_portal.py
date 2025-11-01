# [file name]: parent_portal.py
# [file content begin]
# type:ignore
import streamlit as st
import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from parent_auth import (
    authenticate_parent, 
    create_parent_account, 
    check_parent_authentication,
    logout_parent
)
from database import load_school_config, load_data, load_student_details, load_student_fees
from utils import format_currency

# Page configuration for parent portal
st.set_page_config(
    page_title="Parent Portal - School Fees Management",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_parent_info(email):
    """Get parent information from database"""
    try:
        with open("parents.json", 'r') as f:
            parents = json.load(f)
        
        if email in parents:
            return parents[email]
        return {}
    except Exception as e:
        print(f"Error getting parent info: {str(e)}")
        return {}

def get_parent_students(email):
    """Get student IDs linked to parent"""
    try:
        with open("parents.json", 'r') as f:
            parents = json.load(f)
        
        if email in parents:
            return parents[email].get('student_ids', [])
        return []
    except Exception as e:
        print(f"Error getting student list: {str(e)}")
        return []

def get_student_monthly_fee(student_id):
    """Get student's monthly fee amount"""
    try:
        student_fees = load_student_fees()
        if student_id in student_fees:
            return student_fees[student_id].get('monthly_fee', 3000)
        
        # Default fee if not set
        from database import load_default_fees
        default_fees = load_default_fees()
        return default_fees.get('monthly_fee', 3000)
    except:
        return 3000

def get_student_fee_details(student_id):
    """Get comprehensive fee details for student including paid/unpaid months"""
    try:
        df = load_data()
        student_details = load_student_details()
        
        if student_id not in student_details:
            return None
        
        student_info = student_details[student_id]
        student_records = df[df['ID'] == student_id]
        
        # All months in academic year
        all_months = [
            "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER",
            "OCTOBER", "NOVEMBER", "DECEMBER", "JANUARY", "FEBRUARY", "MARCH"
        ]
        
        # Get monthly fee amount
        monthly_fee_amount = get_student_monthly_fee(student_id)
        
        # Calculate paid and unpaid months
        paid_months = []
        unpaid_months = []
        
        for month in all_months:
            month_records = student_records[
                (student_records['Month'] == month) & 
                (student_records['Monthly Fee'] > 0)
            ]
            if not month_records.empty:
                paid_months.append({
                    'month': month,
                    'amount': month_records['Monthly Fee'].iloc[0],
                    'date': month_records['Date'].iloc[0] if 'Date' in month_records.columns else 'N/A'
                })
            else:
                unpaid_months.append(month)
        
        # Calculate totals
        total_monthly = student_records['Monthly Fee'].sum() if not student_records.empty else 0
        total_annual = student_records['Annual Charges'].sum() if not student_records.empty else 0
        total_admission = student_records['Admission Fee'].sum() if not student_records.empty else 0
        total_received = student_records['Received Amount'].sum() if not student_records.empty else 0
        
        # Calculate outstanding
        total_paid_months = len(paid_months)
        total_unpaid_months = len(unpaid_months)
        total_monthly_due = monthly_fee_amount * 12
        total_annual_due = student_records['Annual Charges'].max() if not student_records.empty else 0
        total_admission_due = student_records['Admission Fee'].max() if not student_records.empty else 0
        
        total_due = total_monthly_due + total_annual_due + total_admission_due
        balance_due = max(0, total_due - total_received)
        
        return {
            "student_id": student_id,
            "student_name": student_info.get('student_name', 'N/A'),
            "father_name": student_info.get('father_name', 'N/A'),
            "class": student_info.get('class_category', 'N/A'),
            "phone": student_info.get('phone', 'N/A'),
            "monthly_fee": monthly_fee_amount,
            "total_monthly": total_monthly,
            "total_annual": total_annual,
            "total_admission": total_admission,
            "total_received": total_received,
            "total_due": total_due,
            "balance_due": balance_due,
            "percentage_paid": round((total_received / total_due * 100) if total_due > 0 else 0, 1),
            "paid_months": paid_months,
            "unpaid_months": unpaid_months,
            "total_paid_months": total_paid_months,
            "total_unpaid_months": total_unpaid_months
        }
    except Exception as e:
        print(f"Error getting fee details: {str(e)}")
        return None

def add_back_button():
    """Add back button to return to dashboard"""
    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        st.session_state.current_parent_page = "📊 Dashboard"
        st.rerun()

def show_bank_transfer_payment(student_id, fee_details):
    """Show bank transfer payment interface"""
    try:
        from payment_config import PaymentConfig
        config_manager = PaymentConfig()
        config = config_manager.load_config()
        bank_config = config.get('bank_details', {})
        
        st.markdown(f"""
        ### 🏦 Bank Transfer Instructions:
        
        1. **Transfer amount** to school bank account
        2. **Use Student ID** as reference: **`{student_id}`**
        3. **Save transaction screenshot/receipt**
        4. **Payment verified** within 24 hours
        
        **Bank Details:**
        - **Bank:** {bank_config.get('bank_name', 'Contact School')}
        - **Account:** {bank_config.get('account_number', 'Contact School')}
        - **Title:** {bank_config.get('account_title', 'Contact School')}
        - **IBAN:** {bank_config.get('iban', 'Contact School')}
        """)
        
        # Payment options
        st.subheader("💳 Payment Options")
        
        payment_option = st.radio(
            "Select what you want to pay:",
            ["Pay Balance Due", "Pay Specific Month", "Pay Custom Amount"]
        )
        
        if payment_option == "Pay Balance Due":
            amount = fee_details['balance_due']
        elif payment_option == "Pay Specific Month":
            if fee_details['unpaid_months']:
                selected_month = st.selectbox("Select Month to Pay:", fee_details['unpaid_months'])
                amount = fee_details['monthly_fee']
                st.info(f"Amount to pay for {selected_month}: {format_currency(amount)}")
            else:
                st.success("All months are already paid!")
                amount = 0
        else:
            amount = st.number_input(
                "Enter Amount to Pay:",
                min_value=1,
                max_value=int(fee_details['balance_due']),
                value=int(fee_details['balance_due'])
            )
        
        # Payment confirmation form
        with st.form("bank_payment_form"):
            st.write("**After making payment, fill this form:**")
            
            transaction_id = st.text_input("Transaction ID*", placeholder="e.g., TXN123456789")
            payment_date = st.date_input("Payment Date*", value=datetime.now())
            
            submitted = st.form_submit_button("📤 Submit Bank Payment", use_container_width=True)
            
            if submitted:
                if not transaction_id:
                    st.error("❌ Please enter Transaction ID")
                elif amount <= 0:
                    st.error("❌ Please select a valid amount to pay")
                else:
                    # Save payment record
                    try:
                        from real_payment_system import RealPaymentSystem
                        payment_system = RealPaymentSystem()
                        
                        success = payment_system.handle_parent_payment(
                            student_id=student_id,
                            student_name=fee_details['student_name'],
                            amount=amount,
                            payment_method="Bank Transfer",
                            transaction_id=transaction_id
                        )
                        
                        if success:
                            st.success("""
                            ✅ Payment submitted successfully!
                            
                            **Next Steps:**
                            1. School will verify your payment
                            2. You'll receive confirmation within 24 hours
                            3. Check payment history for updates
                            
                            Thank you for your payment!
                            """)
                            st.balloons()
                        else:
                            st.error("Failed to save payment record")
                    except Exception as e:
                        st.error(f"Payment processing error: {str(e)}")
    except Exception as e:
        st.error(f"Error loading bank transfer: {str(e)}")

def show_jazzcash_payment(student_id, fee_details):
    """Show JazzCash payment interface"""
    try:
        from payment_config import PaymentConfig
        config_manager = PaymentConfig()
        config = config_manager.load_config()
        jazzcash_config = config.get('jazzcash', {})
        
        st.markdown(f"""
        ### 📱 JazzCash Instructions:
        
        1. **Send payment** to school JazzCash number
        2. **Use Student ID** as reference: **`{student_id}`**
        3. **Save transaction ID**
        4. **Payment verified** within 24 hours
        
        **JazzCash Details:**
        - **Number:** {jazzcash_config.get('account_number', 'Contact School')}
        - **Name:** {jazzcash_config.get('account_name', 'Contact School')}
        """)
        
        # Payment options
        st.subheader("💳 Payment Options")
        
        payment_option = st.radio(
            "Select what you want to pay:",
            ["Pay Balance Due", "Pay Specific Month", "Pay Custom Amount"],
            key="jazzcash_option"
        )
        
        if payment_option == "Pay Balance Due":
            amount = fee_details['balance_due']
        elif payment_option == "Pay Specific Month":
            if fee_details['unpaid_months']:
                selected_month = st.selectbox("Select Month to Pay:", fee_details['unpaid_months'], key="jazzcash_month")
                amount = fee_details['monthly_fee']
                st.info(f"Amount to pay for {selected_month}: {format_currency(amount)}")
            else:
                st.success("All months are already paid!")
                amount = 0
        else:
            amount = st.number_input(
                "Enter Amount to Pay:",
                min_value=1,
                max_value=int(fee_details['balance_due']),
                value=int(fee_details['balance_due']),
                key="jazzcash_amount"
            )
        
        # Payment confirmation form
        with st.form("jazzcash_payment_form"):
            st.write("**After making payment, fill this form:**")
            
            transaction_id = st.text_input("JazzCash Transaction ID*", placeholder="e.g., TXN123456789")
            payment_date = st.date_input("Payment Date*", value=datetime.now(), key="jazzcash_date")
            
            submitted = st.form_submit_button("📤 Submit JazzCash Payment", use_container_width=True)
            
            if submitted:
                if not transaction_id:
                    st.error("❌ Please enter Transaction ID")
                elif amount <= 0:
                    st.error("❌ Please select a valid amount to pay")
                else:
                    # Save payment record
                    try:
                        from real_payment_system import RealPaymentSystem
                        payment_system = RealPaymentSystem()
                        
                        success = payment_system.handle_parent_payment(
                            student_id=student_id,
                            student_name=fee_details['student_name'],
                            amount=amount,
                            payment_method="JazzCash",
                            transaction_id=transaction_id
                        )
                        
                        if success:
                            st.success("""
                            ✅ JazzCash payment submitted successfully!
                            
                            **Next Steps:**
                            1. School will verify your payment
                            2. You'll receive confirmation within 24 hours
                            3. Check payment history for updates
                            
                            Thank you for your payment!
                            """)
                            st.balloons()
                        else:
                            st.error("Failed to save payment record")
                    except Exception as e:
                        st.error(f"Payment processing error: {str(e)}")
    except Exception as e:
        st.error(f"Error loading JazzCash: {str(e)}")

def show_easypaisa_payment(student_id, fee_details):
    """Show EasyPaisa payment interface"""
    try:
        from payment_config import PaymentConfig
        config_manager = PaymentConfig()
        config = config_manager.load_config()
        easypaisa_config = config.get('easypaisa', {})
        
        st.markdown(f"""
        ### 📲 EasyPaisa Instructions:
        
        1. **Send payment** to school EasyPaisa number
        2. **Use Student ID** as reference: **`{student_id}`**
        3. **Save transaction ID**
        4. **Payment verified** within 24 hours
        
        **EasyPaisa Details:**
        - **Number:** {easypaisa_config.get('account_number', 'Contact School')}
        - **Name:** {easypaisa_config.get('account_name', 'Contact School')}
        """)
        
        # Payment options
        st.subheader("💳 Payment Options")
        
        payment_option = st.radio(
            "Select what you want to pay:",
            ["Pay Balance Due", "Pay Specific Month", "Pay Custom Amount"],
            key="easypaisa_option"
        )
        
        if payment_option == "Pay Balance Due":
            amount = fee_details['balance_due']
        elif payment_option == "Pay Specific Month":
            if fee_details['unpaid_months']:
                selected_month = st.selectbox("Select Month to Pay:", fee_details['unpaid_months'], key="easypaisa_month")
                amount = fee_details['monthly_fee']
                st.info(f"Amount to pay for {selected_month}: {format_currency(amount)}")
            else:
                st.success("All months are already paid!")
                amount = 0
        else:
            amount = st.number_input(
                "Enter Amount to Pay:",
                min_value=1,
                max_value=int(fee_details['balance_due']),
                value=int(fee_details['balance_due']),
                key="easypaisa_amount"
            )
        
        # Payment confirmation form
        with st.form("easypaisa_payment_form"):
            st.write("**After making payment, fill this form:**")
            
            transaction_id = st.text_input("EasyPaisa Transaction ID*", placeholder="e.g., TXN123456789")
            payment_date = st.date_input("Payment Date*", value=datetime.now(), key="easypaisa_date")
            
            submitted = st.form_submit_button("📤 Submit EasyPaisa Payment", use_container_width=True)
            
            if submitted:
                if not transaction_id:
                    st.error("❌ Please enter Transaction ID")
                elif amount <= 0:
                    st.error("❌ Please select a valid amount to pay")
                else:
                    # Save payment record
                    try:
                        from real_payment_system import RealPaymentSystem
                        payment_system = RealPaymentSystem()
                        
                        success = payment_system.handle_parent_payment(
                            student_id=student_id,
                            student_name=fee_details['student_name'],
                            amount=amount,
                            payment_method="EasyPaisa",
                            transaction_id=transaction_id
                        )
                        
                        if success:
                            st.success("""
                            ✅ EasyPaisa payment submitted successfully!
                            
                            **Next Steps:**
                            1. School will verify your payment
                            2. You'll receive confirmation within 24 hours
                            3. Check payment history for updates
                            
                            Thank you for your payment!
                            """)
                            st.balloons()
                        else:
                            st.error("Failed to save payment record")
                    except Exception as e:
                        st.error(f"Payment processing error: {str(e)}")
    except Exception as e:
        st.error(f"Error loading EasyPaisa: {str(e)}")

def show_parent_login():
    """Show parent login/signup interface"""
    
    # School header
    school_config = load_school_config()
    school_name = school_config.get("school_name", "School Name")
    
    st.markdown(f"""
    <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; margin-bottom: 30px;">
        <h1 style="margin: 0; font-size: 2.5rem;">🏫 {school_name}</h1>
        <h2 style="margin: 0; font-size: 1.5rem;">Parent Portal</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=150)
        st.markdown("""
        <div style="text-align: center;">
            <h3>📱 Parent Features</h3>
            <p>• View Fee Details</p>
            <p>• Check Payment History</p>
            <p>• Make Payments</p>
            <p>• Download Receipts</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
        
        with tab1:
            st.subheader("Parent Login")
            
            with st.form("parent_login_form"):
                email = st.text_input("📧 Email Address", placeholder="your.email@example.com")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
                
                login_btn = st.form_submit_button("🚀 Login to Portal", use_container_width=True)
                
                if login_btn:
                    if email and password:
                        if authenticate_parent(email, password):
                            st.session_state.parent_authenticated = True
                            st.session_state.parent_email = email
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid email or password")
                    else:
                        st.error("⚠️ Please enter email and password")
        
        with tab2:
            st.subheader("Create Parent Account")
            
            with st.form("parent_signup_form"):
                signup_email = st.text_input("📧 Email Address*", placeholder="your.email@example.com")
                parent_name = st.text_input("👤 Parent Name*", placeholder="Your full name")
                signup_password = st.text_input("🔒 Password*", type="password", placeholder="Minimum 6 characters")
                confirm_password = st.text_input("🔒 Confirm Password*", type="password", placeholder="Re-enter password")
                phone = st.text_input("📱 Phone Number*", placeholder="03001234567")
                student_ids = st.text_area(
                    "🎓 Student IDs*", 
                    placeholder="Enter one student ID per line\nExample:\nSTU001\nSTU002",
                    help="Contact school administration to get your student's ID"
                )
                
                signup_btn = st.form_submit_button("🎉 Create Account", use_container_width=True)
                
                if signup_btn:
                    if signup_email and parent_name and signup_password and phone and student_ids:
                        if signup_password != confirm_password:
                            st.error("❌ Passwords do not match")
                        elif len(signup_password) < 6:
                            st.error("❌ Password must be at least 6 characters")
                        else:
                            # Process student IDs
                            student_id_list = [s.strip() for s in student_ids.split('\n') if s.strip()]
                            
                            if not student_id_list:
                                st.error("❌ Please enter at least one student ID")
                            else:
                                success, message = create_parent_account(
                                    signup_email,
                                    signup_password,
                                    parent_name,
                                    student_id_list,
                                    phone
                                )
                                if success:
                                    st.success("✅ Account created successfully! Please login.")
                                    st.balloons()
                                else:
                                    st.error(f"❌ {message}")
                    else:
                        st.error("⚠️ Please fill all required fields (*)")

def show_parent_dashboard():
    """Show parent dashboard after login"""
    
    # School header
    school_config = load_school_config()
    school_name = school_config.get("school_name", "School Name")
    
    # Sidebar with collapsible design
    with st.sidebar:
        # Parent info section
        parent_info = get_parent_info(st.session_state.parent_email)
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; margin-bottom: 20px;">
            <h3 style="margin: 0; font-size: 1.2rem;">👋 Welcome!</h3>
            <p style="margin: 5px 0; font-size: 1rem;"><strong>{parent_info.get('parent_name', 'Parent')}</strong></p>
            <p style="margin: 5px 0; font-size: 0.8rem;">{st.session_state.parent_email}</p>
            <p style="margin: 5px 0; font-size: 0.8rem;">📱 {parent_info.get('phone', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Student selection
        students = get_parent_students(st.session_state.parent_email)
        
        if not students:
            st.warning("⚠️ No students linked to your account")
            selected_student = None
        else:
            selected_student = st.selectbox(
                "🎒 Select Student:",
                students,
                key="student_selector"
            )
            st.session_state.selected_student = selected_student
        
        st.divider()
        
        # Navigation with better styling
        st.markdown("### 🧭 Navigation")
        
        # Initialize session state for current page
        if 'current_parent_page' not in st.session_state:
            st.session_state.current_parent_page = "📊 Dashboard"
        
        # Page selection buttons
        pages = {
            "📊 Dashboard": "📊",
            "💰 Fee Details": "💰", 
            "📋 Payment History": "📋",
            "💳 Make Payment": "💳"
        }
        
        for page_name, icon in pages.items():
            if st.button(
                f"{icon} {page_name}", 
                key=f"nav_{page_name}",
                use_container_width=True,
                type="primary" if st.session_state.current_parent_page == page_name else "secondary"
            ):
                st.session_state.current_parent_page = page_name
                st.rerun()
        
        st.divider()
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            logout_parent()
            st.rerun()
    
    # Main content area
    st.markdown(f"""
    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h1 style="margin: 0; color: #2c3e50;">{school_name} - Parent Portal</h1>
        <p style="margin: 0; color: #7f8c8d;">{st.session_state.current_parent_page}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not students:
        st.info("📝 No students are linked to your account. Please contact school administration to link your students.")
        return
    
    if not selected_student:
        st.info("👆 Please select a student from the sidebar")
        return
    
    # Show selected page based on session state
    if st.session_state.current_parent_page == "📊 Dashboard":
        show_dashboard_page(selected_student)
    elif st.session_state.current_parent_page == "💰 Fee Details":
        show_fee_details_page(selected_student)
    elif st.session_state.current_parent_page == "📋 Payment History":
        show_payment_history_page(selected_student)
    elif st.session_state.current_parent_page == "💳 Make Payment":
        show_make_payment_page(selected_student)

def show_dashboard_page(student_id):
    """Show dashboard with overview"""
    
    fee_details = get_student_fee_details(student_id)
    
    if not fee_details:
        st.error("❌ Student information not found")
        return
    
    # Quick stats in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🎒 Student", 
            value=fee_details['student_name'],
            help="Student Name"
        )
    with col2:
        st.metric(
            label="🏫 Class", 
            value=fee_details['class'],
            help="Current Class"
        )
    with col3:
        st.metric(
            label="👨 Father", 
            value=fee_details['father_name'],
            help="Father's Name"
        )
    with col4:
        st.metric(
            label="📱 Phone", 
            value=fee_details['phone'],
            help="Contact Number"
        )
    
    st.divider()
    
    # Fee summary cards
    st.subheader("💰 Fee Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Fees", 
            value=format_currency(fee_details['total_due']),
            delta=None
        )
    with col2:
        st.metric(
            label="Amount Paid", 
            value=format_currency(fee_details['total_received']),
            delta=f"{fee_details['percentage_paid']}%"
        )
    with col3:
        st.metric(
            label="Balance Due", 
            value=format_currency(fee_details['balance_due']),
            delta_color="inverse"
        )
    with col4:
        # Status badge
        if fee_details['balance_due'] == 0:
            st.success("✅ All Paid")
        elif fee_details['balance_due'] < fee_details['total_due'] * 0.5:
            st.warning("🟡 Partial Paid")
        else:
            st.error("🔴 Payment Due")
    
    # Progress bar with better styling
    st.markdown(f"**Payment Progress: {fee_details['percentage_paid']}%**")
    st.progress(fee_details['percentage_paid'] / 100)
    
    # Monthly fee status
    st.divider()
    st.subheader("📅 Monthly Fee Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✅ Paid Months")
        if fee_details['paid_months']:
            for paid in fee_details['paid_months']:
                st.success(f"**{paid['month']}** - {format_currency(paid['amount'])}")
        else:
            st.info("No months paid yet")
    
    with col2:
        st.markdown("### ❌ Unpaid Months")
        if fee_details['unpaid_months']:
            for month in fee_details['unpaid_months']:
                st.error(f"**{month}** - {format_currency(fee_details['monthly_fee'])}")
        else:
            st.success("All months paid! 🎉")
    
    # Quick actions
    st.divider()
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 View Detailed History", use_container_width=True, icon="📋"):
            st.session_state.current_parent_page = "📋 Payment History"
            st.rerun()
    
    with col2:
        if st.button("💳 Make Payment", use_container_width=True, icon="💳"):
            st.session_state.current_parent_page = "💳 Make Payment"
            st.rerun()
    
    with col3:
        if st.button("📊 Fee Breakdown", use_container_width=True, icon="📊"):
            st.session_state.current_parent_page = "💰 Fee Details"
            st.rerun()
    
    # Recent activity preview
    st.divider()
    st.subheader("📈 Recent Activity")
    
    df = load_data()
    student_records = df[df['ID'] == student_id].sort_values('Date', ascending=False).head(5)
    
    if not student_records.empty:
        recent_df = student_records[['Date', 'Month', 'Received Amount', 'Payment Method']].copy()
        recent_df['Date'] = pd.to_datetime(recent_df['Date'], errors='coerce').dt.strftime('%d-%m-%Y')
        
        st.dataframe(
            recent_df.style.format({
                'Received Amount': format_currency
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No recent transactions found")

def show_fee_details_page(student_id):
    """Show detailed fee breakdown with all months"""
    
    # Add back button at the top
    add_back_button()
    
    fee_details = get_student_fee_details(student_id)
    
    if not fee_details:
        st.error("❌ Student information not found")
        return
    
    st.subheader(f"💰 Detailed Fee Breakdown - {fee_details['student_name']}")
    
    # Monthly fee card
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Monthly Fee", format_currency(fee_details['monthly_fee']))
    with col2:
        st.metric("Paid Months", fee_details['total_paid_months'])
    with col3:
        st.metric("Unpaid Months", fee_details['total_unpaid_months'])
    with col4:
        st.metric("Total Months", 12)
    
    # All months display in a grid
    st.subheader("📅 Complete Monthly Status")
    
    # Create columns for months (3 months per row)
    months = [
        "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER",
        "OCTOBER", "NOVEMBER", "DECEMBER", "JANUARY", "FEBRUARY", "MARCH"
    ]
    
    # Create 4 columns for better layout
    cols = st.columns(4)
    
    for i, month in enumerate(months):
        col_idx = i % 4
        with cols[col_idx]:
            # Check if month is paid
            is_paid = any(p['month'] == month for p in fee_details['paid_months'])
            
            if is_paid:
                # Find paid month details
                paid_month = next((p for p in fee_details['paid_months'] if p['month'] == month), None)
                st.success(f"""
                **{month}**
                ✅ PAID
                Amount: {format_currency(paid_month['amount'])}
                """)
            else:
                st.error(f"""
                **{month}**
                ❌ UNPAID
                Due: {format_currency(fee_details['monthly_fee'])}
                """)
    
    # Fee summary
    st.divider()
    st.subheader("📊 Fee Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Fee Breakdown")
        fee_data = {
            "Fee Type": ["Monthly Fees", "Annual Charges", "Admission Fee", "Total"],
            "Amount": [
                format_currency(fee_details['total_monthly']),
                format_currency(fee_details['total_annual']),
                format_currency(fee_details['total_admission']),
                format_currency(fee_details['total_due'])
            ]
        }
        fee_df = pd.DataFrame(fee_data)
        st.dataframe(fee_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("#### Payment Summary")
        payment_data = {
            "Description": ["Total Amount Due", "Amount Paid", "Balance Due"],
            "Amount": [
                format_currency(fee_details['total_due']),
                format_currency(fee_details['total_received']),
                format_currency(fee_details['balance_due'])
            ]
        }
        payment_df = pd.DataFrame(payment_data)
        st.dataframe(payment_df, use_container_width=True, hide_index=True)
    
    # Visual indicators
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        # Payment status
        if fee_details['balance_due'] == 0:
            st.success("""
            ### ✅ Payment Status: All Clear!
            All fees are paid up to date. Thank you!
            """)
        elif fee_details['balance_due'] < fee_details['total_due'] * 0.5:
            st.warning(f"""
            ### 🟡 Payment Status: Partial Payment
            Balance amount pending: **{format_currency(fee_details['balance_due'])}**
            """)
        else:
            st.error(f"""
            ### 🔴 Payment Status: Payment Due
            Significant balance pending: **{format_currency(fee_details['balance_due'])}**
            Please make payment at your earliest.
            """)
    
    with col2:
        # Next steps
        st.info("""
        ### 📝 Next Steps:
        1. Check payment details above
        2. View payment history if needed
        3. Make payment through available methods
        4. Contact school for any queries
        """)

def show_payment_history_page(student_id):
    """Show payment history"""
    
    # Add back button at the top
    add_back_button()
    
    df = load_data()
    student_records = df[df['ID'] == student_id]
    
    if student_records.empty:
        st.info("ℹ️ No payment history found")
        return
    
    # Summary stats
    total_payments = len(student_records)
    total_received = student_records['Received Amount'].sum()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Transactions", total_payments)
    with col2:
        st.metric("Total Amount Paid", format_currency(total_received))
    
    st.divider()
    
    # Display payment history
    st.subheader("📋 Payment History")
    
    display_columns = ['Date', 'Month', 'Monthly Fee', 'Annual Charges', 'Admission Fee', 'Received Amount', 'Payment Method']
    available_columns = [col for col in display_columns if col in student_records.columns]
    display_df = student_records[available_columns].copy()
    
    # Format dates and amounts
    if 'Date' in display_df.columns:
        display_df['Date'] = pd.to_datetime(display_df['Date'], errors='coerce').dt.strftime('%d-%m-%Y')
    display_df = display_df.sort_values('Date' if 'Date' in display_df.columns else available_columns[0], ascending=False)
    
    st.dataframe(
        display_df.style.format({
            'Monthly Fee': format_currency,
            'Annual Charges': format_currency,
            'Admission Fee': format_currency,
            'Received Amount': format_currency
        }),
        use_container_width=True,
        height=400
    )
    
    # Download option
    st.divider()
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Payment History (CSV)",
        data=csv,
        file_name=f"payment_history_{student_id}.csv",
        mime="text/csv",
        use_container_width=True
    )

def show_make_payment_page(student_id):
    """Show payment options with real payment integration"""
    
    add_back_button()
    
    fee_details = get_student_fee_details(student_id)
    
    if not fee_details:
        st.error("❌ Student information not found")
        return
    
    if fee_details['balance_due'] == 0:
        st.success("""
        # 🎉 All Fees Paid!
        
        ### Your account is up to date. No payment required at this time.
        
        Thank you for your timely payments!
        """)
        return
    
    # Payment header with balance
    st.warning(f"""
    # 💰 Payment Required
    
    ### Current Balance Due: **{format_currency(fee_details['balance_due'])}**
    
    Please choose a payment method below:
    """)
    
    # Show unpaid months summary
    if fee_details['unpaid_months']:
        st.info(f"**Unpaid Months ({len(fee_details['unpaid_months'])}):** {', '.join(fee_details['unpaid_months'])}")
    
    # Payment methods in tabs
    st.subheader("🏦 Available Payment Methods")
    
    tab1, tab2, tab3 = st.tabs(["🏦 Bank Transfer", "📱 JazzCash", "📲 EasyPaisa"])
    
    with tab1:
        show_bank_transfer_payment(student_id, fee_details)
    
    with tab2:
        show_jazzcash_payment(student_id, fee_details)
    
    with tab3:
        show_easypaisa_payment(student_id, fee_details)

def parent_portal_page():
    """Main parent portal page"""
    # Remove Streamlit warnings and headers
    st.markdown("""
    <style>
    /* Hide Streamlit header and warnings */
    header {
        display: none !important;
    }
    .stAlert, .stWarning, .stException {
        display: none !important;
    }
    div[data-testid="stToolbar"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Set parent portal flag
    st.session_state.is_parent_portal = True
    
    # Check if parent is authenticated
    if not check_parent_authentication():
        show_parent_login()
    else:
        show_parent_dashboard()

if __name__ == "__main__":
    parent_portal_page()
# [file content end]