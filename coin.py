import hashlib
import json
from datetime import datetime
from uuid import uuid4
import requests
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
# from coin import Blockchain



class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.pending_transactions = []
        self.difficulty = 2
        self.miner_rewards = 50
        self.block_size = 10
        self.nodes = set()

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def resolve_conflicts(self):
        neighbors = self.nodes
        new_chain = None
        max_length = len(self.chain)

        for node in neighbors:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.is_valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True

        return False

    def mine_pending_transactions(self, miner_address):
        if len(self.pending_transactions) <= 1:
            print("Not enough transactions to mine! (Must be > 1)")
            return False

        for i in range(0, len(self.pending_transactions), self.block_size):
            end = min(i + self.block_size, len(self.pending_transactions))
            transaction_slice = self.pending_transactions[i:end]

            new_block = Block(transaction_slice, datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), len(self.chain))
            new_block.prev_hash = self.chain[-1].hash
            new_block.mine_block(self.difficulty)
            self.chain.append(new_block)

        self.pending_transactions = [Transaction("Miner Rewards", miner_address, self.miner_rewards)]
        return True

    def add_transaction(self, sender, recipient, amount, sender_private_key):
        transaction = Transaction(sender, recipient, amount)
        transaction.sign_transaction(sender_private_key)

        if not transaction.is_valid_transaction():
            print("Invalid transaction!")
            return False

        self.pending_transactions.append(transaction)
        return True

    def get_balance(self, person):
        balance = 0
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.recipient == person:
                    balance += transaction.amount
                elif transaction.sender == person:
                    balance -= transaction.amount
        return balance

    def create_genesis_block(self):
        return Block([], datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), "0")

    def is_valid_chain(self, chain):
        for i in range(1, len(chain)):
            block = chain[i]
            prev_block = chain[i - 1]

            if block.hash != block.calculate_hash():
                return False

            if block.prev_hash != prev_block.hash:
                return False

            if not block.has_valid_transactions():
                return False

        return True


class Block:
    def __init__(self, transactions, timestamp, prev_hash):
        self.transactions = transactions
        self.timestamp = timestamp
        self.prev_hash = prev_hash
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({"prev_hash": self.prev_hash, "transactions": self.transactions, "timestamp": self.timestamp, "nonce": self.nonce}, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def mine_block(self, difficulty):
        while self.hash[:difficulty] != "0" * difficulty:
            self.nonce += 1
            self.hash = self.calculate_hash()

    def has_valid_transactions(self):
        for transaction in self.transactions:
            if not transaction.is_valid_transaction():
                return False
        return True


class Transaction:
    def __init__(self, sender, recipient, amount):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.timestamp = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        self.signature = None

    def calculate_hash(self):
        transaction_string = json.dumps({"sender": self.sender, "recipient": self.recipient, "amount": self.amount, "timestamp": self.timestamp}).encode()
        return hashlib.sha256(transaction_string).hexdigest()

    def sign_transaction(self, sender_private_key):
        if self.sender == "Miner Rewards":
            return True  # No need to sign miner rewards

        signer = pkcs1_15.new(sender_private_key)
        hash_obj = SHA256.new(self.calculate_hash().encode())
        self.signature = signer.sign(hash_obj)

    def is_valid_transaction(self):
        if self.sender == "Miner Rewards":
            return True

        if self.signature is None:
            return False

        public_key = RSA.import_key(self.sender.encode())
        verifier = pkcs1_15.new(public_key)
        hash_obj = SHA256.new(self.calculate_hash().encode())

        try:
            verifier.verify(hash_obj, self.signature)
            return True
        except (ValueError, TypeError):
            return False
