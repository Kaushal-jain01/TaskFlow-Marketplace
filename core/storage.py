from django.core.files.storage import Storage
from django.conf import settings
import requests
import mimetypes

class SupabaseStorage(Storage):
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_API_KEY
        self.bucket = getattr(settings, 'SUPABASE_BUCKET', 'taskflow-marketplace-completion-proofs')
        self.headers = {
            'Authorization': f'Bearer {self.key}',
            'apikey': self.key
        }

    def _save(self, name: str, content) -> str:
        print(f"📤 UPLOADING {name}")
        
        file_bytes = content.read()
        content_type, _ = mimetypes.guess_type(name) or ('image/png',)
        
        # Direct HTTP upload to Supabase Storage API
        upload_url = f"{self.url}/storage/v1/object/{self.bucket}/{name}"
        files = {'file': (name, file_bytes, content_type)}
        
        response = requests.post(upload_url, headers=self.headers, files=files)
        
        if response.status_code in [200, 201]:
            print(f"✅ UPLOADED {name}")
            return name
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            raise Exception(f"Upload failed: {response.text}")

    def url(self, name: str) -> str:
        return f"{self.url}/storage/v1/object/public/{self.bucket}/{name}"

    def exists(self, name):
        """Avoid infinite loops - cloud storage friendly"""
        if not name:
            return False
        
        # Quick check - don't always hit Supabase API
        if name.startswith('proofs/'):
            return False  # New uploads = don't exist yet
        
        # Optional: Real check for production
        try:
            check_url = f"{self.url}/storage/v1/object/{self.bucket}/{name}"
            r = requests.head(check_url, headers=self.headers, timeout=2)
            return r.status_code == 200
        except:
            return False

