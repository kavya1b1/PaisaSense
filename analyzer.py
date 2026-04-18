"""
PaisaSense AI — Data Analyzer
Enriches parsed transaction data and computes all financial stats and insights.
"""

import pandas as pd
from categorizer import categorize_transaction


def process_dataframe(df: pd.DataFrame) -> dict:
    """Enrich DataFrame and compute all stats."""

    # Use pre-computed Category if available (from parse_csv); otherwise derive it now
    if "Category" not in df.columns:
        df["Category"] = df["Merchant"].apply(categorize_transaction)

    # Override with salary / rent signals found in narration text
    if "Narration" in df.columns:
        salary_mask = df["Narration"].str.lower().str.contains(
            r"salary|sal credit|payroll|ctc|stipend", regex=True, na=False
        )
        df.loc[salary_mask, "Category"] = "Salary"

        rent_mask = df["Narration"].str.lower().str.contains(
            r"\brent\b|house rent|houserent|flat rent|room rent", regex=True, na=False
        )
        df.loc[rent_mask, "Category"] = "Bills"

    df["DayOfWeek"] = df["Date"].dt.day_name()
    df["IsWeekend"] = df["DayOfWeek"].isin(["Saturday", "Sunday"])

    # Summary stats
    total_spent    = float(df["Amount"].sum())
    avg_daily      = float(df.groupby(df["Date"].dt.date)["Amount"].sum().mean())
    num_txns       = int(len(df))
    date_range_days = max(1, (df["Date"].max() - df["Date"].min()).days + 1)

    # Category breakdown
    cat_totals   = df.groupby("Category")["Amount"].sum().round(2).to_dict()
    top_category = max(cat_totals, key=cat_totals.get) if cat_totals else "N/A"

    # Weekend vs weekday spending
    weekend_df    = df[df["IsWeekend"]]
    weekday_df    = df[~df["IsWeekend"]]
    weekend_total = float(weekend_df["Amount"].sum())
    weekday_total = float(weekday_df["Amount"].sum())
    weekend_pct   = round(weekend_total / total_spent * 100, 1) if total_spent else 0

    # Micro-transactions (< ₹200)
    small_txns      = df[df["Amount"] < 200]
    small_txn_count = int(len(small_txns))
    small_txn_total = float(small_txns["Amount"].sum())

    monthly_projection = round(avg_daily * 30, 2)

    # Financial Warning Engine
    risk_alert = None
    if avg_daily > 0:
        projected_days = int(10000 / avg_daily)
        if projected_days < 10:
            risk_alert = f"⚠️ At your current spending rate, your balance may drop critically in {projected_days} days."
        elif projected_days < 20:
            risk_alert = f"⚠️ At this pace, ₹10,000 would last only {projected_days} days. Consider reducing daily spend."

    # Subscription Detector (month-aware — must appear in 2+ distinct months)
    df["Month"] = df["Date"].dt.to_period("M")
    subscription_candidates = []
    merchant_month_groups = df.groupby(["Merchant", "Amount"])["Month"].nunique()
    for (merchant, amount), unique_months in merchant_month_groups.items():
        if unique_months >= 2:
            monthly_cost = float(amount)
            subscription_candidates.append({
                "merchant":     merchant,
                "amount":       monthly_cost,
                "count":        int(unique_months),
                "monthly_cost": monthly_cost,
                "yearly_cost":  round(monthly_cost * 12, 2),
            })
    subscription_total = sum(s["amount"] for s in subscription_candidates)

    # Budget Comparison (50/30/20 rule)
    ideal_budget   = {"Needs": total_spent * 0.5, "Wants": total_spent * 0.3, "Savings": total_spent * 0.2}
    wants_cats     = ["Food", "Shopping", "Travel"]
    split_wants    = ideal_budget["Wants"] / len(wants_cats)
    budget_comparison = {
        "Bills":    {"actual": cat_totals.get("Bills", 0),    "recommended": ideal_budget["Needs"]},
        "Food":     {"actual": cat_totals.get("Food", 0),     "recommended": split_wants},
        "Shopping": {"actual": cat_totals.get("Shopping", 0), "recommended": split_wants},
        "Travel":   {"actual": cat_totals.get("Travel", 0),   "recommended": split_wants},
    }

    decisions = _generate_decisions(
        cat_totals=cat_totals,
        top_category=top_category,
        weekend_total=weekend_total,
        weekend_pct=weekend_pct,
        total_spent=total_spent,
        small_txn_count=small_txn_count,
        monthly_projection=monthly_projection,
        subscriptions=subscription_candidates,
        subscription_total=subscription_total,
    )

    daily_series = (
        df.groupby(df["Date"].dt.strftime("%b %d"))["Amount"]
        .sum().round(2).to_dict()
    )

    # Savings potential
    food                     = cat_totals.get("Food", 0)
    shopping                 = cat_totals.get("Shopping", 0)
    potential_savings_month  = round((food * 0.2) + (shopping * 0.15), 0)
    potential_savings_year   = int(potential_savings_month * 12)

    # Smart highlight
    weekend_vs_weekday = round((weekend_total / max(weekday_total, 1)) * 100 - 100, 1)
    if weekend_vs_weekday > 20:
        highlight = f"You spend {weekend_vs_weekday}% more on weekends than weekdays."
    elif small_txn_count > 5:
        highlight = f"{small_txn_count} small expenses are silently draining your money."
    else:
        highlight = f"Your top spending category is {top_category}."

    # Budget over-alert
    budget_alert     = None
    food_recommended = split_wants
    if food_recommended > 0:
        food_overage_pct = round((food - food_recommended) / food_recommended * 100, 0)
        if food_overage_pct > 10:
            budget_alert = f"🍔 Food spending is {int(food_overage_pct)}% above recommended limit."

    return {
        "summary": {
            "total_spent":      round(total_spent, 2),
            "avg_daily_spend":  round(avg_daily, 2),
            "num_transactions": num_txns,
            "date_range_days":  date_range_days,
            "top_category":     top_category,
        },
        "category_totals": cat_totals,
        "behavior": {
            "weekend_total":  round(weekend_total, 2),
            "weekday_total":  round(weekday_total, 2),
            "weekend_pct":    weekend_pct,
            "small_txn_count": small_txn_count,
            "small_txn_total": round(small_txn_total, 2),
        },
        "prediction": {
            "monthly_projection": round(monthly_projection, 2),
            "days_left": int(ideal_budget["Needs"] / avg_daily) if avg_daily else 0,
        },
        "budget_comparison": budget_comparison,
        "subscriptions": {
            "total": round(subscription_total, 2),
            "items": subscription_candidates,
        },
        "savings": {
            "monthly": potential_savings_month,
            "yearly":  potential_savings_year,
        },
        "risk_alert":   risk_alert,
        "highlight":    highlight,
        "decisions":    decisions,
        "daily_trend":  daily_series,
        "yearly_spend": round(total_spent * (365 / date_range_days), 0),
        "budget_alert": budget_alert,
    }


