#!/usr/bin/env python3
"""
Test script to isolate Binance order placement issues
"""
import os
from dotenv import load_dotenv
from binance.client import Client
from binance.exceptions import BinanceAPIException

load_dotenv()

def test_order_placement():
    """Test order placement directly with python-binance"""
    
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    
    if not api_key or not api_secret:
        print("❌ API credentials not found in environment variables")
        return
    
    print(f"Using API Key: {api_key[:8]}...{api_key[-4:]}")
    
    # Initialize client (testnet=False for mainnet)
    client = Client(api_key=api_key, api_secret=api_secret, testnet=False)
    
    try:
        # Test 1: Get account info (this should work)
        print("\n1. Testing account info...")
        account_info = client.get_account()
        print("✅ Account info retrieved successfully")
        
        # Test 2: Get symbol info for the problematic symbol
        print("\n2. Testing symbol info...")
        symbol = "1000SATSUSDT"
        exchange_info = client.get_exchange_info()
        symbol_info = None
        for s in exchange_info['symbols']:
            if s['symbol'] == symbol:
                symbol_info = s
                break
        
        if symbol_info:
            print(f"✅ Symbol {symbol} found")
            print(f"   Status: {symbol_info['status']}")
            print(f"   Base Asset: {symbol_info['baseAsset']}")
            print(f"   Quote Asset: {symbol_info['quoteAsset']}")
            print(f"   Is Spot Trading Allowed: {symbol_info['isSpotTradingAllowed']}")
            
            # Check filters
            for filter_info in symbol_info['filters']:
                if filter_info['filterType'] == 'LOT_SIZE':
                    print(f"   Min Quantity: {filter_info['minQty']}")
                    print(f"   Max Quantity: {filter_info['maxQty']}")
                    print(f"   Step Size: {filter_info['stepSize']}")
                elif filter_info['filterType'] == 'MIN_NOTIONAL':
                    print(f"   Min Notional: {filter_info['minNotional']}")
                elif filter_info['filterType'] == 'NOTIONAL':
                    print(f"   Min Notional: {filter_info.get('minNotional', 'N/A')}")
                    print(f"   Max Notional: {filter_info.get('maxNotional', 'N/A')}")
                    print(f"   Apply To Market: {filter_info.get('applyToMarket', 'N/A')}")
                elif filter_info['filterType'] == 'MARKET_LOT_SIZE':
                    print(f"   Market Min Quantity: {filter_info['minQty']}")
                    print(f"   Market Max Quantity: {filter_info['maxQty']}")
                    print(f"   Market Step Size: {filter_info['stepSize']}")
                    
            print(f"   All filters: {[f['filterType'] for f in symbol_info['filters']]}")
        else:
            print(f"❌ Symbol {symbol} not found")
            return
            
        # Test 3: Try to get current price
        print("\n3. Testing price info...")
        ticker = client.get_symbol_ticker(symbol=symbol)
        current_price = float(ticker['price'])
        print(f"✅ Current price for {symbol}: {current_price}")
        
        # Test 4: Check account balance for base and quote assets
        print("\n4. Checking account balances...")
        base_asset = symbol_info['baseAsset']  # 1MBABYDOGE
        quote_asset = symbol_info['quoteAsset']  # USDT
        
        base_balance = None
        quote_balance = None
        
        for balance in account_info['balances']:
            if balance['asset'] == base_asset:
                base_balance = balance
            elif balance['asset'] == quote_asset:
                quote_balance = balance
        
        if quote_balance:
            print(f"   {quote_asset} Balance: Free={quote_balance['free']}, Locked={quote_balance['locked']}")
        else:
            print(f"   No {quote_asset} balance found")
            
        if base_balance:
            print(f"   {base_asset} Balance: Free={base_balance['free']}, Locked={base_balance['locked']}")
        
        # Test 5: Attempt a very small test order
        print("\n5. Attempting test order...")
        
        # Calculate minimum quantity based on filters
        min_qty = 0.0
        step_size = 0.0
        min_notional = 0.0
        
        for filter_info in symbol_info['filters']:
            if filter_info['filterType'] == 'LOT_SIZE':
                min_qty = float(filter_info['minQty'])
                step_size = float(filter_info['stepSize'])
            elif filter_info['filterType'] == 'MIN_NOTIONAL':
                min_notional = float(filter_info['minNotional'])
            elif filter_info['filterType'] == 'NOTIONAL':
                if 'minNotional' in filter_info:
                    min_notional = float(filter_info['minNotional'])
        
        print(f"   Min quantity from LOT_SIZE: {min_qty}")
        print(f"   Step size: {step_size}")
        print(f"   Min notional value: {min_notional}")
        
        # Calculate a test quantity that meets minimum requirements
        min_quantity_for_notional = min_notional / current_price if min_notional > 0 else 0
        test_quantity = max(min_qty, min_quantity_for_notional)
        
        print(f"   Min quantity for notional: {min_quantity_for_notional}")
        
        # Round to step size
        if step_size > 0:
            test_quantity = round(test_quantity / step_size) * step_size
            
        # Add extra to ensure we're above the minimum notional (safety margin)
        if min_notional > 0 and current_price > 0:
            while test_quantity * current_price < min_notional * 1.001:  # 0.1% safety margin
                test_quantity += step_size if step_size > 0 else 1
        
        print(f"   Calculated test quantity: {test_quantity}")
        print(f"   Estimated cost: {test_quantity * current_price} USDT")
        
        # IMPORTANT: This will place a real order! Comment out if you don't want to actually trade
        print("   Testing actual order placement:")
        
        try:
            order = client.order_market_buy(
                symbol=symbol,
                quantity=test_quantity
            )
            print(f"✅ Order placed successfully: {order}")
        except BinanceAPIException as api_error:
            print(f"❌ Binance API error during order placement:")
            print(f"   Error code: {api_error.code}")
            print(f"   Error message: {api_error.message}")
            print(f"   Full error: {api_error}")
        except Exception as order_error:
            print(f"❌ Order placement error: {order_error}")
        
    except BinanceAPIException as e:
        print(f"❌ Binance API error: {e}")
        print(f"   Error code: {e.code}")
        print(f"   Error message: {e.message}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_order_placement()
