import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from dotenv import load_dotenv
from src.utils import settings
from datetime import datetime
import time
import signal
import sys
from src.agent import Agent
from src.backtest.backtester import Backtester
from src.gateway.order_executor import OrderExecutor
from src.utils.constants import Interval


load_dotenv()

def signal_handler(sig, frame):
    print('\n🛑 Stopping trading bot...')
    sys.exit(0)

def run_trading_cycle(portfolio, executor=None):
    """Run a single trading cycle"""
    print(f"\n🔄 Running trading cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    result = Agent.run(
        primary_interval=settings.primary_interval,
        intervals=settings.signals.intervals,
        tickers=settings.signals.tickers,
        end_date=datetime.now(),
        portfolio=portfolio,
        strategies=settings.signals.strategies,
        show_reasoning=settings.show_reasoning,
        show_agent_graph=settings.show_agent_graph,
        model_name=settings.model.name,
        model_provider=settings.model.provider,
        model_base_url=settings.model.base_url,
        enable_execution=settings.execution.enabled
    )
    
    print("Trading Decisions:")
    print(result.get('decisions'))
    
    if settings.execution.enabled and 'execution_results' in result:
        print("\nOrder Execution Results:")
        print(result.get('execution_results'))
    
    return result

def get_interval_seconds(interval_str):
    """Convert interval string to seconds"""
    if not interval_str:
        return None
    
    interval = Interval.from_string(interval_str)
    return interval.to_timedelta().total_seconds()

if __name__ == "__main__":
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    if settings.mode == "backtest":
        backtester = Backtester(
            primary_interval=settings.primary_interval,
            intervals=settings.signals.intervals,
            tickers=settings.signals.tickers,
            start_date=settings.start_date,
            end_date=settings.end_date,
            initial_capital=settings.initial_cash,
            strategies=settings.signals.strategies,
            show_agent_graph=settings.show_agent_graph,
            show_reasoning=settings.show_reasoning,
            model_name=settings.model.name,
            model_provider=settings.model.provider,
            model_base_url=settings.model.base_url,
        )
        print("Starting backtest...")
        performance_metrics = backtester.run_backtest()
        performance_df = backtester.analyze_performance()

    else:
        portfolio = {
            "cash": settings.initial_cash,  # Initial cash amount
            "margin_requirement": settings.margin_requirement,  # Initial margin requirement
            "margin_used": 0.0,  # total margin usage across all short positions
            "positions": {
                ticker: {
                    "long": 0.0,  # Number of shares held long
                    "short": 0.0,  # Number of shares held short
                    "long_cost_basis": 0.0,  # Average cost basis for long positions
                    "short_cost_basis": 0.0,  # Average price at which shares were sold short
                    "short_margin_used": 0.0,  # Dollars of margin used for this ticker's short
                }
                for ticker in settings.signals.tickers
            },
            "realized_gains": {
                ticker: {
                    "long": 0.0,  # Realized gains from long positions
                    "short": 0.0,  # Realized gains from short positions
                }
                for ticker in settings.signals.tickers
            },
        }

        # Check if order execution is enabled
        executor = None
        if settings.execution.enabled:
            print("⚠️  WARNING: Live trading is enabled!")
            print(f"   Testnet: {settings.execution.testnet}")
            print(f"   Max order size: ${settings.execution.max_order_size}")
            print(f"   Min confidence: {settings.execution.min_confidence}%")
            
            # Verify API credentials
            try:
                executor = OrderExecutor(testnet=settings.execution.testnet)
                account_info = executor.get_account_info()
                print(f"✅ Connected to Binance account")
                
                # Display balances for spot accounts
                if account_info and 'balances' in account_info:
                    balances = [b for b in account_info['balances'] if float(b['free']) > 0 or float(b['locked']) > 0]
                    if balances:
                        print("   Balances:")
                        for balance in balances:
                            print(f"     - {balance['asset']}: Free={balance['free']}, Locked={balance['locked']}")
                    else:
                        print("   No asset balances found.")
                else:
                    print("   Could not retrieve account balance.")

                # Verify API key loading
                api_key_to_check = os.getenv("BINANCE_API_KEY")
                if api_key_to_check:
                    print(f"   Using API Key: {api_key_to_check[:5]}...{api_key_to_check[-4:]}")
                else:
                    print("   API Key not found in environment variables!")
                    
            except Exception as e:
                print(f"❌ Failed to connect to Binance: {e}")
                exit(1)
        
        # Check if interval-based execution is enabled
        execution_interval_seconds = get_interval_seconds(settings.execution.execution_interval)
        
        if execution_interval_seconds:
            print(f"🔄 Starting interval-based trading with {settings.execution.execution_interval} intervals")
            print("Press Ctrl+C to stop the bot")
            
            try:
                while True:
                    run_trading_cycle(portfolio, executor)
                    
                    # Wait for the next interval
                    print(f"⏰ Waiting {execution_interval_seconds} seconds until next cycle...")
                    time.sleep(execution_interval_seconds)
                    
            except KeyboardInterrupt:
                print('\n🛑 Trading bot stopped by user')
        else:
            # Single execution mode (original behavior)
            print("🚀 Running single trading cycle...")
            run_trading_cycle(portfolio, executor)
