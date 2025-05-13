import base64
import mimetypes
import os
import tempfile

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def build_drive_service(obj):
    service_account_json_key = obj.env['ir.config_parameter'].sudo().get_param('google_drive_service_account_json_key_file_path')
    scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/drive.file']
    cred = service_account.Credentials.from_service_account_file(filename=service_account_json_key, scopes=scopes)
    return build('drive', 'v3', credentials=cred)


def create_folder_on_drive(obj, name, parent_id=None):
    metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        metadata['parents'] = [parent_id]
    service = build_drive_service(obj)
    file = service.files().create(body=metadata, fields='id').execute()
    return file['id']


def create_stream_file(name, file_data):
    folder = tempfile.gettempdir()
    file_path = os.path.join(folder, name)
    with open(file_path, 'wb') as fp:
        fp.write(base64.decodestring(file_data))
    return file_path


def create_file_on_drive(obj, file_metadata, path):
    mimetype = mimetypes.guess_type(file_metadata['name'])
    media = MediaFileUpload(path, mimetype=mimetype[0])
    service = build_drive_service(obj)
    drive_file_obj = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    drive_file_obj['download_link'] = 'https://drive.google.com/uc?export=download&id='+drive_file_obj['id']
    new_permission = {'type': 'anyone', 'role': 'reader'}
    service.permissions().create(fileId=drive_file_obj['id'], body=new_permission, transferOwnership=False).execute()
    return drive_file_obj


def delete_file_from_drive(obj, file_id):
    service = build_drive_service(obj)
    service.files().delete(fileId=file_id).execute()
