import httpx
from django.core.exceptions import ValidationError

IDENTITY_RESOLVE_URL = "https://public.api.bsky.app/xrpc/com.atproto.identity.resolveHandle"


def resolve_handle_identity(handle: str) -> dict[str, str]:
    try:
        response = httpx.get(
            IDENTITY_RESOLVE_URL,
            params={"handle": handle},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ValidationError("Unable to verify the Bluesky handle. Please try again.") from exc

    did = payload.get("did")
    if not isinstance(did, str) or not did.startswith("did:"):
        raise ValidationError("Unable to verify the Bluesky handle. Please try again.")

    resolved_handle = payload.get("handle")
    if not isinstance(resolved_handle, str) or not resolved_handle.strip():
        resolved_handle = handle

    profile_identifier = resolved_handle or did
    return {
        "handle": resolved_handle,
        "did": did,
        "profile_url": f"https://bsky.app/profile/{profile_identifier}",
    }
