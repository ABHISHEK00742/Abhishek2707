import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd

# Suppress Flask development server warning
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

APP_SECRET = os.environ.get("APP_SECRET", "dev-secret-change-me")
DATA_DIR = os.path.join(os.getcwd(), "data")
USERS_CSV = os.path.join(DATA_DIR, "users.csv")
TXNS_CSV = os.path.join(DATA_DIR, "transactions.csv")
LOANS_CSV = os.path.join(DATA_DIR, "loans.csv")

os.makedirs(DATA_DIR, exist_ok=True)

# Ensure CSV files exist with proper headers
if not os.path.exists(USERS_CSV):
    pd.DataFrame(columns=[
        "user_id",
        "name",
        "age",
        "address",
        "aadhaar",
        "father_name",
        "mother_name",
        "password"
    ]).to_csv(USERS_CSV, index=False)

if not os.path.exists(TXNS_CSV):
    pd.DataFrame(columns=[
        "txn_id",
        "user_id",
        "type",
        "amount",
        "timestamp",
        "note"
    ]).to_csv(TXNS_CSV, index=False)

if not os.path.exists(LOANS_CSV):
    pd.DataFrame(columns=[
        "loan_id",
        "user_id",
        "name",
        "father_name",
        "aadhaar",
        "address",
        "principal",
        "duration_years",
        "loan_type",
        "interest_rate",
        "calculated_interest",
        "applied_at",
        "status"
    ]).to_csv(LOANS_CSV, index=False)


def read_users() -> pd.DataFrame:
    return pd.read_csv(USERS_CSV, dtype=str).fillna("")


def write_users(df: pd.DataFrame) -> None:
    df.to_csv(USERS_CSV, index=False)


def read_txns() -> pd.DataFrame:
    return pd.read_csv(TXNS_CSV, dtype={"amount": float}).fillna("")


def write_txns(df: pd.DataFrame) -> None:
    df.to_csv(TXNS_CSV, index=False)


def read_loans() -> pd.DataFrame:
    return pd.read_csv(LOANS_CSV, dtype=str).fillna("")


def write_loans(df: pd.DataFrame) -> None:
    df.to_csv(LOANS_CSV, index=False)


def get_next_id(series) -> str:
    if series.empty:
        return "1"
    try:
        return str(int(series.astype(int).max()) + 1)
    except Exception:
        return str(len(series) + 1)


app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = APP_SECRET


@app.context_processor
def inject_globals():
    return {"BANK_NAME": "BANK OF NIAGARA"}


@app.route("/")
def home():
    user_name = None
    if "user_id" in session:
        users = read_users()
        match = users[users["user_id"] == str(session["user_id"])].head(1)
        if not match.empty:
            user_name = match.iloc[0]["name"]
    return render_template("index.html", user_name=user_name)


