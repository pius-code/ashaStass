import os
import httpx
from dotenv import load_dotenv

load_dotenv()
asha_backend_url = os.getenv("ASHA_BACKEND", "http://localhost:8080")


# TODO: there has to be some form off authentication , otherwise anyone at all would be hitting that endpoint to check validity # noqa
async def check_pairing_code_validity(pairing_Code: str):
    endpoint = f"{asha_backend_url.rstrip('/')}/api/v1/asha/is_pairing_code_valid" # noqa
    try:
        async with httpx.AsyncClient() as client:
            value = await client.post(endpoint, json={
                "pairing_code": pairing_Code
            })
            if value.status_code == 200:
                data = value.json()
                if data.get("valid"):
                    return data
    except Exception as e:
        print(f"Error occurred: {e}")
    return None
