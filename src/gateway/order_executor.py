import os
import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from src.gateway.binance.client import Client
from src.gateway.binance.exceptions import BinanceAPIException, BinanceOrderException

logger = logging.getLogger(__name__)

class OrderExecutor:
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, testnet: bool = True):
        """
        Initialize the order executor with Binance client
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Whether to use testnet (default True for safety)
        """
        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET")
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Binance API credentials are required for order execution")
        
        # Initialize Binance client
        self.client = Client(
            api_key=self.api_key,
            api_secret=self.api_secret,
            testnet=testnet
        )
        
        # Cache for symbol info
        self._symbol_info_cache = {}
        
        logger.info(f"Order executor initialized with testnet={testnet}")
    
    def _get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information including precision requirements"""
        if symbol not in self._symbol_info_cache:
            try:
                exchange_info = self.client.get_exchange_info()
                for s in exchange_info.get('symbols', []):
                    if s['symbol'] == symbol:
                        self._symbol_info_cache[symbol] = s
                        break
                else:
                    raise ValueError(f"Symbol {symbol} not found")
            except Exception as e:
                logger.error(f"Error getting symbol info for {symbol}: {e}")
                raise
        
        return self._symbol_info_cache[symbol]
    
    def _format_quantity(self, symbol: str, quantity: float) -> str:
        """Format quantity according to symbol precision requirements"""
        try:
            symbol_info = self._get_symbol_info(symbol)
            
            # Find the LOT_SIZE filter for quantity precision
            lot_size_filter = None
            for filter_info in symbol_info.get('filters', []):
                if filter_info['filterType'] == 'LOT_SIZE':
                    lot_size_filter = filter_info
                    break
            
            if lot_size_filter:
                step_size = float(lot_size_filter['stepSize'])
                # Calculate precision based on step size
                precision = 0
                if step_size < 1:
                    precision = len(str(step_size).split('.')[-1].rstrip('0'))
                
                # Round quantity to the required precision
                formatted_quantity = round(quantity, precision)
                return f"{formatted_quantity:.{precision}f}"
            else:
                # Default to 8 decimal places if no filter found
                return f"{quantity:.8f}"
                
        except Exception as e:
            logger.error(f"Error formatting quantity for {symbol}: {e}")
            # Fallback to 8 decimal places
            return f"{quantity:.8f}"
    
    def execute_decision(self, ticker: str, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trading decision for a specific ticker
        
        Args:
            ticker: Trading symbol (e.g., 'BTCUSDT')
            decision: Decision dictionary with action, quantity, confidence, reasoning
            
        Returns:
            Dictionary with execution result
        """
        action = decision.get("action", "hold")
        quantity = decision.get("quantity", 0.0)
        confidence = decision.get("confidence", 0.0)
        
        if action == "hold" or quantity <= 0:
            return {
                "ticker": ticker,
                "action": "hold",
                "executed": False,
                "reason": "No action required or invalid quantity"
            }
        
        try:
            if action == "buy":
                return self._execute_buy_order(ticker, quantity)
            elif action == "sell":
                return self._execute_sell_order(ticker, quantity)
            elif action == "short":
                return self._execute_short_order(ticker, quantity)
            elif action == "cover":
                return self._execute_cover_order(ticker, quantity)
            else:
                return {
                    "ticker": ticker,
                    "action": action,
                    "executed": False,
                    "reason": f"Unknown action: {action}"
                }
                
        except Exception as e:
            logger.error(f"Error executing {action} order for {ticker}: {str(e)}")
            return {
                "ticker": ticker,
                "action": action,
                "executed": False,
                "error": str(e)
            }
    
    def _execute_buy_order(self, ticker: str, quantity: float) -> Dict[str, Any]:
        """Execute a market buy order"""
        try:
            # Format quantity according to symbol precision
            formatted_quantity = self._format_quantity(ticker, quantity)
            
            # Use market order for immediate execution
            order = self.client.order_market_buy(
                symbol=ticker,
                quantity=formatted_quantity
            )
            
            logger.info(f"Buy order executed for {ticker}: {order}")
            
            return {
                "ticker": ticker,
                "action": "buy",
                "executed": True,
                "order_id": order.get("orderId"),
                "client_order_id": order.get("clientOrderId"),
                "quantity": formatted_quantity,
                "status": order.get("status"),
                "fills": order.get("fills", [])
            }
            
        except BinanceAPIException as e:
            logger.error(f"Binance API error for buy order {ticker}: {e}")
            raise
        except BinanceOrderException as e:
            logger.error(f"Binance order error for buy order {ticker}: {e}")
            raise
    
    def _execute_sell_order(self, ticker: str, quantity: float) -> Dict[str, Any]:
        """Execute a market sell order"""
        try:
            # Format quantity according to symbol precision
            formatted_quantity = self._format_quantity(ticker, quantity)
            
            order = self.client.order_market_sell(
                symbol=ticker,
                quantity=formatted_quantity
            )
            
            logger.info(f"Sell order executed for {ticker}: {order}")
            
            return {
                "ticker": ticker,
                "action": "sell",
                "executed": True,
                "order_id": order.get("orderId"),
                "client_order_id": order.get("clientOrderId"),
                "quantity": formatted_quantity,
                "status": order.get("status"),
                "fills": order.get("fills", [])
            }
            
        except BinanceAPIException as e:
            logger.error(f"Binance API error for sell order {ticker}: {e}")
            raise
        except BinanceOrderException as e:
            logger.error(f"Binance order error for sell order {ticker}: {e}")
            raise
    
    def _execute_short_order(self, ticker: str, quantity: float) -> Dict[str, Any]:
        """Execute a short order (margin trading)"""
        try:
            # Format quantity according to symbol precision
            formatted_quantity = self._format_quantity(ticker, quantity)
            
            # For short orders, we need to use margin trading
            order = self.client.create_margin_order(
                symbol=ticker,
                side="SELL",
                type="MARKET",
                quantity=formatted_quantity,
                isIsolated="FALSE"  # Use cross margin
            )
            
            logger.info(f"Short order executed for {ticker}: {order}")
            
            return {
                "ticker": ticker,
                "action": "short",
                "executed": True,
                "order_id": order.get("orderId"),
                "client_order_id": order.get("clientOrderId"),
                "quantity": formatted_quantity,
                "status": order.get("status"),
                "fills": order.get("fills", [])
            }
            
        except BinanceAPIException as e:
            logger.error(f"Binance API error for short order {ticker}: {e}")
            raise
        except BinanceOrderException as e:
            logger.error(f"Binance order error for short order {ticker}: {e}")
            raise
    
    def _execute_cover_order(self, ticker: str, quantity: float) -> Dict[str, Any]:
        """Execute a cover order (close short position)"""
        try:
            # Format quantity according to symbol precision
            formatted_quantity = self._format_quantity(ticker, quantity)
            
            # To cover a short position, we buy back the borrowed shares
            order = self.client.create_margin_order(
                symbol=ticker,
                side="BUY",
                type="MARKET",
                quantity=formatted_quantity,
                isIsolated="FALSE"
            )
            
            logger.info(f"Cover order executed for {ticker}: {order}")
            
            return {
                "ticker": ticker,
                "action": "cover",
                "executed": True,
                "order_id": order.get("orderId"),
                "client_order_id": order.get("clientOrderId"),
                "quantity": formatted_quantity,
                "status": order.get("status"),
                "fills": order.get("fills", [])
            }
            
        except BinanceAPIException as e:
            logger.error(f"Binance API error for cover order {ticker}: {e}")
            raise
        except BinanceOrderException as e:
            logger.error(f"Binance order error for cover order {ticker}: {e}")
            raise
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get current account information"""
        try:
            account_info = self.client.get_account()
            return account_info
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            raise
    
    def get_open_orders(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get open orders"""
        try:
            params = {}
            if symbol:
                params["symbol"] = symbol
            return self.client.get_open_orders(**params)
        except Exception as e:
            logger.error(f"Error getting open orders: {e}")
            raise 