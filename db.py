# In Python shell or add to app.py temporarily
import sqlite3

conn = sqlite3.connect('rideshare.db')
c = conn.cursor()

# Find and remove duplicate rides (keep only the latest one for each user-source-dest combo)
c.execute('''
    DELETE FROM rides 
    WHERE id NOT IN (
        SELECT MAX(id) 
        FROM rides 
        GROUP BY user_id, source, destination, created_at
    )
''')

conn.commit()
print(f"Removed {c.rowcount} duplicate rides")
conn.close()
