# debug.py
import gspread
from google.oauth2.service_account import Credentials
import toml

# Load secrets
with open('.streamlit/secrets.toml', 'r') as f:
    secrets = toml.load(f)

print("✅ Secrets loaded successfully")
print(f"Sections: {list(secrets.keys())}")

if 'gsheets' in secrets:
    creds_info = secrets['gsheets']
    print(f"\n📋 GSheets config keys: {list(creds_info.keys())}")
    
    # Check required fields
    required = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
    missing = [field for field in required if field not in creds_info]
    
    if missing:
        print(f"❌ Missing fields: {missing}")
    else:
        print("✅ All required fields present")
        
        # Try to connect
        try:
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
            client = gspread.authorize(creds)
            print("✅ Google Sheets API authorized!")
            
            # Try to open/create sheet
            try:
                sheet = client.open("SmartDataOrganizer_Users")
                print("✅ Found existing sheet!")
            except:
                sheet = client.create("SmartDataOrganizer_Users")
                print("✅ Created new sheet!")
                print(f"📄 Sheet URL: https://docs.google.com/spreadsheets/d/{sheet.id}")
                
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")