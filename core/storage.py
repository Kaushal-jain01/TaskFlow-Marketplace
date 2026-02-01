from django.core.files.storage import Storage
from django.conf import settings
from supabase import create_client, Client
import mimetypes
from io import BytesIO

class SupabaseStorage(Storage):
    def __init__(self):
        self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_API_KEY)
        self.bucket = getattr(settings, 'SUPABASE_BUCKET', 'taskflow-marketplace-completion-proofs')

    def _save(self, name: str, content) -> str:
        """Upload file to Supabase"""
        # Read file content
        content_file = content.file
        content_file.seek(0)
        file_bytes = BytesIO(content_file.read())
        
        # Get content type
        content_type, _ = mimetypes.guess_type(name)
        if content_type is None:
            content_type = 'application/octet-stream'

        # Upload to Supabase
        self.supabase.storage.from_(self.bucket).upload(
            name, 
            file_bytes, 
            {"content-type": content_type}
        )
        return name

    def url(self, name: str, parameters=None, expire=None) -> str:
        """Get public URL"""
        return f"{settings.SUPABASE_URL}/storage/v1/object/public/{self.bucket}/{name}"

    def exists(self, name: str) -> bool:
        """Check if file exists (optional, returns True for simplicity)"""
        return True

    def delete(self, name: str) -> None:
        """Delete file from Supabase"""
        self.supabase.storage.from_(self.bucket).remove([name])

    def size(self, name: str) -> int:
        """Get file size (optional)"""
        return 0
