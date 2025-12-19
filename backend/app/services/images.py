import httpx
from sqlmodel import Session, select
from app.db.engine import engine
from app.models.assets import ImageCache, ResourceType
from app.logger import structlog

logger = structlog.get_logger()
IMAGE_SERVER_BASE = "https://images.evetech.net"

class ImageService:
    async def get_image(self, resource_type: ResourceType, resource_id: int, variant: str) -> bytes:
        """
        Retrieves image from Cache (Postgres) or fetches from EVE Image Server.
        """
        with Session(engine) as session:
            # 1. Check Cache
            statement = select(ImageCache).where(
                ImageCache.resource_type == resource_type,
                ImageCache.resource_id == resource_id,
                ImageCache.variant == variant
            )
            cached_image = session.exec(statement).first()
            
            if cached_image:
                logger.info("image_cache_hit", type=resource_type, id=resource_id)
                return cached_image.blob_data

            # 2. Cache Miss - Fetch from Upstream
            logger.info("image_cache_miss", type=resource_type, id=resource_id)
            
            # Construct URL
            # https://images.evetech.net/{resource_type}/{resource_id}/{variant}
            # Note: For characters, corporations, alliances, the URL structure is consistent.
            # Types: https://images.evetech.net/types/587/icon
            
            # Handle pluralization if needed by API? 
            # EVE Image Server uses plurals usually: 'types', 'characters', 'corporations', 'alliances'.
            # ResourceType enum is singular. Mapping needed.
            
            type_map = {
                ResourceType.type: "types",
                ResourceType.character: "characters",
                ResourceType.corporation: "corporations",
                ResourceType.alliance: "alliances"
            }
            
            url_type = type_map.get(resource_type)
            url = f"{IMAGE_SERVER_BASE}/{url_type}/{resource_id}/{variant}"
            
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    image_data = response.content
                    
                    # 3. Save to Cache
                    new_cache = ImageCache(
                        resource_type=resource_type,
                        resource_id=resource_id,
                        variant=variant,
                        blob_data=image_data
                    )
                    session.add(new_cache)
                    session.commit()
                    
                    return image_data
                except Exception as e:
                    logger.error("image_fetch_failed", url=url, error=str(e))
                    # Return placeholder or re-raise? 
                    # For now re-raise to let 404 propagate if invalid ID
                    raise e

image_service = ImageService()
