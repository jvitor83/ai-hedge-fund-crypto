import os
import json
import logging
from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage
from .base_node import BaseNode, AgentState
from src.gateway.order_executor import OrderExecutor

logger = logging.getLogger(__name__)

class OrderExecutionNode(BaseNode):
    def __init__(self, testnet: bool = True, enable_execution: bool = False):
        """
        Initialize the order execution node
        
        Args:
            testnet: Whether to use Binance testnet
            enable_execution: Whether to actually execute orders (safety flag)
        """
        self.testnet = testnet
        self.enable_execution = enable_execution
        
        # Initialize order executor only if execution is enabled
        self.order_executor = None
        if self.enable_execution:
            try:
                self.order_executor = OrderExecutor(testnet=self.testnet)
                logger.info("Order executor initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize order executor: {e}")
                self.enable_execution = False
    
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """Execute orders based on portfolio management decisions"""
        
        data = state.get('data', {})
        data['name'] = "OrderExecutionNode"
        
        # Get the decisions from the previous node
        messages = state.get('messages', [])
        if not messages:
            return {
                "messages": [HumanMessage(content="No decisions to execute")],
                "data": data
            }
        
        # Parse the decisions from the last message
        try:
            last_message = messages[-1]
            if hasattr(last_message, 'content'):
                decisions = json.loads(last_message.content)
            else:
                decisions = {}
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"Failed to parse decisions: {e}")
            return {
                "messages": [HumanMessage(content="Failed to parse trading decisions")],
                "data": data
            }
        
        # Execute orders for each ticker
        execution_results = {}
        
        if not self.enable_execution:
            # Simulation mode - just log what would be executed
            for ticker, decision in decisions.items():
                action = decision.get("action", "hold")
                quantity = decision.get("quantity", 0.0)
                
                if action != "hold" and quantity > 0:
                    logger.info(f"SIMULATION: Would execute {action} {quantity} {ticker}")
                    execution_results[ticker] = {
                        "action": action,
                        "quantity": quantity,
                        "executed": False,
                        "reason": "Simulation mode - no actual orders placed"
                    }
        else:
            # Live execution mode
            for ticker, decision in decisions.items():
                try:
                    result = self.order_executor.execute_decision(ticker, decision)
                    execution_results[ticker] = result
                    
                    if result.get("executed"):
                        logger.info(f"Order executed successfully: {ticker} - {result}")
                    else:
                        logger.warning(f"Order not executed: {ticker} - {result}")
                        
                except Exception as e:
                    logger.error(f"Error executing order for {ticker}: {e}")
                    execution_results[ticker] = {
                        "action": decision.get("action"),
                        "quantity": decision.get("quantity"),
                        "executed": False,
                        "error": str(e)
                    }
        
        # Create execution summary message
        execution_summary = {
            "mode": "live" if self.enable_execution else "simulation",
            "results": execution_results,
            "total_orders": len([r for r in execution_results.values() if r.get("executed")]),
            "total_errors": len([r for r in execution_results.values() if r.get("error")])
        }
        
        message = HumanMessage(
            content=json.dumps(execution_summary),
            name="order_execution"
        )
        
        # Add execution results to state
        data["execution_results"] = execution_results
        
        return {
            "messages": [message],
            "data": data
        } 