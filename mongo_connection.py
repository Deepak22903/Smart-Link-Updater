from pymongo import MongoClient

def get_database():
    """
    Connect to the MongoDB database using the provided connection string.
    Returns the database object.
    """
    CONNECTION_STRING = "mongodb+srv://deepakshitole4_db_user:6KiH8syvWCTNhh2D@smartlinkupdater.rpo4hmt.mongodb.net/SmartLinkUpdater?appName=SmartLinkUpdater"

    # Create a connection using MongoClient
    client = MongoClient(CONNECTION_STRING)

    # Return the specified database object
    return client["SmartLinkUpdater"]

# Example usage
if __name__ == "__main__":
    db = get_database()
    print("Connected to MongoDB database successfully!")