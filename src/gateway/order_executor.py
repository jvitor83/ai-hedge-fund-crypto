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
            
            # Find the LOT_SIZE and NOTIONAL filters
            lot_size_filter = None
            notional_filter = None
            
            for filter_info in symbol_info.get('filters', []):
                if filter_info['filterType'] == 'LOT_SIZE':
                    lot_size_filter = filter_info
                elif filter_info['filterType'] == 'NOTIONAL':
                    notional_filter = filter_info
                elif filter_info['filterType'] == 'MIN_NOTIONAL':
                    notional_filter = filter_info
            
            if lot_size_filter:
                step_size = float(lot_size_filter['stepSize'])
                min_qty = float(lot_size_filter['minQty'])
                
                # Check for minimum notional value
                min_notional = 0.0
                if notional_filter:
                    min_notional = float(notional_filter.get('minNotional', 0.0))
                
                # Get current price to calculate minimum quantity for notional
                current_price = 0.0
                try:
                    ticker_price = self.client._client.get_symbol_ticker(symbol=symbol)
                    current_price = float(ticker_price['price'])
                except Exception as e:
                    logger.warning(f"Could not get current price for {symbol}: {e}")
                
                # Debug logging
                logger.info(f"Symbol {symbol}: step_size={step_size}, min_qty={min_qty}, min_notional={min_notional}, current_price={current_price}, input_quantity={quantity}")
                
                # Calculate minimum quantity needed to meet notional requirement
                min_qty_for_notional = 0.0
                if min_notional > 0 and current_price > 0:
                    min_qty_for_notional = min_notional / current_price
                
                # Use the higher of the two minimum requirements
                effective_min_qty = max(min_qty, min_qty_for_notional)
                
                # Ensure quantity meets minimum requirement
                if quantity < effective_min_qty:
                    logger.warning(f"Quantity {quantity} is below effective minimum {effective_min_qty} for {symbol} (lot: {min_qty}, notional: {min_qty_for_notional}), adjusting to minimum")
                    quantity = effective_min_qty
                
                # Round to step size
                if step_size > 0:
                    quantity = round(quantity / step_size) * step_size
                
                # After rounding, ensure we still meet minimum notional
                if min_notional > 0 and current_price > 0:
                    while quantity * current_price < min_notional * 1.001:  # 0.1% safety margin
                        quantity += step_size if step_size > 0 else 0.1
                
                # Calculate precision based on step size
                precision = 0
                if step_size < 1:
                    precision = len(str(step_size).split('.')[-1].rstrip('0'))
                
                # Format with appropriate precision
                formatted_quantity = f"{quantity:.{precision}f}"
                
                # Remove trailing zeros and decimal point if it's a whole number
                if precision == 0:
                    formatted_quantity = str(int(quantity))
                else:
                    formatted_quantity = f"{quantity:.{precision}f}".rstrip('0').rstrip('.')
                
                logger.info(f"Formatted quantity for {symbol}: {formatted_quantity}")
                
                # Final validation - check if the order value meets minimum notional
                if min_notional > 0 and current_price > 0:
                    order_value = float(formatted_quantity) * current_price
                    if order_value < min_notional:
                        logger.error(f"Order value {order_value} is still below minimum notional {min_notional} for {symbol}")
                        raise ValueError(f"Order value {order_value} USDT is below minimum notional {min_notional} USDT for {symbol}")
                
                return formatted_quantity
            else:
                # Default to 8 decimal places if no filter found
                logger.warning(f"No LOT_SIZE filter found for {symbol}, using default formatting")
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
        
        # Debug logging for all decisions
        logger.info(f"OrderExecutor received decision for {ticker}: action={action}, quantity={quantity}, confidence={confidence}")
        
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
            
            # Add debug logging
            logger.info(f"Executing buy order for {ticker}: original_quantity={quantity}, formatted_quantity={formatted_quantity}")
            
            # Validate quantity is not zero or negative
            if float(formatted_quantity) <= 0:
                raise ValueError(f"Invalid quantity: {formatted_quantity}")
            
            # Use market order for immediate execution - use native client directly
            order = self.client._client.order_market_buy(
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
            
            order = self.client._client.order_market_sell(
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