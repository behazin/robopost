import logging
import trafilatura
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Article, ArticleStatus, SourceDestinationMap, Destination
from .config import settings
# from .ai_client import AIClient # To be implemented

logger = logging.getLogger(__name__)

class ArticleProcessor:
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        # self.ai_client = AIClient(api_key=settings.GOOGLE_AI_API_KEY)

    async def process_article(self, url: str, source_id: int) -> int | None:
        """
        Processes a new article: fetches, cleans, processes with AI, and saves to DB.
        Returns the article ID if successful, otherwise None.
        """
        async with self.db_session_factory() as session:
            # 1. Idempotency Check
            existing_article = await session.scalar(select(Article).where(Article.original_url == url))
            if existing_article:
                logger.warning(f"Article with URL {url} already exists (ID: {existing_article.id}). Skipping.")
                return None

            # 2. Fetch and extract content
            logger.info(f"Fetching content from {url}")
            downloaded_content = trafilatura.fetch_url(url)
            if not downloaded_content:
                logger.error(f"Failed to download content for {url}")
                return None
            
            main_content = trafilatura.extract(downloaded_content, include_comments=False, include_tables=False)
            if not main_content:
                logger.warning(f"Could not extract main content from {url}")
                return None

            # 3. Process with AI (summarize, generate title, etc.)
            # This is a placeholder for the actual AI call.
            # processed_data = await self.ai_client.process(main_content)
            # For now, we'll use a simple placeholder:
            processed_data = {
                "title": trafilatura.extract(downloaded_content, include_comments=False, include_tables=False, with_metadata=True).get('title', 'Untitled'),
                "content": main_content[:2000] # Truncate for safety
            }
            logger.info(f"Content processed for {url}")

            # 4. Find assigned destinations for the source
            assigned_destinations = await self._get_active_destinations(session, source_id)
            if not assigned_destinations:
                logger.warning(f"No active destinations found for source {source_id}. Article will not be processed further.")
                # You might still want to save the article without destinations

            # 5. Create article in DB
            new_article = Article(
                source_id=source_id,
                original_url=url,
                status=ArticleStatus.PENDING_APPROVAL,
                processed_title=processed_data['title'],
                processed_content=processed_data['content'],
                assigned_destinations=assigned_destinations
            )
            session.add(new_article)
            await session.commit()
            await session.refresh(new_article)
            
            logger.info(f"New article created with ID: {new_article.id}")
            return new_article.id

    async def _get_active_destinations(self, session: AsyncSession, source_id: int) -> list:
        """Fetches all active destinations linked to a source."""
        stmt = (
            select(Destination.id, Destination.platform)
            .join(SourceDestinationMap, SourceDestinationMap.destination_id == Destination.id)
            .where(SourceDestinationMap.source_id == source_id, SourceDestinationMap.enabled == True)
        )
        result = await session.execute(stmt)
        return [{"destination_id": row.id, "platform": row.platform.value} for row in result.all()]