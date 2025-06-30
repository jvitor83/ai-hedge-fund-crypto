#!/usr/bin/env python3
"""
Test the OrderExecutor class directly
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.gateway.order_executor import OrderExecutor

# Set up logging
logging.basicConfig(level=logging.INFO)

load_dotenv()

def test_order_executor():
    """Test the OrderExecutor class directly"""
    
    try:
        # Initialize OrderExecutor (same as main bot)
        executor = OrderExecutor(testnet=False)
        
        # Test account info
        print("1. Testing account info...")
        account_info = executor.get_account_info()
        print("✅ Account info retrieved successfully")
        
        # Test decision execution for multiple symbols
        print("\n2. Testing decision execution for multiple symbols...")
        
        test_symbols = ["1000SATSUSDT", "GALAUSDT", "1MBABYDOGEUSDT", "VETUSDT"]
        
        for symbol in test_symbols:
            print(f"\n--- Testing {symbol} ---")
            
            # Get symbol info first
            try:
                exchange_info = executor.client._client.get_exchange_info()
                symbol_info = None
                for s in exchange_info['symbols']:
                    if s['symbol'] == symbol:
                        symbol_info = s
                        break
                
                if not symbol_info:
                    print(f"❌ Symbol {symbol} not found")
                    continue
                
                # Get current price
                ticker_price = executor.client._client.get_symbol_ticker(symbol=symbol)
                current_price = float(ticker_price['price'])
                
                # Get minimum notional
                min_notional = 1.0  # default
                for filter_info in symbol_info['filters']:
                    if filter_info['filterType'] == 'NOTIONAL':
                        min_notional = float(filter_info.get('minNotional', 1.0))
                        break
                
                # Calculate minimum quantity
                min_quantity = min_notional / current_price
                test_quantity = max(1.0, min_quantity)
                
                print(f"   Current price: {current_price}")
                print(f"   Min notional: {min_notional}")
                print(f"   Test quantity: {test_quantity}")
                
                test_decision = {
                    "action": "buy",
                    "quantity": test_quantity,
                    "confidence": 75.0,
                    "reasoning": "Test order"
                }
                
                result = executor.execute_decision(symbol, test_decision)
                if result.get("executed"):
                    print(f"   ✅ Success: {result}")
                else:
                    print(f"   ❌ Failed: {result}")
                    
            except Exception as e:
                print(f"   ❌ Error for {symbol}: {e}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_order_executor()
