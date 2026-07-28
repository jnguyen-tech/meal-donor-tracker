"""
Hearts & Hunger Meal & Donor Tracker

Tracks meal distribution, meal costs, donor contributions, and food vs.
non-food expenses for the Hearts & Hunger outreach program. Generates
summary reports and charts from data stored in a local SQLite database.
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

DB_NAME = "hearts_and_hunger.db"


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

def init_db():
    """Create all tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            location TEXT NOT NULL,
            meal_count INTEGER NOT NULL,
            notes TEXT,
            cost REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS donors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            amount REAL,
            contact_info TEXT,
            notes TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS store_donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            store_name TEXT NOT NULL,
            amount REAL NOT NULL,
            notes TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            store TEXT,
            amount REAL NOT NULL,
            notes TEXT
        )
    """)

    conn.commit()
    conn.close()


def reset_db():
    """Delete all rows from every table. Use before re-seeding data from scratch."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM meals")
    cursor.execute("DELETE FROM donors")
    cursor.execute("DELETE FROM store_donations")
    cursor.execute("DELETE FROM expenses")
    conn.commit()
    conn.close()
    print("Database cleared.")


# ---------------------------------------------------------------------------
# Data entry
# ---------------------------------------------------------------------------

def log_meal(date, location, meal_count, notes="", cost=0):
    """Insert one meal distribution record. cost is the full event cost (food + non-food)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO meals (date, location, meal_count, notes, cost) VALUES (?, ?, ?, ?, ?)",
        (date, location, meal_count, notes, cost)
    )
    conn.commit()
    conn.close()


def log_donor(name, date, amount, contact_info="", notes=""):
    """Insert one individual donor contribution record."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO donors (name, date, amount, contact_info, notes) VALUES (?, ?, ?, ?, ?)",
        (name, date, amount, contact_info, notes)
    )
    conn.commit()
    conn.close()


def log_store_donation(date, store_name, amount, notes=""):
    """Insert one business/store donation record."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO store_donations (date, store_name, amount, notes) VALUES (?, ?, ?, ?)",
        (date, store_name, amount, notes)
    )
    conn.commit()
    conn.close()


def log_expense(date, category, amount, store="", notes=""):
    """Insert one expense record. category should be 'Food' or 'Non-Food'."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (date, category, store, amount, notes) VALUES (?, ?, ?, ?, ?)",
        (date, category, store, amount, notes)
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Reports (text output)
# ---------------------------------------------------------------------------

def meal_log():
    """Print every meal record in chronological order."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM meals ORDER BY date", conn)
    conn.close()

    print("\n--- Meal Log ---")
    for _, row in df.iterrows():
        print(f"{row['date']} | {row['location']} | {row['meal_count']} meals | {row['notes']}")

    return df


def meal_costs_log():
    """Print the cost of each meal event plus a running total."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM meals ORDER BY date", conn)
    conn.close()

    print("\n--- Meal Costs ---")
    for _, row in df.iterrows():
        cost = row['cost'] if row['cost'] else 0
        print(f"{row['date']} | {row['notes']} | ${cost:.2f}")

    total_cost = df['cost'].sum()
    print(f"Total spent: ${total_cost:.2f}")
    return df


def meal_trends():
    """Print and return total meals distributed, grouped by month."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM meals", conn)
    conn.close()

    df["date"] = pd.to_datetime(df["date"])
    monthly = df.groupby(df["date"].dt.to_period("M"))["meal_count"].sum()

    print("\n--- Meals Distributed by Month ---")
    print(monthly.to_string())
    print(f"Total meals distributed: {monthly.sum()}")
    return monthly


def donor_summary():
    """Print and return total contributions per individual donor, highest first."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM donors", conn)
    conn.close()

    total_by_donor = df.groupby("name")["amount"].sum().sort_values(ascending=False)

    print("\n--- Donor Contributions ---")
    print(total_by_donor.to_string())
    print(f"Total raised: ${total_by_donor.sum():.2f}")
    return total_by_donor


