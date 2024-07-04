import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Global variables
completed_files = 0
total_files = 0

# Path to your service account key file
SERVICE_ACCOUNT_FILE = r"C:\Users\dani\Desktop\MinecraftServerAutomatization\graphic-theory-428210-p5-756b975287c1.json"

# Google Drive folder ID where you want to upload the files
drive_folder_id = '13925S0Jeq3cBGemSf2H0Q5FonCA2msGK'

# Local directory whose contents you want to upload
local_directory = 'C:/Users/dani/Desktop/ServerDownloadTest/'

# Scopes required to access Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate_and_upload(service_account_file, drive_folder_id, local_directory):
    # Authenticate using the service account key file
    credentials = service_account.Credentials.from_service_account_file(
        service_account_file, scopes=SCOPES)
    
    # Create a service object
    service = build('drive', 'v3', credentials=credentials)
    
    try:
        # Check if the drive_folder_id already has contents
        if check_folder_contents(service, drive_folder_id):
            # Ask for confirmation to delete existing contents
            confirm = input(f"The folder {drive_folder_id} already has contents. Do you want to delete them before uploading? (y/n): ")
            if confirm.lower() == 'y':
                delete_folder_contents(service, drive_folder_id)
            else:
                print("Upload aborted.")
                return
        
        # Calculate total number of files to be uploaded
        global total_files
        total_files = count_files(local_directory)
        
        # Upload contents of the local directory recursively
        upload_directory(service, drive_folder_id, local_directory)
        print('Upload completed.')
    
    except HttpError as e:
        print(f"HTTP Error uploading files: {e}")
    except Exception as e:
        print(f"Error uploading files: {e}")

def count_files(directory):
    # Recursively count total number of files in a directory
    count = 0
    for root, dirs, files in os.walk(directory):
        count += len(files)
    return count

def check_folder_contents(service, folder_id):
    # Check if the folder has any contents (files or subfolders)
    query = f"'{folder_id}' in parents"
    results = service.files().list(q=query, pageSize=1, fields="files(id)").execute()
    items = results.get('files', [])
    return bool(items)

def delete_folder_contents(service, folder_id):
    try:
        # Query to list all files and folders in the folder
        query = f"'{folder_id}' in parents"
        results = service.files().list(q=query, pageSize=1000, fields="files(id)").execute()
        items = results.get('files', [])

        # Delete each file and folder
        for item in items:
            service.files().delete(fileId=item['id']).execute()
            print(f"Deleted item: {item['id']}")

        print(f"All contents of folder {folder_id} deleted.")

    except HttpError as e:
        print(f"HTTP Error deleting folder contents: {e}")
    except Exception as e:
        print(f"Error deleting folder contents: {e}")

def upload_directory(service, drive_folder_id, local_directory):
    # Recursively upload a local directory to a Google Drive folder.
    for root, dirs, files in os.walk(local_directory):
        relative_path = os.path.relpath(root, local_directory)
        current_drive_folder_id = drive_folder_id

        # Create folders in Google Drive as needed
        if relative_path != '.':
            current_drive_folder_id = create_or_get_folder(service, drive_folder_id, relative_path)

        # Upload files in the current directory
        for file_name in files:
            local_file_path = os.path.join(root, file_name)
            upload_file(service, current_drive_folder_id, local_file_path)

def create_or_get_folder(service, parent_folder_id, folder_path):
    # Create a folder in Google Drive or get its ID if it already exists.
    folder_names = folder_path.split(os.sep)
    current_folder_id = parent_folder_id

    for folder_name in folder_names:
        # Check if the folder already exists in the current directory
        query = f"name = '{folder_name}' and '{current_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])

        if items:
            current_folder_id = items[0]['id']
        else:
            # Folder doesn't exist, create it
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [current_folder_id]
            }
            folder = service.files().create(body=folder_metadata, fields='id').execute()
            current_folder_id = folder.get('id')
            print(f"Created folder: {folder_name} with ID: {current_folder_id}")

    return current_folder_id

def upload_file(service, drive_folder_id, local_file_path):
    # Upload a file to a specific Google Drive folder.
    try:
        global completed_files
        completed_files += 1
        
        file_metadata = {
            'name': os.path.basename(local_file_path),
            'parents': [drive_folder_id]
        }
        media = MediaFileUpload(local_file_path, resumable=True)
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"Uploaded file: {local_file_path} ({completed_files}/{total_files})")

    except HttpError as e:
        print(f"HTTP Error uploading file {local_file_path}: {e}")
    except Exception as e:
        print(f"Error uploading file {local_file_path}: {e}")

# Call the function to authenticate and upload files
authenticate_and_upload(SERVICE_ACCOUNT_FILE, drive_folder_id, local_directory)