# # [file name]: real_payment_system.py
# # [file content begin]
# # type:ignore
# import streamlit as st
# import json
# import os
# from datetime import datetime

# class RealPaymentSystem:
#     def __init__(self):
#         self.payments_file = "parent_payments.json"
#         self._initialize_payments_file()
    
#     def _initialize_payments_file(self):
#         """Initialize payments file if it doesn't exist"""
#         if not os.path.exists(self.payments_file):
#             with open(self.payments_file, 'w') as f:
#                 json.dump({}, f)
    
#     def _save_payment_record(self, payment_data):
#         """Save payment record to JSON file"""
#         try:
#             with open(self.payments_file, 'r') as f:
#                 payments = json.load(f)
            
#             student_id = payment_data['student_id']
#             if student_id not in payments:
#                 payments[student_id] = []
            
#             payments[student_id].append(payment_data)
            
#             with open(self.payments_file, 'w') as f:
#                 json.dump(payments, f, indent=4)
            
#             return True
#         except Exception as e:
#             st.error(f"Error saving payment: {str(e)}")
#             return False
    
#     def handle_parent_payment(self, student_id, student_name, amount, payment_method, transaction_id):
#         """Handle payment from parent and record in admin system"""
#         try:
#             from database import load_data, save_to_csv, load_student_details
#             import pandas as pd
#             from datetime import datetime
            
#             # Load student details
#             student_details = load_student_details()
#             student_info = student_details.get(student_id, {})
            
#             # Create payment record
#             payment_record = {
#                 "ID": student_id,
#                 "Student Name": student_name,
#                 "Father Name": student_info.get('father_name', ''),
#                 "Student Phone": student_info.get('phone', ''),
#                 "Class Category": student_info.get('class_category', ''),
#                 "Class Section": student_info.get('class_section', ''),
#                 "Address": student_info.get('address', ''),
#                 "Age": student_info.get('age', ''),
#                 "Month": "PARENT_PAYMENT",
#                 "Monthly Fee": amount,
#                 "Annual Charges": 0,
#                 "Admission Fee": 0,
#                 "Received Amount": amount,
#                 "Payment Method": payment_method,
#                 "Date": datetime.now().strftime("%Y-%m-%d"),
#                 "Signature": "Parent Portal",
#                 "Entry Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#                 "Academic Year": "2024-2025",
#                 "Transaction ID": transaction_id,
#                 "Payment Source": "Parent Portal"
#             }
            
#             # Save to main database
#             if save_to_csv([payment_record]):
#                 return True
#             return False
            
#         except Exception as e:
#             st.error(f"Payment recording error: {str(e)}")
#             return False
    
#     def process_parent_payment(self, student_id, student_name, amount, payment_method, transaction_data):
#         """Process payment from parent portal"""
#         try:
#             # Validate transaction
#             if payment_method == "JazzCash":
#                 from jazz_cash import JazzCashPayment
#                 payment = JazzCashPayment()
#                 verification = payment.verify_payment(transaction_data)
#             elif payment_method == "EasyPaisa":
#                 from easy_paisa import EasyPaisaPayment
#                 payment = EasyPaisaPayment()
#                 verification = payment.verify_payment(transaction_data)
#             else:
#                 verification = {'success': True, 'verified': True}
            
#             if verification.get('success') and verification.get('verified'):
#                 # Record payment in admin system
#                 if self.handle_parent_payment(student_id, student_name, amount, payment_method, 
#                                            transaction_data.get('transaction_id', '')):
#                     return True, "Payment successful and recorded!"
#                 else:
#                     return False, "Payment verification failed"
#             else:
#                 return False, verification.get('error', 'Payment verification failed')
                
#         except Exception as e:
#             return False, f"Payment processing error: {str(e)}"
    
#     def get_parent_payments(self, student_id=None):
#         """Get parent payments (for admin view)"""
#         try:
#             with open(self.payments_file, 'r') as f:
#                 payments = json.load(f)
            
#             if student_id:
#                 return payments.get(student_id, [])
#             return payments
#         except:
#             return {}
    
#     def show_payment_interface(self):
#         """Show payment interface for parents"""
#         st.header("💳 Real Payment System")
        
#         # Check if user is parent or admin
#         if hasattr(st.session_state, 'parent_authenticated') and st.session_state.parent_authenticated:
#             self._show_parent_payment_interface()
#         else:
#             self._show_admin_payment_interface()
    
#     def _show_parent_payment_interface(self):
#         """Show payment interface for parents"""
#         st.subheader("Make Payment")
        
#         # Get student information
#         student_id = st.session_state.get('selected_student')
#         if not student_id:
#             st.warning("Please select a student first")
#             return
        
#         from parent_database import get_student_fee_summary
#         fee_summary = get_student_fee_summary(student_id)
        
#         if not fee_summary:
#             st.error("Student information not found")
#             return
        
#         st.write(f"**Student:** {fee_summary['student_name']}")
#         st.write(f"**Class:** {fee_summary['class']}")
#         st.write(f"**Amount Due:** Rs. {fee_summary['balance_due']:,}")
        
#         payment_amount = st.number_input("Payment Amount", 
#                                        min_value=0.0, 
#                                        value=float(fee_summary['balance_due']),
#                                        step=500.0)
        
#         payment_method = st.selectbox("Payment Method", 
#                                     ["JazzCash", "EasyPaisa", "Bank Transfer"])
        
#         if st.button("Proceed to Payment"):
#             if payment_amount <= 0:
#                 st.error("Please enter a valid payment amount")
#             else:
#                 st.session_state.payment_amount = payment_amount
#                 st.session_state.payment_method = payment_method
#                 st.session_state.student_id = student_id
#                 st.session_state.student_name = fee_summary['student_name']
                
