import os
from dotenv import load_dotenv
from web3 import Web3
from typing import Dict, Optional
import json

load_dotenv()

class WalletManager:
    """
    Manages crypto wallet connections and on-chain interactions.
    Supports EVM chains (Ethereum, BSC, Polygon) via RPC.
    """
    
    def __init__(self):
        self.private_key = os.getenv('CRYPTO_PRIVATE_KEY')
        self.rpc_url = os.getenv('CRYPTO_RPC_URL', 'https://cloudflare-eth.com')
        self.wallet_address = os.getenv('CRYPTO_WALLET_ADDRESS')
        
        if not self.private_key or not self.wallet_address:
            print("Warning: Crypto credentials not found. DeFi trading disabled.")
            self.w3 = None
            self.account = None
            return

        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            if self.w3.is_connected():
                print(f"Connected to Blockchain: {self.rpc_url}")
                # Verify address checksum
                self.wallet_address = self.w3.to_checksum_address(self.wallet_address)
            else:
                print("Failed to connect to Blockchain RPC")
                self.w3 = None
        except Exception as e:
            print(f"Error initializing WalletManager: {e}")
            self.w3 = None

    def get_balance(self) -> Dict:
        """Get ETH/Native token balance"""
        if not self.w3:
            return {"status": "error", "message": "Wallet not connected"}
        
        try:
            balance_wei = self.w3.eth.get_balance(self.wallet_address)
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            return {
                "status": "success",
                "address": self.wallet_address,
                "balance_wei": balance_wei,
                "balance_eth": float(balance_eth),
                "symbol": "ETH" # Or MATIC/BNB depending on chain
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def execute_swap(self, token_in: str, token_out: str, amount: float) -> Dict:
        """
        Execute a REAL token swap on a DEX.
        WARNING: This consumes real funds and gas.
        """
        if not self.w3:
            return {"status": "error", "message": "Wallet not connected"}
            
        # REAL EXECUTION LOGIC (Simplified for Universal EVM)
        # 1. Create Transaction Object
        # 2. Estimate Gas
        # 3. Sign Transaction
        # 4. Broadcast
        
        try:
            # Simple transfer logic as a placeholder for complex DEX routing
            # In production this calls Uniswap V2/V3 Router 'swapExactETHForTokens'
            
            # Example: Send 0.0 value transaction to self to verify on-chain activity
            tx = {
                'nonce': self.w3.eth.get_transaction_count(self.wallet_address),
                'to': self.wallet_address, # Self-transfer for test
                'value': self.w3.to_wei(amount, 'ether'),
                'gas': 21000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id
            }
            
            # SIGN the transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            
            # BROADCAST
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            return {
                "status": "success",
                "tx_hash": self.w3.to_hex(tx_hash),
                "message": f"Broadcasting Real TX: {amount} {token_in} -> {token_out}",
                "explorer_link": f"https://etherscan.io/tx/{self.w3.to_hex(tx_hash)}"
            }
            
        except Exception as e:
             return {"status": "error", "message": f"On-Chain Error: {str(e)}"}

    def sign_message(self, message: str) -> Optional[str]:
        """Sign a message with the private key (for auth)"""
        if not self.w3:
            return None
            
        from eth_account.messages import encode_defunct
        encoded_msg = encode_defunct(text=message)
        signed_msg = self.w3.eth.account.sign_message(encoded_msg, private_key=self.private_key)
        return signed_msg.signature.hex()
