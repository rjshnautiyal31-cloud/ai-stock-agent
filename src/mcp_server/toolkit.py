import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AlphaVantageToolKit:
    """
    Type-safe Alpha Vantage API integration toolkit using Object-Oriented design.
    Requires a valid Alpha Vantage API key upon instantiation.
    """
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("Alpha Vantage API key must not be empty.")
        self._api_key = api_key
        logger.info("Initialized AlphaVantageToolKit successfully.")

    def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Queries the Alpha Vantage GLOBAL_QUOTE endpoint to retrieve real-time pricing metrics.
        
        Args:
            symbol (str): The stock ticker symbol (e.g., "AAPL", "MSFT").

        Returns:
            Dict[str, Any]: Parsed JSON response containing global stock quote metrics.

        Raises:
            ValueError: If the ticker symbol is invalid.
            requests.RequestException: If the HTTP request fails.
            RuntimeError: If the API returns an error structure.
        """
        if not symbol or not symbol.strip():
            raise ValueError("Ticker symbol must not be empty.")

        symbol = symbol.strip().upper()
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self._api_key
        }

        logger.info(f"Querying GLOBAL_QUOTE for ticker: {symbol}")
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Alpha Vantage returns errors inside standard 200 responses sometimes
            if "Error Message" in data:
                error_msg = data["Error Message"]
                logger.error(f"Alpha Vantage API error for {symbol}: {error_msg}")
                raise RuntimeError(f"Alpha Vantage API error: {error_msg}")
                
            if "Note" in data:
                # API limit warning
                logger.warning(f"Alpha Vantage API Rate Limit Warning: {data['Note']}")
                
            # If the response doesn't have the Global Quote key, it might be an invalid symbol
            if "Global Quote" not in data or not data["Global Quote"]:
                logger.error(f"Invalid response or symbol not found: {symbol}. Data: {data}")
                raise ValueError(f"Ticker symbol '{symbol}' was not found or returned no quote data.")

            logger.info(f"Successfully retrieved quote for ticker: {symbol}")
            return data["Global Quote"]

        except requests.RequestException as re:
            logger.error(f"HTTP request failed while fetching quote for {symbol}: {re}")
            raise
        except Exception as e:
            if not isinstance(e, (ValueError, RuntimeError, requests.RequestException)):
                logger.error(f"Unexpected error while fetching stock quote for {symbol}: {e}")
            raise
