import httpx
from .config import settings
from fastapi import HTTPException

class SupabaseStorage:
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY
        self.headers = {
            "Authorization": f"Bearer {self.key}",
            "apikey": self.key,                    # ← This is critical
            "Content-Type": "application/json"
        }

    async def upload_file(self, bucket: str, file_path: str, file_bytes: bytes, content_type: str):
        """Upload a file to Supabase Storage"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.url}/storage/v1/object/{bucket}/{file_path}",
                    headers=self.headers,
                    files={"file": (file_path, file_bytes, content_type)}
                )
                
                print(f"Supabase Status Code: {response.status_code}")
                print(f"Supabase Response Body: {response.text}")

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                print(f"Supabase ERROR {e.response.status_code}: {e.response.text}")
                raise HTTPException(status_code=500, detail=f"Upload failed: {e.response.text}")
            except Exception as e:
                print(f"Unexpected error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    def get_public_url(self, bucket: str, file_path: str):
        return f"{self.url}/storage/v1/object/public/{bucket}/{file_path}"