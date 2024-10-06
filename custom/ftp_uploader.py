from google.oauth2 import service_account
from google.cloud import storage
import json

class FTPUploader:
    def upload_file(self, local_file_path, file_name, isVideo=False):
        credential_json_path = "/home/admin/GCP_credentials.json"
        
        # Create credentials from the service account JSON file
        creds = service_account.Credentials.from_service_account_file(credential_json_path)

        # Initialize the storage client with the credentials
        storage_client = storage.Client(credentials=creds)

        # Get the bucket
        bucket = storage_client.get_bucket("ngsi-ld")
        #bucket = storage_client.get_bucket("sndgo_scd")

        # Create a blob object
        blob = bucket.blob(file_name)
        
        # Upload the file
        with open(local_file_path, 'rb') as f:
            if isVideo:
                blob.upload_from_file(f, content_type='video/mp4')
            else:
                blob.upload_from_file(f, content_type='image/jpeg')
            #blob.upload_from_file(f)
        
        print("Upload complete")
        url = blob.public_url
        print (url)
        #url = blob.generate_signed_url(expiration=3600, method='GET')

        return url
