from fastapi import APIRouter, HTTPException, Response
from app.models.assets import ResourceType
from app.services.images import image_service

router = APIRouter(prefix="/api/images", tags=["Images"])

@router.get("/{resource_type}/{resource_id}")
async def get_image(
    resource_type: ResourceType, 
    resource_id: int, 
    size: int = 64
):
    """
    Get cached image for EVE resource.
    """
    # Determine variant based on type
    variant = "icon"
    if resource_type == ResourceType.character:
        variant = "portrait"
    elif resource_type in [ResourceType.corporation, ResourceType.alliance]:
        variant = "logo"
        
    # EVE Image server uses 'icon?size=64' or 'portrait?size=64'
    # Actually, often the path is /types/1/icon?size=64
    # The variant variable above maps to strictly what EVE Image Server expects at the end path?
    # Checking EVE Image Server docs:
    # Character: /characters/{character_id}/portrait
    # Corporation: /corporations/{corporation_id}/logo
    # Type: /types/{type_id}/icon
    # So yes, logic holds.
    
    # We might want to handle query params for size in the upstream fetch, 
    # BUT caching 'size=64' vs 'size=128' separately would bloat DB.
    # PROMPT SPEC: "Query param: ?size=64 (default)."
    # Does prompt imply we ignore size for caching? 
    # "Save binary to Postgres ImageCache". 
    # If we cache 512px version, we can downscale? Or we just cache what is requested.
    # To prevent DB bloat, maybe force a specific size or include size in cache key?
    # The prompt's ImageCache model `variant` column is `icon`, `portrait`, `logo`. It does NOT have `size`.
    # This implies we might be caching ONE master size or the requested size under that variant name.
    # NOTE: user didn't ask for size in DB model.
    # I will assume we fetch/cache the request as-is, OR we fetch the largest and downscale?
    # Simplest interpretation: The 'variant' string in DB is just 'icon'/'logo'.
    # If users requests size=64 vs size=128, they get the SAME DB entry if I don't differentiate.
    # This suggests I should fetch a standard size (e.g. 64 or 512) and serve that. 
    # Or append size to variant e.g. "portrait_64".
    # I will append size to variant to be safe: f"{variant}_{size}" or pass size to upstream.
    # BUT prompt says: "Variants: For type use 'icon'..."
    # I will append query param to upstream URL but store with simple variant name if I want collisions? No.
    # I will store `variant` as `logo_64` to be safe and avoid serving 64px as 128px.
    
    # Wait, fetching "icon" from EVE usually defaults to something.
    # I will stick to caching exactly what is requested to avoid complexity.
    # Key = (type, id, "icon_64")
    
    full_variant = f"{variant}" # For URL
    # We need to pass ?size to upstream.
    # And store in DB with unique key.
    # Let's store variant as "icon_64" in DB?
    # Prompt Model: `variant` (icon, portrait, logo).
    # Prompt didn't specify size column. 
    # I will append query params to the upstream call and maybe store it as `icon` if size is default?
    # Let's just use `variant` for the string that goes into the URL path segment, 
    # but since size is a query param, it's NOT part of the path variant.
    # https://images.evetech.net/types/34/icon?size=64
    # If I ignore size in storage, I might cache a 32px image and serve it when 512px is requested.
    # I will modify logic to fetch `size=128` (decent default) if not specified, 
    # but actually the simplest path is: ignore size for cache key (store default), OR include size in variant key.
    
    # Prompt says: "Query param: ?size=64 (default)." 
    # I will just pass `?size={size}` to upstream. 
    # And I will use `f"{variant}_{size}"` as the stored variant key to ensure uniqueness.
    
    db_variant = f"{variant}_{size}"
    
    try:
        # We need to hack the service a bit to support query params in URL if validation is strict,
        # or just pass the full "icon?size=64" as the variant? 
        # Upstream construction was: f"{IMAGE_SERVER_BASE}/{url_type}/{resource_id}/{variant}"
        # So passing variant="icon?size=64" works for URL.
        # It also works for DB string column.
        
        upstream_variant_str = f"{variant}?size={size}"
        
        image_data = await image_service.get_image(resource_type, resource_id, upstream_variant_str)
        
        return Response(content=image_data, media_type="image/jpeg") # EVE Images are usually JPG or PNG
    except Exception as e:
        raise HTTPException(status_code=404, detail="Image not found")
