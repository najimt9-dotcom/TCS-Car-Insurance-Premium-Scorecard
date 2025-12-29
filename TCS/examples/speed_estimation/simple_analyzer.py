from pymongo import MongoClient

def test_connection():
    try:
        # Test your working connection string
        client = MongoClient(
            "Mongodb connection String",
            serverSelectionTimeoutMS=5000
        )
        client.admin.command('ping')
        print("✅ MongoDB Connection SUCCESS!")
        
        # Test if database and collections exist
        db = client["traffic_analysis"]
        print("✅ Database accessible")
        print("📊 Collections:", db.list_collection_names())
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()