import streamlit as st
import pandas as pd
from datetime import datetime
import csv
import os

from backend.utils import get_feature_engineered_path, get_model_path, load_model
from backend.hybrid_decision import make_decision
from backend.rule_engine import calculate_all_limits
from backend.autoencoder import AutoencoderInference
from backend.db_service import get_db_service

db = get_db_service()

def save_transaction_to_csv(cid, amount, t_type, status="Approved"):
    file_name = 'data/transaction_history.csv'
    file_exists = os.path.isfile(file_name)
    
    with open(file_name, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Txn_id', 'CustomerID', 'Amount', 'Type', 'Status', 'Timestamp'])
        writer.writerow([len(pd.read_csv(file_name)) if file_exists else 1, cid, amount, t_type, status, datetime.now()])

st.set_page_config(page_title="Banking Fraud Detection", layout="wide")

def init_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'customer_id' not in st.session_state:
        st.session_state.customer_id = None
    if 'result' not in st.session_state:
        st.session_state.result = None
    if 'txn_history' not in st.session_state:
        st.session_state.txn_history = {}  
    if 'session_count' not in st.session_state:
        st.session_state.session_count = {}  
    if 'monthly_spending' not in st.session_state:
        st.session_state.monthly_spending = {}  

def get_velocity(cid, account_no):
    try:
        return db.get_velocity_metrics(cid, account_no)
    except:
        return {
            'txn_count_10min': 0,
            'txn_count_1hour': 0,
            'time_since_last_txn': 3600
        }

def record_transaction(cid, account_no):
    account_key = f"{cid}_{account_no}"
    if account_key not in st.session_state.txn_history:
        st.session_state.txn_history[account_key] = []
    st.session_state.txn_history[account_key].append(datetime.now())
    
    if account_key not in st.session_state.session_count:
        st.session_state.session_count[account_key] = 0
    st.session_state.session_count[account_key] += 1

def add_monthly_spending(cid, account_no, amount):
    account_key = f"{cid}_{account_no}"
    if account_key not in st.session_state.monthly_spending:
        st.session_state.monthly_spending[account_key] = 0.0
    st.session_state.monthly_spending[account_key] += amount

@st.cache_data
def load_data():
    try:
        customers = db.get_all_customers()
        if customers:
            return pd.DataFrame({'CustomerId': customers})
        return None
    except Exception as e:
        st.error(f"Database error: {e}")
        return None

@st.cache_resource
def get_model():
    if os.path.exists(get_model_path()):
        return load_model()
    else:
        st.error(f"Model not found: {get_model_path()}")
        st.info("Run `python -m backend.model_training` first.")
        return None, None

@st.cache_resource
def get_autoencoder():
    ae = AutoencoderInference()
    if ae.load():
        return ae
    else:
        return None

def get_monthly_spending_from_csv(cust_data, account_no, amt_col):
    try:
        return db.get_monthly_spending(st.session_state.customer_id, account_no)
    except:
        return 0.0

def login_page(df):
    st.title("Banking Fraud Detection System")
    st.subheader("Login")
    
    try:
        customers = db.get_all_customers()
        customers = sorted([str(c) for c in customers])
    except:
        st.error("Cannot fetch customers from database")
        return
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Select Customer ID")
        cid = st.selectbox("Customer ID", customers)
        pwd = st.text_input("Password", type="password")
        
        if st.button("Login", type="primary", use_container_width=True):
            if pwd == "12345":
                st.session_state.logged_in = True
                st.session_state.customer_id = cid
                st.rerun()
            else:
                st.error("Invalid password")
        
        st.info("Password: 12345")


def dashboard(df, model, features, scaler=None, autoencoder=None):
    cid = str(st.session_state.customer_id)
    
    try:
        accounts_raw = db.get_customer_accounts(cid)
        # Create mapping: display_value -> original_value
        account_mapping = {}
        accounts_display = []
        for acc in accounts_raw:
            original = str(acc)
            display = str(int(acc)) if str(acc).isdigit() else str(acc)
            account_mapping[display] = original
            accounts_display.append(display)
        accounts = accounts_display
    except:
        st.error("Cannot fetch accounts from database")
        return

    st.title("Fraud Detection Dashboard")
    
    st.subheader("Step 1: Select Account")
    
    if len(accounts) == 0:
        st.error("No accounts found for this customer")
        return
        
    account_display = st.selectbox("Select Account", accounts, label_visibility="collapsed")
    # Get original account number for queries
    account = account_mapping.get(account_display, account_display)
    
    try:
        account_data = db.get_account_transactions(cid, account)
    except:
        st.error("Cannot fetch account transactions")
        return
    
    csv_count = len(account_data)
    account_key = f"{cid}_{account}"
    session_count = st.session_state.session_count.get(account_key, 0)
    total_txns = csv_count + session_count

    vel = get_velocity(cid, account)

    st.sidebar.title("Navigation")
    st.sidebar.markdown(f"**Customer ID:** {cid}")
    st.sidebar.markdown(f"**Account:** {account_display}")  # Display without leading zeros
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.customer_id = None
        st.session_state.result = None
        st.rerun()
    
    st.sidebar.markdown("---")
    
    if autoencoder is not None:
        st.sidebar.success("Autoencoder: Active")
    else:
        st.sidebar.warning("Autoencoder: Unavailable")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Account Statistics")
    
    if len(account_data) > 0:
        amt_col = 'AmountInAed'
        avg = account_data[amt_col].mean()
        max_amt = account_data[amt_col].max()
        std = account_data[amt_col].std() if len(account_data) > 1 else 0
        
        st.sidebar.markdown(f"**Average Transaction:** AED {avg:,.2f}")
        st.sidebar.markdown(f"**Max Transaction:** AED {max_amt:,.2f}")
        st.sidebar.metric("Total Transactions", total_txns, 
                         delta=f"+{session_count} this session" if session_count > 0 else None)
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("Current Velocity")
        st.sidebar.markdown(f"**Last 10 min:** {vel['txn_count_10min']} transactions")
        st.sidebar.markdown(f"**Last 1 hour:** {vel['txn_count_1hour']} transactions")
        
        try:
            monthly_spending = db.get_monthly_spending(cid, account)
        except:
            monthly_spending = 0.0
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("Monthly Spending")
        st.sidebar.markdown(f"**This Month:** AED {monthly_spending:,.2f}")
        st.sidebar.markdown("---")
        st.sidebar.subheader("Transfer Type Limits")
        limits = calculate_all_limits(avg, std)
        st.sidebar.markdown(f"**O - Own Account:** AED {limits['O']:,.2f}")
        st.sidebar.markdown(f"**I - Ajman:** AED {limits['I']:,.2f}")
        st.sidebar.markdown(f"**L - UAE:** AED {limits['L']:,.2f}")
        st.sidebar.markdown(f"**Q - Quick:** AED {limits['Q']:,.2f}")
        st.sidebar.markdown(f"**S - Overseas:** AED {limits['S']:,.2f}")
        st.sidebar.markdown(f"**M - MobilePay:** AED {limits['M']:,.2f}")
        st.sidebar.markdown(f"**F - Family Transfer:** AED {limits['F']:,.2f}")
    else:
        avg, std, max_amt = 5000, 2000, 15000
        st.sidebar.warning("No transaction history for this account")

    st.markdown("---")

    st.subheader("Step 2: Transaction Details")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("**Transaction Amount (AED)**")
        amount = st.number_input("", min_value=0.0, max_value=1000000.0, value=1000.0, step=100.0, key="amt_input")
    
    with c2:
        st.markdown("**Recipient Account Number**")
        recipient_account = st.text_input("", placeholder="Enter recipient account number", key="recipient_input")
    
    c3, c4, c5 = st.columns(3)
    
    with c3:
        st.markdown("**Transfer Type**")
        types = {
            'O': 'O - Own Account', 
            'I': 'I - Within Ajman', 
            'L': 'L - Within UAE', 
            'Q': 'Q - Quick Remittance', 
            'S': 'S - Overseas',
            'M': 'M - MobilePay',
            'F': 'F - Family Transfer'
        }
        t_type = st.selectbox("", list(types.keys()), format_func=lambda x: types[x], key="type_input")
    
    with c4:
        st.markdown("**Bank Country**")
        countries = ['UAE', 'USA', 'UK', 'India', 'Pakistan', 'Philippines', 'Egypt', 'Other']
        country = st.selectbox("", countries, key="country_input")
    
    with c5:
        st.markdown("**Recipient Name (Optional)**")
        recipient_name = st.text_input("", placeholder="Recipient name", key="recipient_name_input")
    
    st.markdown("---")
    
    st.subheader("Step 3: Process Transaction")
 
    current_vel = get_velocity(cid, account)
    
    if st.button("Process Transaction", type="primary", use_container_width=True):
        # Validate recipient account
        if not recipient_account or recipient_account.strip() == "":
            st.error("Please enter recipient account number")
            st.stop()
        
        current_vel = get_velocity(cid, account)
        
        txn_count_10min = current_vel['txn_count_10min'] + 1
        txn_count_1hour = current_vel['txn_count_1hour'] + 1
        
        try:
            monthly_spending = db.get_monthly_spending(cid, account)
        except:
            monthly_spending = 0.0
        
        overall_avg = account_data['AmountInAed'].mean() if len(account_data) > 0 else 5000
        overall_std = account_data['AmountInAed'].std() if len(account_data) > 1 else 2000
        overall_max = account_data['AmountInAed'].max() if len(account_data) > 0 else 15000

        total_txns_count = len(account_data)
        intl_ratio = 0.0
        if total_txns_count > 0:
            count_s = len(account_data[account_data['TransferType'] == 'S'])
            intl_ratio = count_s / total_txns_count

        user_stats = {
            'user_avg_amount': overall_avg,
            'user_std_amount': overall_std,
            'user_max_amount': overall_max,
            'user_txn_frequency': total_txns_count,
            'user_international_ratio': intl_ratio,
            'current_month_spending': monthly_spending
        }

        # Check if beneficiary is new
        try:
            is_new_ben = db.check_new_beneficiary(cid, recipient_account.strip())
        except Exception as e:
            st.warning(f"Could not verify beneficiary status: {e}")
            is_new_ben = 0  # Assume existing beneficiary if check fails

        txn = {
            'amount': amount, 
            'transfer_type': t_type, 
            'bank_country': country,
            'account': account,
            'txn_count_10min': txn_count_10min,
            'txn_count_1hour': txn_count_1hour,
            'time_since_last_txn': current_vel['time_since_last_txn'],
            'is_new_beneficiary': is_new_ben
        }

        st.session_state.result = make_decision(txn, user_stats, model, features, autoencoder=autoencoder)
        st.session_state.result['amount'] = amount
        st.session_state.result['t_type'] = t_type
        st.session_state.result['account'] = account
        st.session_state.result['recipient_account'] = recipient_account.strip()
        st.session_state.result['txn_count_10min'] = txn_count_10min
        st.session_state.result['txn_count_1hour'] = txn_count_1hour
        st.rerun()

    st.markdown("---")
    
    st.subheader("Step 4: Transaction Result")

    if st.session_state.result:
        r = st.session_state.result
        t_type = r.get('t_type', 'O')
        result_account = r.get('account', account)

        st.info(f"Velocity: {r.get('txn_count_10min', 0)} txns in 10min | {r.get('txn_count_1hour', 0)} txns in 1hour")
        
        if r.get('ae_reconstruction_error') is not None:
            ae_status = "Anomaly" if r.get('ae_flag', False) else "Normal"
            st.info(f"AE Error: {r['ae_reconstruction_error']:.4f} | Threshold: {r.get('ae_threshold', 'N/A'):.4f} | Status: {ae_status}")
        
        if r['is_fraud']:
            st.error("FRAUD ALERT - Transaction Flagged!")

            for reason in r['reasons']:
                if isinstance(reason, str):
                    st.warning(reason)
                elif isinstance(reason, list):
                    for r_item in reason:
                        st.warning(r_item)
            
            st.markdown(f"**Risk Score:** {r['risk_score']:.4f}")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Approve (Force)", type="primary"):
                    record_transaction(cid, result_account)
                    add_monthly_spending(cid, result_account, r['amount'])
                    save_transaction_to_csv(cid, r['amount'], t_type, "Force Approved")
                    st.success("Approved & Saved!")
                    st.session_state.result = None
                    st.rerun()
                    
            with c2:
                if st.button("Reject"):
                    save_transaction_to_csv(cid, r['amount'], t_type, "Rejected")
                    st.error("Rejected!")
                    st.session_state.result = None
                    st.rerun()

        else:
            st.success("SAFE TRANSACTION")
            st.info(f"Amount: AED {r['amount']:,.2f} | Threshold: AED {r['threshold']:,.2f}")

            if st.button("Confirm & Continue", type="primary"):
                record_transaction(cid, result_account)
                add_monthly_spending(cid, result_account, r['amount'])
                st.session_state.result = None
                st.rerun()

def main():
    init_state()
    
    df = load_data()
    if df is None:
        return
    
    model, features, scaler = get_model()
    if model is None:
        return
    autoencoder = get_autoencoder()
    
    if st.session_state.logged_in:
        dashboard(df, model, features, scaler=scaler, autoencoder=autoencoder)
    else:
        login_page(df)

if __name__ == "__main__":
    main()
