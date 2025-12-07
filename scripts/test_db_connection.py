import psycopg2
import sys

def test_connection(port, password):
    print(f"Testing connection to port {port} with password '{password}'...")
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="newsaggregator",
            user="newsaggregator",
            password=password,
            port=port
        )
        conn.close()
        print(f"✅ SUCCESS: Connected to port {port}!")
        return True
    except Exception as e:
        print(f"❌ FAILED: Port {port}: {e}")
        return False

if __name__ == "__main__":
    # Test 1: Docker default (5433, newspassword)
    s1 = test_connection(5433, "newspassword")
    
    # Test 2: Common mistake (5432, newspassword)
    s2 = test_connection(5432, "newspassword")

    # Test 3: Example env password (5433, newspassword123)
    s3 = test_connection(5433, "newspassword123")

    if s1:
        print("\nRECOMMENDATION: Use port 5433 and password 'newspassword'.")
        sys.exit(0)
    elif s2:
        print("\nRECOMMENDATION: Use port 5432 and password 'newspassword'.")
        sys.exit(0)
    else:
        print("\nCould not connect. Ensure Docker is running.")
        sys.exit(1)