def process_transactions(csv_text: str) -> dict:
    """Kept for backward compatibility — parses CSV text directly."""
    from parser import parse_csv
    return process_dataframe(parse_csv(csv_text))


def _generate_decisions(cat_totals, top_category, weekend_total, weekend_pct,
                        total_spent, small_txn_count, monthly_projection,
                        subscriptions, subscription_total):
    """Rule-based actionable financial decisions with color-coded types."""
    decisions = []

    food = cat_totals.get("Food", 0)
    if food > 0:
        saving = round(food * 0.20, 0)
        decisions.append({
            "icon": "🍔", "type": "warning",
            "title": "Food Spending Alert",
            "detail": f"Cutting food expenses by 20% could save you ₹{saving:,.0f}/month.",
        })

    shopping = cat_totals.get("Shopping", 0)
    if shopping > 3000:
        decisions.append({
            "icon": "🛍️", "type": "warning",
            "title": "High Shopping Spend",
            "detail": f"You spent ₹{shopping:,.0f} on shopping. Try a 7-day wishlist rule before purchases.",
        })

    if weekend_pct > 35:
        decisions.append({
            "icon": "📅", "type": "danger",
            "title": "Weekend Overspending",
            "detail": f"{weekend_pct}% of your spending happens on weekends (₹{weekend_total:,.0f}). Set a weekend budget.",
        })

    if small_txn_count > 10:
        decisions.append({
            "icon": "☕", "type": "info",
            "title": "Micro-Transaction Drain",
            "detail": f"{small_txn_count} small transactions (<₹200) collectively drain your wallet unnoticed.",
        })

    potential_savings = round(total_spent * 0.15, 0)
    decisions.append({
        "icon": "💰", "type": "success",
        "title": "Savings Opportunity",
        "detail": f"Optimizing your top categories could save approx. ₹{potential_savings:,.0f}/month.",
    })

    decisions.append({
        "icon": "📊", "type": "info",
        "title": "Monthly Projection",
        "detail": f"At your current pace, you'll spend ₹{monthly_projection:,.0f} this month.",
    })

    decisions.append({
        "icon": "💸", "type": "success",
        "title": "Annual Savings Potential",
        "detail": f"You could save approx ₹{int(total_spent * 0.15 * 12):,}/year by improving habits.",
    })

    if subscriptions:
        yearly = int(subscription_total * 12)
        decisions.append({
            "icon": "📺", "type": "warning",
            "title": "Subscription Alert",
            "detail": f"You have ₹{int(subscription_total)}/month in recurring payments — ₹{yearly:,}/year.",
        })

    return decisions
