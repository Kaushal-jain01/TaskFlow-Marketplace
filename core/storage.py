from django.core.files.storage import Storage
from django.conf import settings
import requests
import mimetypes
import posixpath

class SupabaseStorage(Storage):
    def __init__(self):
        self._base_url = settings.SUPABASE_URL  # ✅ FIXED: Rename to avoid conflict
        self.key = settings.SUPABASE_API_KEY
        self.bucket = getattr(settings, 'SUPABASE_BUCKET', 'taskflow-marketplace-completion-proofs')
        self.headers = {
            'Authorization': f'Bearer {self.key}',
            'apikey': self.key
        }

    def _save(self, name: str, content) -> str:
        print(f"📤 UPLOADING {name}")
        
        # ✅ FIX: Convert Windows \ → Unix / using posixpath
        clean_name = posixpath.join(*name.split('\\')).replace('\\', '/')
        print(f"📤 CLEAN NAME: {clean_name}")
        
        file_bytes = content.read()
        content_type, _ = mimetypes.guess_type(clean_name) or ('image/png',)
        
        upload_url = f"{self._base_url}/storage/v1/object/{self.bucket}/{clean_name}"
        files = {'file': (clean_name, file_bytes, content_type)}
        
        response = requests.post(upload_url, headers=self.headers, files=files)
        
        if response.status_code in [200, 201]:
            print(f"✅ UPLOADED {clean_name}")
            return clean_name  # Return clean name to database
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            raise Exception(f"Upload failed: {response.text}")

    def url(self, name: str) -> str:
        """✅ FIXED: Now callable - generates CDN URL"""
        clean_name = name.replace('\\', '/')
        return f"{self._base_url}/storage/v1/object/public/{self.bucket}/{clean_name}"

    def exists(self, name):
        """Cloud-friendly exists check"""
        if not name:
            return False
        try:
            clean_name = name.replace('\\', '/')
            check_url = f"{self._base_url}/storage/v1/object/{self.bucket}/{clean_name}"
            r = requests.head(check_url, headers=self.headers, timeout=1)
            return r.status_code == 200
        except:
            return False  # Fast fallback

    def size(self, name):
        """Optional: Return file size"""
        try:
            clean_name = name.replace('\\', '/')
            check_url = f"{self._base_url}/storage/v1/object/{self.bucket}/{clean_name}"
            r = requests.head(check_url, headers=self.headers, timeout=1)
            return int(r.headers.get('Content-Length', 0))
        except:
            return 0
