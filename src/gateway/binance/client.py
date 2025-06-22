from typing import Dict, Optional, List, Union, Any
from binance.client import Client as BinanceClient
from binance.exceptions import BinanceAPIException, BinanceRequestException
from binance.enums import *
import time


class Client:
    """
    Wrapper around the official python-binance Client to maintain compatibility
    with the existing codebase while using the official library.
    """
    
    # Constants for compatibility
    TIME_IN_FORCE_GTC = "GTC"
    TIME_IN_FORCE_IOC = "IOC"
    TIME_IN_FORCE_FOK = "FOK"
    
    ORDER_TYPE_LIMIT = "LIMIT"
    ORDER_TYPE_MARKET = "MARKET"
    ORDER_TYPE_STOP_LOSS = "STOP_LOSS"
    ORDER_TYPE_STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
    ORDER_TYPE_TAKE_PROFIT = "TAKE_PROFIT"
    ORDER_TYPE_TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"
    ORDER_TYPE_LIMIT_MAKER = "LIMIT_MAKER"
    
    SIDE_BUY = "BUY"
    SIDE_SELL = "SELL"
    
    KLINE_INTERVAL_1MINUTE = "1m"
    KLINE_INTERVAL_3MINUTE = "3m"
    KLINE_INTERVAL_5MINUTE = "5m"
    KLINE_INTERVAL_15MINUTE = "15m"
    KLINE_INTERVAL_30MINUTE = "30m"
    KLINE_INTERVAL_1HOUR = "1h"
    KLINE_INTERVAL_2HOUR = "2h"
    KLINE_INTERVAL_4HOUR = "4h"
    KLINE_INTERVAL_6HOUR = "6h"
    KLINE_INTERVAL_8HOUR = "8h"
    KLINE_INTERVAL_12HOUR = "12h"
    KLINE_INTERVAL_1DAY = "1d"
    KLINE_INTERVAL_3DAY = "3d"
    KLINE_INTERVAL_1WEEK = "1w"
    KLINE_INTERVAL_1MONTH = "1M"

    # Aggregate trade constants
    AGG_ID = "a"
    AGG_PRICE = "p"
    AGG_QUANTITY = "q"
    AGG_FIRST_TRADE_ID = "f"
    AGG_LAST_TRADE_ID = "l"
    AGG_TIME = "T"
    AGG_BUYER_MAKES = "m"
    AGG_BEST_MATCH = "M"

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        requests_params: Optional[Dict[str, Any]] = None,
        tld: str = "com",
        base_endpoint: str = "",
        testnet: bool = False,
        private_key: Optional[Union[str, Any]] = None,
        private_key_pass: Optional[str] = None,
        ping: Optional[bool] = True,
        time_unit: Optional[str] = None,
    ):
        """
        Initialize the Binance client wrapper.
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            requests_params: Additional request parameters
            tld: Top level domain (com, us, etc.)
            base_endpoint: Base endpoint number
            testnet: Whether to use testnet
            private_key: Private key for RSA/Ed25519 signing (not supported in this wrapper)
            private_key_pass: Private key password (not supported in this wrapper)
            ping: Whether to ping the server on initialization
            time_unit: Time unit for requests
        """
        self._client = BinanceClient(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet,
            tld=tld
        )
        
        if ping:
            self.ping()

    def ping(self) -> Dict:
        """Test connectivity to the Rest API."""
        try:
            return self._client.ping()
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_server_time(self) -> Dict:
        """Check server time."""
        try:
            return self._client.get_server_time()
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_exchange_info(self) -> Dict:
        """Current exchange trading rules and symbol information."""
        try:
            return self._client.get_exchange_info()
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get symbol information."""
        try:
            exchange_info = self._client.get_exchange_info()
            for symbol_info in exchange_info['symbols']:
                if symbol_info['symbol'] == symbol:
                    return symbol_info
            return None
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_order_book(self, **params) -> Dict:
        """Get order book for a symbol."""
        try:
            return self._client.get_order_book(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_recent_trades(self, **params) -> Dict:
        """Get recent trades for a symbol."""
        try:
            return self._client.get_recent_trades(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_historical_trades(self, **params) -> Dict:
        """Get older trades for a symbol."""
        try:
            return self._client.get_historical_trades(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_aggregate_trades(self, **params) -> Dict:
        """Get compressed, aggregate trades."""
        try:
            return self._client.get_aggregate_trades(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def aggregate_trade_iter(self, symbol, start_str=None, last_id=None):
        """Iterate over aggregate trades for a symbol."""
        if start_str is not None and last_id is not None:
            raise ValueError(
                "start_str and last_id may not be simultaneously specified."
            )

        # If no start_str was passed, then we will fetch the most recent
        # aggregate trades.
        if start_str is None:
            trades = self.get_aggregate_trades(symbol=symbol)
        else:
            trades = self.get_aggregate_trades(symbol=symbol, fromId=start_str)

        for t in trades:
            yield t

        while len(trades) > 0:
            # If we're here, then we have more data to fetch.
            # The last trade we received has an ID of trades[-1][AGG_ID].
            # We need to fetch from that ID onwards.
            last_id = trades[-1][self.AGG_ID]

            # This is a bit tricky. We need to fetch from the last_id
            # onwards, but the API doesn't support that directly.
            # So we fetch the most recent trades and filter out the ones
            # we already have.
            trades = self.get_aggregate_trades(symbol=symbol, fromId=last_id)
            # fromId=n returns a set starting with id n, but we already have
            # that one. So get rid of the first item in the result set.
            trades = trades[1:]
            if len(trades) == 0:
                return
            for t in trades:
                yield t

    def get_klines(self, **params) -> Dict:
        """Get kline/candlestick data for a symbol."""
        try:
            return self._client.get_klines(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_historical_klines(
        self,
        symbol: str,
        interval: str,
        start_str: Optional[str] = None,
        end_str: Optional[str] = None,
        limit: Optional[int] = None,
        klines_type: str = "SPOT"
    ) -> List:
        """Get historical kline data."""
        try:
            return self._client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_str,
                end_str=end_str,
                limit=limit
            )
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_ticker(self, **params) -> Dict:
        """Get 24hr ticker price change statistics."""
        try:
            return self._client.get_ticker(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_symbol_ticker(self, **params) -> Dict:
        """Get symbol price ticker."""
        try:
            return self._client.get_symbol_ticker(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_orderbook_ticker(self, **params) -> Dict:
        """Get best price/qty on the order book for a symbol."""
        try:
            return self._client.get_orderbook_ticker(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def create_order(self, **params) -> Dict:
        """Send in a new order."""
        try:
            return self._client.create_order(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def order_limit(
        self, 
        timeInForce: str = TIME_IN_FORCE_GTC, 
        **params
    ) -> Dict:
        """Send in a new limit order."""
        try:
            return self._client.order_limit(timeInForce=timeInForce, **params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def order_limit_buy(
        self, 
        timeInForce: str = TIME_IN_FORCE_GTC, 
        **params
    ) -> Dict:
        """Send in a new limit buy order."""
        try:
            return self._client.order_limit_buy(timeInForce=timeInForce, **params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def order_limit_sell(
        self, 
        timeInForce: str = TIME_IN_FORCE_GTC, 
        **params
    ) -> Dict:
        """Send in a new limit sell order."""
        try:
            return self._client.order_limit_sell(timeInForce=timeInForce, **params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def order_market(self, **params) -> Dict:
        """Send in a new market order."""
        try:
            return self._client.order_market(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def order_market_buy(self, **params) -> Dict:
        """Send in a new market buy order."""
        try:
            return self._client.order_market_buy(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def order_market_sell(self, **params) -> Dict:
        """Send in a new market sell order."""
        try:
            return self._client.order_market_sell(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_order(self, **params) -> Dict:
        """Check an order's status."""
        try:
            return self._client.get_order(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_all_orders(self, **params) -> Dict:
        """Get all account orders; active, canceled, or filled."""
        try:
            return self._client.get_all_orders(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def cancel_order(self, **params) -> Dict:
        """Cancel an active order."""
        try:
            return self._client.cancel_order(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_open_orders(self, **params) -> Dict:
        """Get all open orders on a symbol."""
        try:
            return self._client.get_open_orders(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_account(self, **params) -> Dict:
        """Get current account information."""
        try:
            return self._client.get_account(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_asset_balance(self, asset: Optional[str] = None, **params) -> Dict:
        """Get asset balance."""
        try:
            account = self._client.get_account(**params)
            if asset:
                for balance in account['balances']:
                    if balance['asset'] == asset:
                        return balance
                return {'asset': asset, 'free': '0.00000000', 'locked': '0.00000000'}
            return account
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_my_trades(self, **params) -> Dict:
        """Get trades for a specific account and symbol."""
        try:
            return self._client.get_my_trades(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_system_status(self) -> Dict:
        """Get system status."""
        try:
            return self._client.get_system_status()
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_account_status(self, **params) -> Dict:
        """Get account status."""
        try:
            return self._client.get_account_status(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_trade_fee(self, **params) -> Dict:
        """Get trade fee."""
        try:
            return self._client.get_trade_fee(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_asset_details(self, **params) -> Dict:
        """Get asset details."""
        try:
            return self._client.get_asset_details(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_deposit_history(self, **params) -> Dict:
        """Get deposit history."""
        try:
            return self._client.get_deposit_history(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_withdraw_history(self, **params) -> Dict:
        """Get withdrawal history."""
        try:
            return self._client.get_withdraw_history(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_deposit_address(self, coin: str, network: Optional[str] = None, **params) -> Dict:
        """Get deposit address."""
        try:
            return self._client.get_deposit_address(coin=coin, network=network, **params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def withdraw(self, **params) -> Dict:
        """Submit a withdraw request."""
        try:
            return self._client.withdraw(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_all_tickers(self, symbol: Optional[str] = None) -> List[Dict[str, str]]:
        """Get 24hr ticker price change statistics for all symbols."""
        try:
            return self._client.get_all_tickers()
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_orderbook_tickers(self, **params) -> Dict:
        """Get best price/qty on the order book for all symbols."""
        try:
            return self._client.get_orderbook_tickers(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_avg_price(self, **params) -> Dict:
        """Get current average price for a symbol."""
        try:
            return self._client.get_avg_price(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_symbol_ticker_window(self, **params) -> Dict:
        """Get ticker price change statistics for a symbol."""
        try:
            return self._client.get_symbol_ticker_window(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_ui_klines(self, **params) -> Dict:
        """Get UI klines (same as get_klines but with different response format)."""
        try:
            return self._client.get_ui_klines(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_products(self) -> Dict:
        """Return list of products currently listed on Binance."""
        try:
            return self._client.get_products()
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_current_order_count(self, **params) -> Dict:
        """Get current order count usage for all intervals."""
        try:
            return self._client.get_current_order_count(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def create_test_order(self, **params) -> Dict:
        """Test new order creation and signature/recvWindow long."""
        try:
            return self._client.create_test_order(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def stream_get_listen_key(self) -> str:
        """Start a new user data stream."""
        try:
            return self._client.stream_get_listen_key()
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def stream_keepalive(self, listenKey: str) -> Dict:
        """Keepalive a user data stream to prevent a timeout."""
        try:
            return self._client.stream_keepalive(listenKey)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def stream_close(self, listenKey: str) -> Dict:
        """Close out a user data stream."""
        try:
            return self._client.stream_close(listenKey)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    # Futures methods
    def futures_ping(self) -> Dict:
        """Test connectivity to the Rest API."""
        try:
            return self._client.futures_ping()
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_time(self) -> Dict:
        """Check server time."""
        try:
            return self._client.futures_time()
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_exchange_info(self) -> Dict:
        """Current exchange trading rules and symbol information."""
        try:
            return self._client.futures_exchange_info()
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_order_book(self, **params) -> Dict:
        """Get order book for a symbol."""
        try:
            return self._client.futures_order_book(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_recent_trades(self, **params) -> Dict:
        """Get recent trades for a symbol."""
        try:
            return self._client.futures_recent_trades(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_historical_trades(self, **params) -> Dict:
        """Get older trades for a symbol."""
        try:
            return self._client.futures_historical_trades(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_aggregate_trades(self, **params) -> Dict:
        """Get compressed, aggregate trades."""
        try:
            return self._client.futures_aggregate_trades(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_klines(self, **params) -> Dict:
        """Get kline/candlestick data for a symbol."""
        try:
            return self._client.futures_klines(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_historical_klines(
        self, 
        symbol: str, 
        interval: str, 
        start_str: str, 
        end_str: Optional[str] = None, 
        limit: int = 500
    ) -> List:
        """Get historical kline data."""
        try:
            return self._client.futures_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_str,
                end_str=end_str,
                limit=limit
            )
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_mark_price(self, **params) -> Dict:
        """Get mark price for a symbol."""
        try:
            return self._client.futures_mark_price(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_funding_rate(self, **params) -> Dict:
        """Get funding rate for a symbol."""
        try:
            return self._client.futures_funding_rate(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_ticker(self, **params) -> Dict:
        """Get 24hr ticker price change statistics."""
        try:
            return self._client.futures_ticker(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_symbol_ticker(self, **params) -> Dict:
        """Get symbol price ticker."""
        try:
            return self._client.futures_symbol_ticker(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_orderbook_ticker(self, **params) -> Dict:
        """Get best price/qty on the order book for a symbol."""
        try:
            return self._client.futures_orderbook_ticker(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_create_order(self, **params) -> Dict:
        """Send in a new futures order."""
        try:
            return self._client.futures_create_order(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_get_order(self, **params) -> Dict:
        """Check a futures order's status."""
        try:
            return self._client.futures_get_order(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_get_open_orders(self, **params) -> Dict:
        """Get all open futures orders on a symbol."""
        try:
            return self._client.futures_get_open_orders(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_get_all_orders(self, **params) -> Dict:
        """Get all futures account orders; active, canceled, or filled."""
        try:
            return self._client.futures_get_all_orders(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_cancel_order(self, **params) -> Dict:
        """Cancel an active futures order."""
        try:
            return self._client.futures_cancel_order(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_account_balance(self, **params) -> Dict:
        """Get futures account balance."""
        try:
            return self._client.futures_account_balance(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_account(self, **params) -> Dict:
        """Get futures account information."""
        try:
            return self._client.futures_account(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_position_information(self, **params) -> Dict:
        """Get futures position information."""
        try:
            return self._client.futures_position_information(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_account_trades(self, **params) -> Dict:
        """Get futures account trades."""
        try:
            return self._client.futures_account_trades(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_income_history(self, **params) -> Dict:
        """Get futures income history."""
        try:
            return self._client.futures_income_history(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_change_leverage(self, **params) -> Dict:
        """Change futures leverage."""
        try:
            return self._client.futures_change_leverage(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_change_margin_type(self, **params) -> Dict:
        """Change futures margin type."""
        try:
            return self._client.futures_change_margin_type(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_change_position_margin(self, **params) -> Dict:
        """Change futures position margin."""
        try:
            return self._client.futures_change_position_margin(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_position_margin_history(self, **params) -> Dict:
        """Get futures position margin history."""
        try:
            return self._client.futures_position_margin_history(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_stream_get_listen_key(self) -> str:
        """Start a new futures user data stream."""
        try:
            return self._client.futures_stream_get_listen_key()
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_stream_keepalive(self, listenKey: str) -> Dict:
        """Keepalive a futures user data stream to prevent a timeout."""
        try:
            return self._client.futures_stream_keepalive(listenKey)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def futures_stream_close(self, listenKey: str) -> Dict:
        """Close out a futures user data stream."""
        try:
            return self._client.futures_stream_close(listenKey)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    # Margin methods
    def get_margin_account(self, **params) -> Dict:
        """Get margin account information."""
        try:
            return self._client.get_margin_account(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_isolated_margin_account(self, **params) -> Dict:
        """Get isolated margin account information."""
        try:
            return self._client.get_isolated_margin_account(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def create_margin_order(self, **params) -> Dict:
        """Send in a new margin order."""
        try:
            return self._client.create_margin_order(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def cancel_margin_order(self, **params) -> Dict:
        """Cancel an active margin order."""
        try:
            return self._client.cancel_margin_order(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_margin_order(self, **params) -> Dict:
        """Check a margin order's status."""
        try:
            return self._client.get_margin_order(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_open_margin_orders(self, **params) -> Dict:
        """Get all open margin orders on a symbol."""
        try:
            return self._client.get_open_margin_orders(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_all_margin_orders(self, **params) -> Dict:
        """Get all margin account orders; active, canceled, or filled."""
        try:
            return self._client.get_all_margin_orders(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_margin_trades(self, **params) -> Dict:
        """Get margin trades for a specific account and symbol."""
        try:
            return self._client.get_margin_trades(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def transfer_spot_to_margin(self, **params) -> Dict:
        """Transfer from spot account to margin account."""
        try:
            return self._client.transfer_spot_to_margin(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def transfer_margin_to_spot(self, **params) -> Dict:
        """Transfer from margin account to spot account."""
        try:
            return self._client.transfer_margin_to_spot(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def create_margin_loan(self, **params) -> Dict:
        """Apply for a margin loan."""
        try:
            return self._client.create_margin_loan(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def repay_margin_loan(self, **params) -> Dict:
        """Repay margin loan."""
        try:
            return self._client.repay_margin_loan(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_margin_loan_details(self, **params) -> Dict:
        """Get margin loan details."""
        try:
            return self._client.get_margin_loan_details(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_margin_repay_details(self, **params) -> Dict:
        """Get margin repay details."""
        try:
            return self._client.get_margin_repay_details(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_margin_transfer_history(self, **params) -> Dict:
        """Get margin transfer history."""
        try:
            return self._client.get_margin_transfer_history(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_margin_interest_history(self, **params) -> Dict:
        """Get margin interest history."""
        try:
            return self._client.get_margin_interest_history(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_margin_price_index(self, **params) -> Dict:
        """Get margin price index."""
        try:
            return self._client.get_margin_price_index(**params)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def margin_stream_get_listen_key(self) -> str:
        """Start a new margin user data stream."""
        try:
            return self._client.margin_stream_get_listen_key()
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def margin_stream_keepalive(self, listenKey: str) -> Dict:
        """Keepalive a margin user data stream to prevent a timeout."""
        try:
            return self._client.margin_stream_keepalive(listenKey)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def margin_stream_close(self, listenKey: str) -> Dict:
        """Close out a margin user data stream."""
        try:
            return self._client.margin_stream_close(listenKey)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    # Additional utility methods
    def get_timestamp(self) -> int:
        """Get current timestamp in milliseconds."""
        return int(time.time() * 1000)

    def get_exchange_info_symbols(self) -> List[str]:
        """Get list of all trading symbols."""
        try:
            exchange_info = self._client.get_exchange_info()
            return [symbol['symbol'] for symbol in exchange_info['symbols']]
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_symbol_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol."""
        try:
            ticker = self._client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e))

    def get_24hr_ticker(self, symbol: str) -> Dict:
        """Get 24hr ticker for a specific symbol."""
        try:
            return self._client.get_ticker(symbol=symbol)
        except BinanceAPIException as e:
            raise BinanceAPIException(e.response, e.status_code, str(e))
        except BinanceRequestException as e:
            raise BinanceRequestException(str(e)) 