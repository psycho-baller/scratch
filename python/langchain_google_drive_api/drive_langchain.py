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
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate

# If modifying these SCOPES, delete your token.json file.
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
CLIENT_SECRET_FILE = 'token.json'
CREDS_FILE = 'credentials.json'
APPLICATION_NAME = 'Drive API Python Quickstart'

llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")

def generate_actionable_takeaways(docs):
    """Generates actionable takeaways from a list of documents
    
    Args:
        docs (list): list of documents
    Returns:
        actionable_takeaways (list): list of actionable takeaways
    """
    
    text_splitter = RecursiveCharacterTextSplitter(separators=["\n\n", "\n", "\r\n\r\n\r\n"], chunk_size=10000, chunk_overlap=200)
    split_docs = text_splitter.split_documents(docs)
    map_prompt = """
Write a concise summary of the following:
"{text}"
CONCISE SUMMARY:
"""
    map_prompt_template = PromptTemplate(template=map_prompt, input_variables=["text"])
    
    combine_prompt = """
Write a concise summary of the following text delimited by triple backquotes.
Return your response in bullet points which covers the key points of the text.
```{text}```
BULLET POINT SUMMARY:
"""
    combine_prompt_template = PromptTemplate(template=combine_prompt, input_variables=["text"])

    summary_chain = load_summarize_chain(llm=llm,
                                     chain_type='map_reduce',
                                     map_prompt=map_prompt_template,
                                     combine_prompt=combine_prompt_template,
#                                      verbose=True
                                    )
    output = summary_chain.run(split_docs)
    return output

def get_credentials():
    """Gets valid user credentials from storage."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
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
        actionable_takeaways = generate_actionable_takeaways(docs)
        print(f"Actionable takeaways: {actionable_takeaways}")
        
        # chain = load_summarize_chain(llm, chain_type="stuff")
        # summary = chain.run(docs)
        # print(f"Summary of {docs}: {summary}")
    except HttpError as e:
        print(e)
        

if __name__ == '__main__':
    main()
