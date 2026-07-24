"""
Tracks meal distribution, meal costs, and donor contributions for the
Hearts & Hunger outreach program. Generates summary reports and charts
from data stored in a local SQLite database.
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

def add_logo(fig):
    try:
        logo = mpimg.imread("logo.png")
        logo_ax = fig.add_axes([0.005, 0.01, 0.12, 0.12])  # left, bottom, width, height (fractions of figure)
        logo_ax.imshow(logo)
        logo_ax.axis("off")
    except FileNotFoundError:
        print("Logo file not found - skipping.")

def init_db():
    conn = sqlite3.connect("hearts_and_hunger.db")
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
    
    conn.commit()
    conn.close()


def log_meal(date, location, meal_count, notes="", cost=0):
    conn = sqlite3.connect("hearts_and_hunger.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO meals (date, location, meal_count, notes, cost) VALUES (?, ?, ?, ?, ?)",
        (date, location, meal_count, notes, cost)
    )
    conn.commit()
    conn.close()

def log_donor(name, date, amount, contact_info="", notes=""):
    conn = sqlite3.connect("hearts_and_hunger.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO donors (name, date, amount, contact_info, notes) VALUES (?, ?, ?, ?, ?)",
        (name, date, amount, contact_info, notes)
    )
    conn.commit()
    conn.close()

def log_store_donation(date, store_name, amount, notes=""):
    conn = sqlite3.connect("hearts_and_hunger.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO store_donations (date, store_name, amount, notes) VALUES (?, ?, ?, ?)",
        (date, store_name, amount, notes)
    )
    conn.commit()
    conn.close()

def meal_costs_log():
    conn = sqlite3.connect("hearts_and_hunger.db")
    df = pd.read_sql_query("SELECT * FROM meals ORDER BY date", conn)
    conn.close()
    
    print("\n--- Meal Costs ---")
    for _, row in df.iterrows():
        cost = row['cost'] if row['cost'] else 0
        print(f"{row['date']} | {row['notes']} | ${cost:.2f}")
    
    total_cost = df['cost'].sum()
    print(f"Total spent: ${total_cost:.2f}")

def meal_trends():
    conn = sqlite3.connect("hearts_and_hunger.db")
    df = pd.read_sql_query("SELECT * FROM meals", conn)
    conn.close()
    
    df["date"] = pd.to_datetime(df["date"])
    monthly = df.groupby(df["date"].dt.to_period("M"))["meal_count"].sum()
    
    print("\n--- Meals Distributed by Month ---")
    print(monthly.to_string())
    print(f"Total meals distributed: {monthly.sum()}")
    return monthly

def meal_log():
    conn = sqlite3.connect("hearts_and_hunger.db")
    df = pd.read_sql_query("SELECT * FROM meals ORDER BY date", conn)
    conn.close()
    
    print("\n--- Meal Log ---")
    for _, row in df.iterrows():
        print(f"{row['date']} | {row['location']} | {row['meal_count']} meals | {row['notes']}")
    
    return df
def add_cost_column():
    conn = sqlite3.connect("hearts_and_hunger.db")
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE meals ADD COLUMN cost REAL")
        conn.commit()
        print("Cost column added.")
    except sqlite3.OperationalError:
        print("Cost column already exists.")
    conn.close()

def store_donations_log():
    conn = sqlite3.connect("hearts_and_hunger.db")
    df = pd.read_sql_query("SELECT * FROM store_donations ORDER BY date", conn)
    conn.close()
    
    print("\n--- Store Donations ---")
    for _, row in df.iterrows():
        print(f"{row['date']} | {row['store_name']} | ${row['amount']:.2f} | {row['notes']}")
    
    return df

def donor_summary():
    conn = sqlite3.connect("hearts_and_hunger.db")
    df = pd.read_sql_query("SELECT * FROM donors", conn)
    conn.close()
    
    total_by_donor = df.groupby("name")["amount"].sum().sort_values(ascending=False)
    
    print("\n--- Donor Contributions ---")
    print(total_by_donor.to_string())
    print(f"Total raised: ${total_by_donor.sum():.2f}")
    return total_by_donor


def plot_meal_trends():
    conn = sqlite3.connect("hearts_and_hunger.db")
    df = pd.read_sql_query("SELECT * FROM meals", conn)
    conn.close()
    
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    
    monthly_meals = df.groupby(df["date"].dt.to_period("M"))["meal_count"].sum()
    
    df_with_cost = df[df["cost"] > 0].copy()
    monthly_cost = df_with_cost.groupby(df_with_cost["date"].dt.to_period("M"))["cost"].sum()
    monthly_meals_costed = df_with_cost.groupby(df_with_cost["date"].dt.to_period("M"))["meal_count"].sum()
    
    monthly_cost = monthly_cost.reindex(monthly_meals.index, fill_value=0)
    monthly_meals_costed = monthly_meals_costed.reindex(monthly_meals.index, fill_value=0)
    
    cumulative_cost_per_meal = monthly_cost.cumsum() / monthly_meals_costed.cumsum()
    
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
    ax2.plot(x, cumulative_cost_per_meal.values, color="orange", marker="o", linewidth=3, markersize=8, zorder=5)
    ax2.set_ylabel("Cumulative Cost per Meal ($)", color="orange")
    
    plt.tight_layout()
    add_logo(fig)
    plt.savefig("meal_trends.png")
    print("Chart saved as meal_trends.png")

def plot_meal_costs():
    conn = sqlite3.connect("hearts_and_hunger.db")
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
    conn = sqlite3.connect("hearts_and_hunger.db")
    df = pd.read_sql_query("SELECT * FROM meals", conn)
    conn.close()
    
    df["date"] = pd.to_datetime(df["date"])
    
    # Only keep rows where we actually have cost data
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

def reset_db():
    conn = sqlite3.connect("hearts_and_hunger.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM meals")
    cursor.execute("DELETE FROM donors")
    cursor.execute("DELETE FROM store_donations")
    conn.commit()
    conn.close()
    print("Database cleared.")

if __name__ == "__main__":
    print("Script started")
    init_db()

    meal_log()
    meal_costs_log()
    meal_trends()
    donor_summary()
    plot_meal_trends()
    plot_meal_costs()
    plot_cost_per_meal()