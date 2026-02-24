# #!/usr/bin/env python3
# """
# Reset database and recreate all tables (DEVELOPMENT ONLY - WILL DELETE ALL DATA)
# """
# import sys
# import os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from app import create_app, db

# def reset_database():
#     app = create_app()
    
#     with app.app_context():
#         try:
#             print("WARNING: This will delete all data!")
#             confirm = input("Type 'YES' to continue: ")
            
#             if confirm != 'YES':
#                 print("Aborted.")
#                 return
            
#             print("Dropping all tables...")
#             db.drop_all()
            
#             print("Creating all tables...")
#             db.create_all()
            
#             print("Database reset completed!")
            
#         except Exception as e:
#             print(f"Reset failed: {e}")
#             db.session.rollback()

# if __name__ == '__main__':
#     reset_database()

