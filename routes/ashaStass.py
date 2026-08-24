from fastapi import APIRouter
from schema.ashaStass import StassClaimRequest
from utils.asha import claim_device_with_token
from utils.redis import get_or_create_user_identity, r

router = APIRouter(prefix="/api/v1/stass", tags=["stass"])


@router.post("/claim_device")
async def claim_device_endpoint(payload: StassClaimRequest):
    """Claim device with token"""
    res = await claim_device_with_token(payload.pairing_code, payload.token)
    if not res or not res.get("valid"):
        detail = res.get("detail", "Failed to claim device") if res else "Backend connection error" # noqa
        return {"success": False, "detail": detail}

    identity_key, _ = get_or_create_user_identity(payload.channel, payload.address) # noqa
    r.hset(identity_key, "pairing_code", payload.pairing_code)

    project_name = res.get("project_name", "Device")
    try:
        print("Nothing in here yet")
    except Exception as e:
        print(f"Failed to send confirmation message: {e}")

    return {
        "success": True,
        "message": f"Device '{project_name}' paired successfully!",
        "project_name": project_name,
        "asha_id": res.get("asha_id")
    }
