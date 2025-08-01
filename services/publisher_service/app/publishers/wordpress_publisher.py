import logging
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost

from .base import BasePublisher
from ..models import Article

logger = logging.getLogger(__name__)

class WordpressPublisher(BasePublisher):

    @staticmethod
    def publish(credentials: dict, article: Article):
        wp = Client(credentials['site_url'], credentials['username'], credentials['application_password'])
        
        post = WordPressPost()
        post.title = article.processed_title
        post.content = article.processed_content
        post.post_status = 'publish' # Or 'draft'
        # post.terms_names = { 'category': ['...'], 'post_tag': ['...'] }

        post_id = wp.call(NewPost(post))
        logger.info(f"Article {article.id} published to WordPress with post ID {post_id}")
        return post_id