def store_donations_log():
    """Print every business/store donation record in chronological order."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM store_donations ORDER BY date", conn)
    conn.close()

    print("\n--- Store Donations ---")
    for _, row in df.iterrows():
        print(f"{row['date']} | {row['store_name']} | ${row['amount']:.2f} | {row['notes']}")

    return df


def expenses_log():
    """Print every expense record (food and non-food), plus category totals by month."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM expenses ORDER BY date", conn)
    conn.close()

    print("\n--- Expense Log ---")
    for _, row in df.iterrows():
        print(f"{row['date']} | {row['category']:<8} | {row['store']} | ${row['amount']:.2f} | {row['notes']}")

    df["date"] = pd.to_datetime(df["date"])
    monthly_by_category = df.groupby([df["date"].dt.to_period("M"), "category"])["amount"].sum().unstack(fill_value=0)

    print("\n--- Monthly Totals by Category ---")
    print(monthly_by_category.to_string())

    if "Non-Food" in monthly_by_category.columns:
        print("\n--- Non-Food Spending by Month ---")
        print(monthly_by_category["Non-Food"].to_string())

    totals = df.groupby("category")["amount"].sum()
    print("\nOverall Totals by Category:")
    print(totals.to_string())

    return df


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def add_logo(fig):
    """Stamp logo.png in the bottom-left corner of a chart, if it exists."""
    try:
        logo = mpimg.imread("logo.png")
        logo_ax = fig.add_axes([0.005, 0.01, 0.12, 0.12])  # left, bottom, width, height
        logo_ax.imshow(logo)
        logo_ax.axis("off")
    except FileNotFoundError:
        print("Logo file not found - skipping.")


def _monthly_cumulative_cost_per_meal(df):
    """Helper: cumulative (total cost so far / total meals so far), reindexed to every month."""
    monthly_meals = df.groupby(df["date"].dt.to_period("M"))["meal_count"].sum()

    df_with_cost = df[df["cost"] > 0].copy()
    monthly_cost = df_with_cost.groupby(df_with_cost["date"].dt.to_period("M"))["cost"].sum()
    monthly_meals_costed = df_with_cost.groupby(df_with_cost["date"].dt.to_period("M"))["meal_count"].sum()

    monthly_cost = monthly_cost.reindex(monthly_meals.index, fill_value=0)
    monthly_meals_costed = monthly_meals_costed.reindex(monthly_meals.index, fill_value=0)

    cumulative = monthly_cost.cumsum() / monthly_meals_costed.cumsum()
    return monthly_meals, cumulative


def plot_meal_trends():
    """Bar chart of meals distributed per month, with a line for cumulative cost-per-meal."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM meals", conn)
    conn.close()

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    monthly_meals, cumulative_cost_per_meal = _monthly_cumulative_cost_per_meal(df)

    x = range(len(monthly_meals))
    labels = [str(m) for m in monthly_meals.index]

    fig, ax1 = plt.subplots()

    ax1.bar(x, monthly_meals.values, color="steelblue")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(labels, rotation=90)
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Meals Distributed", color="steelblue")
    ax1.set_title("Meals Distributed by Month with Cumulative Cost per Meal")

    ax2 = ax1.twinx()
    ax2.plot(x, cumulative_cost_per_meal.values, color="orange",
             marker="o", linewidth=3, markersize=8, zorder=5)
    ax2.set_ylabel("Cumulative Cost per Meal ($)", color="orange")

    plt.tight_layout()
    add_logo(fig)
    plt.savefig("meal_trends.png")
    print("Chart saved as meal_trends.png")


def plot_meal_costs():
    """Bar chart of total meal cost per month."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM meals", conn)
    conn.close()

    df["date"] = pd.to_datetime(df["date"])
    monthly_cost = df.groupby(df["date"].dt.to_period("M"))["cost"].sum()

    fig = plt.figure()
    monthly_cost.plot(kind="bar", color="green")
    plt.title("Meal Costs by Month")
    plt.ylabel("Cost ($)")
    plt.xlabel("Month")
    plt.tight_layout()
    add_logo(fig)
    plt.savefig("meal_costs.png")
    print("Chart saved as meal_costs.png")


def plot_cost_per_meal():
    """Bar chart of cost-per-meal for each month that has recorded cost data."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM meals", conn)
    conn.close()

    df["date"] = pd.to_datetime(df["date"])
    df_with_cost = df[df["cost"] > 0]

    monthly_meals = df_with_cost.groupby(df_with_cost["date"].dt.to_period("M"))["meal_count"].sum()
    monthly_cost = df_with_cost.groupby(df_with_cost["date"].dt.to_period("M"))["cost"].sum()
    cost_per_meal = monthly_cost / monthly_meals

    fig = plt.figure()
    cost_per_meal.plot(kind="bar", color="orange")
    plt.title("Cost per Meal by Month (Months with Recorded Costs Only)")
    plt.ylabel("Cost per Meal ($)")
    plt.xlabel("Month")
    plt.tight_layout()
    add_logo(fig)
    plt.savefig("cost_per_meal.png")
    print("Chart saved as cost_per_meal.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Script started")
    init_db()

    meal_log()
    meal_costs_log()
    meal_trends()
    donor_summary()
    expenses_log()

    plot_meal_trends()
    plot_meal_costs()
    plot_cost_per_meal()