from supabase import create_client, Client
from app.config import settings

class SupabaseStorage:
    def __init__(self):
        self.client: Client = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_KEY
        )

    async def upload_file(self, bucket: str, file_path: str, file_bytes: bytes, content_type: str):
        """Upload file to Supabase Storage"""
        try:
            response = self.client.storage.from_(bucket).upload(
                file_path,
                file_bytes,
                file_options={"content-type": content_type}
            )
            return response
        except Exception as e:
            raise Exception(f"Upload failed: {str(e)}")

    def get_public_url(self, bucket: str, file_path: str):
        """Get public URL for the file"""
        return self.client.storage.from_(bucket).get_public_url(file_path)

# Singleton instance
supabase_storage = SupabaseStorage()