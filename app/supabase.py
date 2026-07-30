from supabase import create_client, Client
from app.config import settings


class SupabaseStorage:
    def __init__(self):
        self.client: Client = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_KEY,
        )

    async def upload_file(
        self,
        bucket: str,
        file_path: str,
        file_bytes: bytes,
        content_type: str,
    ):
        try:
            return self.client.storage.from_(bucket).upload(
                file_path,
                file_bytes,
                file_options={"content-type": content_type},
            )
        except Exception as e:
            raise Exception(f"Upload failed: {str(e)}")

    def get_public_url(self, bucket: str, file_path: str) -> str:
        return self.client.storage.from_(bucket).get_public_url(file_path)

    async def delete_file(self, bucket: str, file_path: str) -> None:
        """Remove a single object from Supabase Storage."""
        try:
            self.client.storage.from_(bucket).remove([file_path])
        except Exception as e:
            raise Exception(f"Delete failed: {str(e)}")


supabase_storage = SupabaseStorage()