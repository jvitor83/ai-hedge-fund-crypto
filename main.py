import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from dotenv import load_dotenv
from src.utils import settings
from datetime import datetime
from src.agent import Agent
from src.backtest.backtester import Backtester
from src.gateway.order_executor import OrderExecutor


load_dotenv()

if __name__ == "__main__":

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
                print(f"   Balance: {account_info.get('totalWalletBalance', 'N/A')}")
            except Exception as e:
                print(f"❌ Failed to connect to Binance: {e}")
                exit(1)
        
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
            enable_execution=settings.execution.enabled  # Pass execution flag
        )
        
        print("Trading Decisions:")
        print(result.get('decisions'))
        
        if settings.execution.enabled and 'execution_results' in result:
            print("\nOrder Execution Results:")
            print(result.get('execution_results'))