#                 if payment_method == "JazzCash":
#                     st.switch_page("pages/jazz_cash.py")
#                 elif payment_method == "EasyPaisa":
#                     st.switch_page("pages/easy_paisa.py")
#                 else:
#                     self._show_bank_transfer_instructions()
    
#     def _show_admin_payment_interface(self):
#         """Show payment interface for admin"""
#         st.subheader("Parent Payments Overview")
        
#         payments = self.get_parent_payments()
        
#         if not payments:
#             st.info("No parent payments received yet")
#             return
        
#         total_parent_payments = 0
#         total_transactions = 0
        
#         for student_id, student_payments in payments.items():
#             st.subheader(f"Student: {student_id}")
#             for payment in student_payments:
#                 total_parent_payments += payment.get('amount', 0)
#                 total_transactions += 1
                
#                 col1, col2, col3 = st.columns(3)
#                 with col1:
#                     st.write(f"**Amount:** Rs. {payment.get('amount', 0):,}")
#                 with col2:
#                     st.write(f"**Method:** {payment.get('payment_method', 'N/A')}")
#                 with col3:
#                     st.write(f"**Date:** {payment.get('timestamp', 'N/A')}")
#                 st.write(f"**Transaction ID:** {payment.get('transaction_id', 'N/A')}")
#                 st.divider()
        
#         st.metric("Total Parent Payments", f"Rs. {total_parent_payments:,}")
#         st.metric("Total Transactions", total_transactions)
    
#     def _show_bank_transfer_instructions(self):
#         """Show bank transfer instructions"""
#         from payment_config import PaymentConfig
#         config = PaymentConfig()
#         bank_config = config.load_config().get('bank_details', {})
        
#         st.info("""
#         **Bank Transfer Instructions:**
#         1. Transfer to the school bank account
#         2. Use Student ID as reference
#         3. Keep transaction receipt
#         4. Payment will be verified within 24 hours
#         """)
        
#         st.write(f"**Bank:** {bank_config.get('bank_name', 'Contact School')}")
#         st.write(f"**Account:** {bank_config.get('account_number', 'Contact School')}")
#         st.write(f"**Title:** {bank_config.get('account_title', 'Contact School')}")

# def real_payment_page():
#     """Real payment system page"""
#     payment_system = RealPaymentSystem()
#     payment_system.show_payment_interface()

# if __name__ == "__main__":
#     real_payment_page()
# # [file content end]

# [file name]: real_payment_system.py
# [file content begin]
# type:ignore
import streamlit as st
import json
import os
from datetime import datetime

class RealPaymentSystem:
    def __init__(self):
        self.payments_file = "parent_payments.json"
        self._initialize_payments_file()
    
    def _initialize_payments_file(self):
        """Initialize payments file if it doesn't exist"""
        if not os.path.exists(self.payments_file):
            with open(self.payments_file, 'w') as f:
                json.dump({}, f)
    
    def handle_parent_payment(self, student_id, student_name, amount, payment_method, transaction_id):
        """Handle payment from parent and record in admin system"""
        try:
            from database import save_to_csv, load_student_details
            
            # Load student details
            student_details = load_student_details()
            student_info = student_details.get(student_id, {})
            
            # Create payment record
            payment_record = {
                "ID": student_id,
                "Student Name": student_name,
                "Father Name": student_info.get('father_name', ''),
                "Student Phone": student_info.get('phone', ''),
                "Class Category": student_info.get('class_category', ''),
                "Class Section": student_info.get('class_section', ''),
                "Address": student_info.get('address', ''),
                "Age": student_info.get('age', ''),
                "Month": "PARENT_PAYMENT",
                "Monthly Fee": amount,
                "Annual Charges": 0,
                "Admission Fee": 0,
                "Received Amount": amount,
                "Payment Method": payment_method,
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Signature": "Parent Portal",
                "Entry Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Academic Year": "2024-2025",
                "Transaction ID": transaction_id,
                "Payment Source": "Parent Portal"
            }
            
            # Save to main database
            if save_to_csv([payment_record]):
                # Also save to parent payments file for tracking
                self._save_parent_payment_record(student_id, student_name, amount, payment_method, transaction_id)
                return True
            return False
            
        except Exception as e:
            st.error(f"Payment recording error: {str(e)}")
            return False

    def _save_parent_payment_record(self, student_id, student_name, amount, payment_method, transaction_id):
        """Save parent payment record to separate file"""
        try:
            parent_payments_file = "parent_payments_history.json"
            
            if os.path.exists(parent_payments_file):
                with open(parent_payments_file, 'r') as f:
                    payments = json.load(f)
            else:
                payments = {}
            
            if student_id not in payments:
                payments[student_id] = []
            
            payment_data = {
                "student_id": student_id,
                "student_name": student_name,
                "amount": amount,
                "payment_method": payment_method,
                "transaction_id": transaction_id,
                "payment_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "pending_verification"
            }
            
            payments[student_id].append(payment_data)
            
            with open(parent_payments_file, 'w') as f:
                json.dump(payments, f, indent=4)
            
            return True
        except Exception as e:
            print(f"Error saving parent payment: {str(e)}")
            return False

def real_payment_page():
    """Real payment system page"""
    payment_system = RealPaymentSystem()
    
    st.header("💳 Real Payment System")
    st.info("This is the payment system for processing parent payments.")

if __name__ == "__main__":
    real_payment_page()
# [file content end]