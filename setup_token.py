import os
import logging
from gmail_service import GmailService

def setup_token():
    """
    Standalone script to authenticate with Gmail API and save token.json.
    Useful for generating the token on a local machine before deploying,
    or just to separate authentication from the sending process.
    """
    print("🛠️  Gmail API Token Setup")
    print("="*30)
    
    if not os.path.exists("credentials.json"):
        print("❌ Error: 'credentials.json' not found.")
        print("Please download your OAuth 2.0 Credentials from Google Cloud Console")
        print("and save the file as 'credentials.json' in this directory.")
        print("\nSteps:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a Project > Enable 'Gmail API'")
        print("3. APIs & Services > Credentials > Create Credentials > OAuth client ID > Desktop app")
        print("4. Download JSON > Rename to 'credentials.json'")
        return

    try:
        print("🚀 Starting authentication flow...")
        print("A browser window should open. Please log in with your Google account.")
        
        # Initialize service which triggers the auth flow
        service = GmailService()
        
        if os.path.exists("token.json"):
            print("\n✅ Success! 'token.json' has been created/verified.")
            print("You can now run 'python main.py --live' to send emails using this token.")
        else:
            print("\n❌ Something went wrong. 'token.json' was not created.")
            
    except Exception as e:
        print(f"\n❌ Error during authentication: {e}")

if __name__ == "__main__":
    setup_token()