@app.route("/admin/migrate-ids", methods=["POST"])  # one-time helper
def migrate_ids():
    # Map old user_id -> new starting from 1001 in order of current IDs
    users = read_users()
    if users.empty:
        flash("No users to migrate", "info")
        return redirect(url_for("home"))
    # Sort by numeric value when possible
    try:
        users_sorted = users.copy()
        users_sorted["_num"] = users_sorted["user_id"].astype(int)
        users_sorted = users_sorted.sort_values("_num")
    except Exception:
        users_sorted = users.copy()
    mapping = {}
    current = 1001
    for _, row in users_sorted.iterrows():
        mapping[str(row["user_id"]) ] = str(current)
        current += 1

    # Apply mapping on users
    users["user_id"] = users["user_id"].astype(str).map(mapping)
    write_users(users)

    # Update transactions and loans foreign keys
    txns = read_txns()
    if not txns.empty:
        txns["user_id"] = txns["user_id"].astype(str).map(lambda x: mapping.get(x, x))
        write_txns(txns)
    loans = read_loans()
    if not loans.empty:
        loans["user_id"] = loans["user_id"].astype(str).map(lambda x: mapping.get(x, x))
        write_loans(loans)

    # Fix current session user_id if logged in
    if "user_id" in session:
        session["user_id"] = mapping.get(str(session["user_id"]), session["user_id"])

    flash("User IDs migrated to start from 1001", "success")
    return redirect(url_for("home"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        users = read_users()
        match = users[(users["name"].str.lower() == name.lower()) & (users["password"] == password)]
        if not match.empty:
            session["user_id"] = str(match.iloc[0]["user_id"])  # store as string
            flash("Login successful", "success")
            return redirect(url_for("home"))
        flash("Invalid credentials", "error")
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age = request.form.get("age", "").strip()
        address = request.form.get("address", "").strip()
        aadhaar = request.form.get("aadhaar", "").strip()
        father_name = request.form.get("father_name", "").strip()
        mother_name = request.form.get("mother_name", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not password:
            flash("Name and Password are required", "error")
            return render_template("signup.html")
        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template("signup.html")

        users = read_users()
        if (users["name"].str.lower() == name.lower()).any():
            flash("User with this name already exists", "error")
            return render_template("signup.html")

        # Generate account numbers starting from 1001
        if users.empty:
            new_id = "1001"
        else:
            try:
                max_existing = users["user_id"].astype(int).max()
            except Exception:
                max_existing = 1000
            new_id = str(max(1000, int(max_existing)) + 1)

        new_user = {
            "user_id": new_id,
            "name": name,
            "age": age,
            "address": address,
            "aadhaar": aadhaar,
            "father_name": father_name,
            "mother_name": mother_name,
            "password": password,
        }
        users = pd.concat([users, pd.DataFrame([new_user])], ignore_index=True)
        write_users(users)
        session["user_id"] = new_id
        flash("Account created successfully", "success")
        return redirect(url_for("home"))
    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("home"))


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        flash("Please login first", "error")
        return redirect(url_for("login"))

    user_id = str(session["user_id"])  # keep consistent as string
    users = read_users()
    user_row = users[users["user_id"].astype(str) == user_id].head(1)
    user_name = user_row.iloc[0]["name"] if not user_row.empty else ""

    txns = read_txns()
    txns_user = txns[txns["user_id"].astype(str) == user_id].copy()
    balance = txns_user.apply(lambda r: r["amount"] if r["type"] == "deposit" else -r["amount"], axis=1).sum() if not txns_user.empty else 0.0

    if request.method == "POST":
        action = request.form.get("action", "withdraw").lower()
        try:
            amount = float(request.form.get("amount", "0").strip() or 0)
        except ValueError:
            amount = 0
        if amount <= 0:
            flash("Enter a valid amount", "error")
            return render_template("dashboard.html", balance=balance, txns=txns_user.sort_values("timestamp", ascending=False), user_name=user_name, account_number=user_id)

        new_txn_id = get_next_id(txns["txn_id"]) if not txns.empty else "1"
        if action == "deposit":
            new_txn = {
                "txn_id": new_txn_id,
                "user_id": user_id,
                "type": "deposit",
                "amount": amount,
                "timestamp": datetime.utcnow().isoformat(),
                "note": "Cash Deposit"
            }
            txns = pd.concat([txns, pd.DataFrame([new_txn])], ignore_index=True)
            write_txns(txns)
            flash("Deposit successful", "success")
            return redirect(url_for("dashboard"))
        else:
            if amount > balance:
                flash("Insufficient balance", "error")
                return render_template("dashboard.html", balance=balance, txns=txns_user.sort_values("timestamp", ascending=False), user_name=user_name, account_number=user_id)
            new_txn = {
                "txn_id": new_txn_id,
                "user_id": user_id,
                "type": "withdrawal",
                "amount": amount,
                "timestamp": datetime.utcnow().isoformat(),
                "note": "ATM Withdrawal"
            }
            txns = pd.concat([txns, pd.DataFrame([new_txn])], ignore_index=True)
            write_txns(txns)
            flash("Withdrawal successful", "success")
            return redirect(url_for("dashboard"))

    return render_template("dashboard.html", balance=balance, txns=txns_user.sort_values("timestamp", ascending=False), user_name=user_name, account_number=user_id)


@app.route("/pay", methods=["GET", "POST"])
def pay():
    if "user_id" not in session:
        flash("Please login first", "error")
        return redirect(url_for("login"))

    users = read_users()
    recipient = None
    confirmation = None

    if request.method == "POST":
        action = request.form.get("action", "lookup")
        acct = request.form.get("account_number", "").strip()
        amount_str = request.form.get("amount", "").strip()
        try:
            amount = float(amount_str or 0)
        except ValueError:
            amount = 0

        if action == "lookup":
            recipient = users[users["user_id"].astype(str) == acct].head(1)
            if recipient.empty:
                flash("No user found with that account number", "error")
            else:
                recipient = recipient.iloc[0].to_dict()
        elif action == "transfer":
            if amount <= 0:
                flash("Enter a valid amount", "error")
            else:
                # Check balance
                payer_id = str(session["user_id"])
                txns = read_txns()
                txns_payer = txns[txns["user_id"].astype(str) == payer_id].copy()
                balance = txns_payer.apply(lambda r: r["amount"] if r["type"] == "deposit" else -r["amount"], axis=1).sum() if not txns_payer.empty else 0.0
                if amount > balance:
                    flash("Insufficient balance", "error")
                else:
                    # Validate recipient exists
                    rec = users[users["user_id"].astype(str) == acct].head(1)
                    if rec.empty:
                        flash("Recipient account not found", "error")
                    else:
                        recipient = rec.iloc[0].to_dict()
                        # Create two transactions: payer withdrawal and recipient deposit
                        new_id1 = get_next_id(txns["txn_id"]) if not txns.empty else "1"
                        withdraw_txn = {
                            "txn_id": new_id1,
                            "user_id": payer_id,
                            "type": "withdrawal",
                            "amount": amount,
                            "timestamp": datetime.utcnow().isoformat(),
                            "note": f"Transfer to {acct}"
                        }
                        txns = pd.concat([txns, pd.DataFrame([withdraw_txn])], ignore_index=True)
                        new_id2 = get_next_id(txns["txn_id"]) if not txns.empty else "2"
                        deposit_txn = {
                            "txn_id": new_id2,
                            "user_id": str(rec.iloc[0]["user_id"]),
                            "type": "deposit",
                            "amount": amount,
                            "timestamp": datetime.utcnow().isoformat(),
                            "note": f"Transfer from {payer_id}"
                        }
                        txns = pd.concat([txns, pd.DataFrame([deposit_txn])], ignore_index=True)
                        write_txns(txns)
                        confirmation = {
                            "to_account": acct,
                            "to_name": recipient["name"],
                            "amount": amount
                        }
                        flash("Payment sent", "success")

    return render_template("pay.html", recipient=recipient, confirmation=confirmation)


@app.route("/personal-loan", methods=["GET", "POST"])
def personal_loan():
    calc = None
    applied = False
    if request.method == "POST":
        action = request.form.get("action")
        principal_str = request.form.get("principal", "0").strip()
        duration_years_str = request.form.get("duration_years", "0").strip()
        try:
            principal = float(principal_str or 0)
            duration_years = float(duration_years_str or 0)
        except ValueError:
            principal = 0
            duration_years = 0
        interest_rate = 9.0
        if action == "calc":
            calc = {
                "principal": principal,
                "duration_years": duration_years,
                "interest_rate": interest_rate,
                "interest": (principal * interest_rate * duration_years) / 100.0
            }
        elif action == "apply":
            name = request.form.get("name", "").strip()
            father_name = request.form.get("father_name", "").strip()
            aadhaar = request.form.get("aadhaar", "").strip()
            account_number = request.form.get("account_number", "").strip()
            loans = read_loans()
            new_id = get_next_id(loans["loan_id"]) if not loans.empty else "1"
            new_loan = {
                "loan_id": new_id,
                "user_id": account_number,
                "name": name,
                "father_name": father_name,
                "aadhaar": aadhaar,
                "address": "",
                "principal": str(principal),
                "duration_years": str(duration_years),
                "loan_type": "personal",
                "interest_rate": str(interest_rate),
                "calculated_interest": str((principal * interest_rate * duration_years) / 100.0),
                "applied_at": datetime.utcnow().isoformat(),
                "status": "applied",
            }
            loans = pd.concat([loans, pd.DataFrame([new_loan])], ignore_index=True)
            write_loans(loans)
            applied = True
            flash("Personal loan application submitted", "success")

    return render_template("personal_loan.html", calculation=calc, applied=applied)


@app.route("/loan", methods=["GET", "POST"])
def loan():
    calculation = None
    applied = False
    if request.method == "POST":
        action = request.form.get("action")
        loan_type = request.form.get("loan_type", "home")
        principal_str = request.form.get("principal", "0").strip()
        duration_years_str = request.form.get("duration_years", "0").strip()
        try:
            principal = float(principal_str or 0)
            duration_years = float(duration_years_str or 0)
        except ValueError:
            principal = 0
            duration_years = 0

        interest_rate = 8.0 if loan_type == "home" else 5.0
        calculated_interest = (principal * interest_rate * duration_years) / 100.0
        calculation = {
            "principal": principal,
            "duration_years": duration_years,
            "interest_rate": interest_rate,
            "interest": calculated_interest,
        }

        if action == "apply":
            name = request.form.get("name", "").strip()
            father_name = request.form.get("father_name", "").strip()
            aadhaar = request.form.get("aadhaar", "").strip()
            address = request.form.get("address", "").strip()
            user_id = str(session.get("user_id", ""))

            loans = read_loans()
            new_id = get_next_id(loans["loan_id"]) if not loans.empty else "1"
            new_loan = {
                "loan_id": new_id,
                "user_id": user_id,
                "name": name,
                "father_name": father_name,
                "aadhaar": aadhaar,
                "address": address,
                "principal": str(principal),
                "duration_years": str(duration_years),
                "loan_type": loan_type,
                "interest_rate": str(interest_rate),
                "calculated_interest": str(calculated_interest),
                "applied_at": datetime.utcnow().isoformat(),
                "status": "applied",
            }
            loans = pd.concat([loans, pd.DataFrame([new_loan])], ignore_index=True)
            write_loans(loans)
            applied = True
            flash("Loan application submitted", "success")

    return render_template("loan.html", calculation=calculation, applied=applied)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
