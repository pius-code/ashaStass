import os
import httpx
from dotenv import load_dotenv

load_dotenv()
asha_backend_url = os.getenv("ASHA_BACKEND", "http://localhost:8080")


async def claim_device_with_token(pairing_code: str, token: str):
    endpoint = f"{asha_backend_url.rstrip('/')}/api/v1/asha/claim_device"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with httpx.AsyncClient() as client:
            value = await client.post(
                endpoint,
                json={"pairing_code": pairing_code},
                headers=headers
            )
            data = value.json() if value.content else {}
            if value.status_code == 200 and data.get("valid"):
                return data
            else:
                detail = data.get("detail") or f"Backend returned HTTP {value.status_code}"
                return {"valid": False, "detail": detail}
    except Exception as e:
        print(f"Error occurred claiming device: {e}")
        return {"valid": False, "detail": f"Connection error: {str(e)}"}
