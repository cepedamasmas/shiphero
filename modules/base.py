# modules/base.py

import time
import requests
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import json
from utils.logger import setup_logger
from utils.exceptions import AuthenticationError, APIError, RateLimitError
from config.config import Config

class ShipHeroAPI:
    """Base class for ShipHero API interactions."""
    
    def __init__(self):
        """Initialize the ShipHero API client."""
        self.logger = setup_logger(self.__class__.__name__)
        self.config = Config
        self.config.validate_config()
        
        self.access_token = self.config.ACCESS_TOKEN
        self.refresh_token = self.config.REFRESH_TOKEN
        self.email = self.config.EMAIL
        
        self._last_request_time = 0
        self._request_count = 0
        self._token_expires_at = None
        
        # Initialize headers with current access token
        self.headers = self._get_headers()

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def _refresh_access_token(self) -> None:
        """
        Refresh the access token using the refresh token.
        
        Raises:
            AuthenticationError: If token refresh fails
        """
        try:
            response = requests.post(
                f"{self.config.BASE_URL_AUTH}/auth/refresh",
                json={
                    "refresh_token": self.refresh_token,
                    "email": self.email
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self._token_expires_at = datetime.now() + timedelta(hours=1)
                self.headers = self._get_headers()
                self.logger.info("Access token refreshed successfully")
            else:
                error_msg = f"Failed to refresh access token. Status: {response.status_code}"
                if response.text:
                    error_msg += f", Response: {response.text}"
                raise AuthenticationError(error_msg)
                
        except Exception as e:
            self.logger.error(f"Error refreshing access token: {str(e)}")
            raise AuthenticationError(f"Token refresh failed: {str(e)}")

    def _make_request(
        self,
        query: str,
        variables: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make a GraphQL request to ShipHero API with retry logic and token refresh.
        
        Args:
            query (str): GraphQL query
            variables (Dict, optional): Query variables
            retry_count (int): Current retry attempt number
            
        Returns:
            Dict[str, Any]: API response
            
        Raises:
            APIError: If the request fails after all retries
            RateLimitError: If rate limit is exceeded
            AuthenticationError: If authentication fails
        """
        if retry_count >= self.config.MAX_RETRIES:
            raise APIError("Max retries exceeded")
            
        self._handle_rate_limiting()
        
        try:
            # Check if token refresh is needed
            if self._token_expires_at and datetime.now() >= self._token_expires_at:
                self._refresh_access_token()
            
            payload = {
                "query": query,
                "variables": variables or {}
            }
            
            # Log the request details (without sensitive info)
            self.logger.debug(f"Making GraphQL request with variables: {json.dumps(variables or {})}")
            
            response = requests.post(
                self.config.BASE_URL,
                headers=self.headers,
                json=payload
            )
            
            self._request_count += 1
            
            # Log response status and details
            self.logger.debug(f"Response status: {response.status_code}")
            
            if response.status_code == 429:  # Rate limit exceeded
                raise RateLimitError("Rate limit exceeded")
                
            if response.status_code == 401:  # Unauthorized
                self._refresh_access_token()
                return self._make_request(query, variables, retry_count + 1)
                
            if response.status_code != 200:
                error_msg = f"API request failed with status {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f"\nResponse: {json.dumps(error_detail, indent=2)}"
                except:
                    error_msg += f"\nResponse Text: {response.text}"
                
                self.logger.error(error_msg)
                raise APIError(
                    error_msg,
                    status_code=response.status_code,
                    response=response.json() if response.text else None
                )
            
            response_data = response.json()
            
            # Check for GraphQL errors
            if 'errors' in response_data:
                error_msg = f"GraphQL errors: {json.dumps(response_data['errors'], indent=2)}"
                self.logger.error(error_msg)
                raise APIError(error_msg)
            
            return response_data
            
        except requests.RequestException as e:
            error_msg = f"Request error: {str(e)}"
            self.logger.error(error_msg)
            if retry_count < self.config.MAX_RETRIES:
                time.sleep(self.config.RETRY_DELAY * (retry_count + 1))
                return self._make_request(query, variables, retry_count + 1)
            raise APIError(error_msg)
            
        except (RateLimitError, AuthenticationError) as e:
            raise e
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(error_msg)
            raise APIError(error_msg)

    def _handle_rate_limiting(self) -> None:
        """Handle rate limiting by implementing delay if necessary."""
        current_time = time.time()
        time_diff = current_time - self._last_request_time
        
        if time_diff < 60:  # Within the same minute
            if self._request_count >= self.config.MAX_REQUESTS_PER_MINUTE:
                sleep_time = 60 - time_diff
                self.logger.warning(f"Rate limit approached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                self._request_count = 0
                self._last_request_time = time.time()
        else:
            # Reset counters for new minute
            self._request_count = 0
            self._last_request_time = current_time