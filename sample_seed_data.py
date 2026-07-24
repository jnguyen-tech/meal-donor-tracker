from meal_tracker import log_meal, log_donor, reset_db, init_db

init_db()
reset_db()

# Example data — replace with your own records
log_meal("2026-07-11", "Sample Location", 100, "Example meal event", 250.00)
log_donor("Jane Doe", "2026-07-19", 50, "", "Cash")

print("Sample data seeded successfully.")