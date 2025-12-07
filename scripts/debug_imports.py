import sys
with open("debug_log.txt", "w") as f:
    f.write("Start\n")
    try:
        import sqlalchemy
        f.write("Imported sqlalchemy\n")
        from dotenv import load_dotenv
        f.write("Imported dotenv\n")
        sys.path.insert(0, ".")
        import app.database.base as db_base
        f.write("Imported app.database.base\n")
        f.write(f"DB URL: {db_base.DATABASE_URL}\n")
    except Exception as e:
        f.write(f"Error: {e}\n")
    f.write("Done\n")
