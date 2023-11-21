# filename: drive_file_listener.py

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from langchain.chains.summarize import load_summarize_chain
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import GoogleDriveLoader

# If modifying these SCOPES, delete your token.json file.
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
CLIENT_SECRET_FILE = 'token.json'
CREDS_FILE = 'credentials.json'
APPLICATION_NAME = 'Drive API Python Quickstart'

def get_credentials():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    """Gets valid user credentials from storage."""
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
          token.write(creds.to_json())
    return creds
def main():
    """Shows basic usage of the Google Drive API."""
    
    # check if token.json exists
    if not os.path.exists(CLIENT_SECRET_FILE):
        print("token.json not found. Please run drive_file_listener.py first.")
    try:
        loader = GoogleDriveLoader(
    # folder_id="1yucgL9WGgWZdM1TOuKkeghlPizuzMYb5",
    document_ids=["1vuuvRgsPtyE1O6fmH8iicV1qP5McYV-VR5k0fLl7py0"],
    token_path=CLIENT_SECRET_FILE,
    credentials_path=CREDS_FILE,
    # file_types=["document", "sheet"],
    # Optional: configure whether to recursively fetch files from subfolders. Defaults to False.
    # recursive=False,
)
        docs = loader.load()
        
        llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
        chain = load_summarize_chain(llm, chain_type="stuff")
        summary = chain.run(docs)
        print(f"Summary of {docs}: {summary}")
    except HttpError as e:
        print(e)
        

if __name__ == '__main__':
    main()
