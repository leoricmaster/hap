import os
import time
import logging
from typing import Optional, Any, List, Dict
from tavily import TavilyClient
from hap.tools.base import Tool, ToolParameter
from hap.core.exceptions import ToolException

logger = logging.getLogger(__name__)


class WebSearch(Tool):
    """Web search tool using Tavily API."""

    # Maximum number of results to return from the search
    DEFAULT_MAX_RESULTS = 5

    # Maximum number of retries for failed API calls
    DEFAULT_MAX_RETRIES = 3

    # Delay between retries in seconds
    DEFAULT_RETRY_DELAY = 1.0

    # Preview length for content in characters
    CONTENT_PREVIEW_LENGTH = 200

    def __init__(
        self,
        max_results: int = DEFAULT_MAX_RESULTS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY
    ):
        super().__init__(
            name="search",
            description="A web search engine. Use this tool when you need to answer questions about current events, facts, or information not in your knowledge base."
        )
        self._max_results = max_results
        self._max_retries = max_retries
        self._retry_delay = retry_delay

        # Tavily-specific configuration (internal)
        self._tavily_key = os.getenv("TAVILY_API_KEY")
        self._tavily_client: Optional[TavilyClient] = None

    def get_parameters(self) -> List[ToolParameter]:
        """Get tool parameter definitions."""
        return [
            ToolParameter(
                name="query",
                type="string",
                description="Search query keywords",
                required=True
            )
        ]

    def _execute(self, parameters: Dict[str, Any]) -> str:
        """
        Execute search.

        Args:
            parameters: Dictionary containing query parameter (already validated)

        Returns:
            Search results

        Raises:
            ToolException: Search execution failed
        """
        query = parameters.get("query", "").strip()
        if not query:
            logger.warning("Search query is empty")
            raise ToolException("Search query cannot be empty")

        logger.info(f"Executing search: {query}")

        try:
            result = self._search_with_retry(query)
            logger.info("Search completed successfully")
            return result
        except ToolException:
            raise
        except Exception as e:
            logger.error(f"Search execution failed: {e}")
            raise ToolException(f"Search failed: {str(e)}") from e

    def _search_with_retry(self, query: str) -> str:
        """Execute search with retry mechanism."""
        last_exception = None

        for attempt in range(self._max_retries):
            try:
                return self._search_tavily(query)
            except ToolException:
                raise
            except Exception as e:
                last_exception = e
                if attempt < self._max_retries - 1:
                    logger.warning(
                        f"Search failed (attempt {attempt + 1}/{self._max_retries}): {e}, "
                        f"retrying in {self._retry_delay}s..."
                    )
                    time.sleep(self._retry_delay)
                else:
                    logger.error(f"Search failed after {self._max_retries} retries: {e}")
                    raise

        raise ToolException(f"Search failed: {str(last_exception)}") from last_exception

    def _search_tavily(self, query: str) -> str:
        """Execute search using Tavily API."""
        if not self._tavily_key:
            logger.error("TAVILY_API_KEY environment variable not set")
            raise ToolException(
                "TAVILY_API_KEY not configured. Please set TAVILY_API_KEY environment variable."
            )

        # Lazy initialization of client
        if self._tavily_client is None:
            self._tavily_client = TavilyClient(api_key=self._tavily_key)
            logger.debug("TavilyClient initialized")

        # Tavily-specific search options
        # search_depth: "basic" for fast standard results, "advanced" for comprehensive deep search
        tavily_options = {
            "search_depth": "basic",
            "include_answer": True,
            "max_results": self._max_results
        }

        try:
            logger.debug(f"Calling Tavily API: {query}")
            response = self._tavily_client.search(query=query, **tavily_options)
        except Exception as e:
            logger.error(f"Tavily API request failed: {e}")
            raise ToolException(f"Tavily API request failed: {str(e)}") from e

        return self._format_results(response, query)

    def _format_results(self, response: Dict[str, Any], query: str) -> str:
        """Format search results into readable text."""
        # Build result text
        result_lines = ["Tavily AI Search Results:", ""]

        # AI summary (if available)
        answer = response.get("answer")
        if answer:
            result_lines.append(f"AI Summary: {answer}")
            result_lines.append("")
            logger.debug(f"AI summary received, length: {len(answer)}")

        # Search results
        results = response.get("results", [])
        if results:
            result_lines.append("Related Results:")
            result_lines.append("")

            for i, item in enumerate(results[:self._max_results], 1):
                title = item.get("title", "")
                content = item.get("content", "")
                url = item.get("url", "")

                result_lines.append(f"[{i}] {title}")

                # Truncate content if too long
                if len(content) > self.CONTENT_PREVIEW_LENGTH:
                    content = content[:self.CONTENT_PREVIEW_LENGTH] + "..."
                result_lines.append(f"    {content}")
                result_lines.append(f"    Source: {url}")
                result_lines.append("")

            logger.debug(f"Retrieved {len(results)} results")
            return "\n".join(result_lines)

        logger.warning(f"No information found for '{query}'")
        return f"Sorry, no information found for '{query}'."
