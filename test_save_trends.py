from src.news_agent.agents.db.sql_db import SQLiteTrendDB

db = SQLiteTrendDB("trends.db")
unsent = db.get_unsent_trends()
print("Unsent trends:", unsent)
