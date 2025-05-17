from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import os
import logging
import time
import json

# Setup logging
logging.basicConfig(
    filename='faucet_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()
RPC_URL = os.getenv("RPC_URL")
CHAIN_ID = int(os.getenv("CHAIN_ID"))
FAUCET_ADDRESS = os.getenv("FAUCET_ADDRESS")
PRIVATE_KEYS = os.getenv("PRIVATE_KEYS").split(",")

# Faucet contract ABI (update with actual ABI)
FAUCET_ABI = [
    {
        "constant": False,
        "inputs": [],
        "name": "claim",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def connect_to_web3():
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not w3.is_connected():
            raise Exception("Failed to connect to Pharos Testnet")
        logging.info("Connected to Pharos Testnet")
        return w3
    except Exception as e:
        logging.error(f"Web3 connection error: {e}")
        return None

def claim_faucet(w3, faucet_address, wallet_address, private_key):
    try:
        # Initialize faucet contract
        faucet_contract = w3.eth.contract(address=faucet_address, abi=FAUCET_ABI)
        
        # Build transaction
        nonce = w3.eth.get_transaction_count(wallet_address)
        gas_price = w3.eth.gas_price
        tx = faucet_contract.functions.claim().build_transaction({
            'chainId': CHAIN_ID,
            'gas': 200000,
            'gasPrice': gas_price,
            'nonce': nonce,
            'from': wallet_address
        })

        # Sign and send transaction
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        logging.info(f"Transaction sent for {wallet_address}: {tx_hash.hex()}")

        # Wait for receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt.status == 1:
            logging.info(f"Claim successful for {wallet_address}")
            return True
        else:
            logging.warning(f"Claim failed for {wallet_address}")
            return False
    except Exception as e:
        logging.error(f"Error claiming for {wallet_address}: {e}")
        return False

def main():
    # Validate configuration
    if not all([RPC_URL, CHAIN_ID, FAUCET_ADDRESS, PRIVATE_KEYS]):
        logging.error("Missing configuration in .env file")
        return

    # Connect to Web3
    w3 = connect_to_web3()
    if not w3:
        return

    # Enable unaudited HD wallet features
    Account.enable_unaudited_hdwallet_features()

    # Process each wallet
    for i, private_key in enumerate(PRIVATE_KEYS, 1):
        try:
            # Derive wallet address
            account = Account.from_key(private_key.strip())
            wallet_address = account.address
            logging.info(f"Processing wallet {i}: {wallet_address}")

            # Claim faucet
            claim_faucet(w3, FAUCET_ADDRESS, wallet_address, private_key)

            # Delay to avoid rate limits
            time.sleep(5)
        except Exception as e:
            logging.error(f"Error processing wallet {i}: {e}")
            continue

if __name__ == "__main__":
    logging.info("Starting Pharos Faucet Bot")
    main()
    logging.info("Faucet Bot finished")
