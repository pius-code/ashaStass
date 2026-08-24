from pydantic import BaseModel


class StassClaimRequest(BaseModel):
    pairing_code: str
    channel: str
    address: str
    token: str
