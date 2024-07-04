import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

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
        
        # Call function to upload directory contents
        upload_directory_contents(service, drive_folder_id, local_directory)
        print('Upload completed.')
    
    except HttpError as e:
        print(f"HTTP Error uploading files: {e}")
    except Exception as e:
        print(f"Error uploading files: {e}")

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

def upload_directory_contents(service, drive_folder_id, local_directory):
    # Iterate over all files and subdirectories in the local directory
    for root, dirs, files in os.walk(local_directory):
        # Upload files in the current directory
        for file_name in files:
            local_file_path = os.path.join(root, file_name)
            upload_file(service, drive_folder_id, local_file_path)
        
        # Upload subdirectories recursively
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            upload_folder(service, drive_folder_id, dir_path)

def upload_file(service, drive_folder_id, local_file_path):
    try:
        # Prepare file metadata and media object for upload
        file_metadata = {
            'name': os.path.basename(local_file_path),
            'parents': [drive_folder_id]
        }
        media = MediaFileUpload(local_file_path)
        
        # Execute upload request
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"Uploaded file: {local_file_path}")
    
    except HttpError as e:
        print(f"HTTP Error uploading file {local_file_path}: {e}")
    except Exception as e:
        print(f"Error uploading file {local_file_path}: {e}")

def upload_folder(service, drive_folder_id, local_folder_path):
    try:
        # Create folder metadata
        folder_metadata = {
            'name': os.path.basename(local_folder_path),
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [drive_folder_id]
        }
        
        # Create folder in Google Drive
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        folder_id = folder.get('id')
        print(f"Created folder: {local_folder_path} ({folder_id})")
        
        # Upload contents of the folder recursively
        upload_directory_contents(service, folder_id, local_folder_path)
    
    except HttpError as e:
        print(f"HTTP Error creating or uploading folder {local_folder_path}: {e}")
    except Exception as e:
        print(f"Error creating or uploading folder {local_folder_path}: {e}")

# Call the function to authenticate and upload files
authenticate_and_upload(SERVICE_ACCOUNT_FILE, drive_folder_id, local_directory)
