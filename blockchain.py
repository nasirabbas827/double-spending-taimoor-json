"""
blockchain.py - Core Blockchain Implementation
Contains all blockchain logic, transaction processing, and attack simulation
"""

import hashlib
import json
import time
import random
from datetime import datetime
import uuid
import threading
import csv
import os

class Transaction:
    """Represents a blockchain transaction"""
    
    def __init__(self, sender, recipient, amount, transaction_id=None):
        self.transaction_id = transaction_id or str(uuid.uuid4())[:8]
        self.sender = sender
        self.recipient = recipient
        self.amount = float(amount)
        self.timestamp = time.time()
        
    def to_dict(self):
        return {
            'transaction_id': self.transaction_id,
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'date': datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def calculate_hash(self):
        """Calculate transaction hash"""
        tx_string = json.dumps({
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'timestamp': self.timestamp
        }, sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()

class Block:
    """Represents a blockchain block"""
    
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        """Calculate block hash"""
        block_string = json.dumps({
            'index': self.index,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty, hash_rate=1.0):
        """Mine the block using Proof of Work with hash rate scaling"""
        target = "0" * difficulty
        start_time = time.time()
        
        # Simulate hash rate by scaling the mining effort
        attempts_per_second = 1000 * hash_rate
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
            if hash_rate < 1.0:
                time.sleep(0.001 / max(hash_rate, 0.1))
        
        mining_time = time.time() - start_time
        return mining_time
    
    def to_dict(self):
        return {
            'index': self.index,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'timestamp': self.timestamp,
            'date': datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash,
            'hash_short': self.hash[:16] + '...'
        }

class Blockchain:
    """Main blockchain class with attack simulation capabilities"""
    
    def __init__(self, node_name="main"):
        self.node_name = node_name
        self.chain = [self.create_genesis_block()]
        self.difficulty = 1
        self.pending_transactions = []
        self.mining_reward = 10
        self.balances = {
            'Alice': 100,
            'Bob': 100,
            'Charlie': 100,
            'Attacker': 100,
            'Victim': 50,
            'Merchant': 0
        }
        self.is_mining = False
        
    def create_genesis_block(self):
        genesis_transactions = []
        return Block(0, genesis_transactions, time.time(), "0")
    
    def get_latest_block(self):
        return self.chain[-1]
    
    def add_transaction(self, transaction, verify_nodes=None):
        if self.validate_transaction(transaction):
            if verify_nodes and not verify_nodes(transaction):
                return False
            self.pending_transactions.append(transaction)
            print(f"[Node {self.node_name}] Transaction {transaction.transaction_id} added to pending: {transaction.sender} → {transaction.recipient} ({transaction.amount})")
            return True
        return False
    
    def validate_transaction(self, transaction):
        if transaction.sender == "system":
            return True
        if transaction.sender not in self.balances:
            self.balances[transaction.sender] = 0
        return self.balances[transaction.sender] >= transaction.amount
    
    def mine_pending_transactions(self, mining_reward_address="Miner", hash_rate=1.0):
        if self.is_mining:
            return None
        if not self.pending_transactions:
            return None
        self.is_mining = True
        try:
            reward_transaction = Transaction("system", mining_reward_address, self.mining_reward)
            transactions_to_mine = self.pending_transactions.copy()
            transactions_to_mine.append(reward_transaction)
            block = Block(len(self.chain), transactions_to_mine, time.time(), self.get_latest_block().hash)
            mining_time = block.mine_block(self.difficulty, hash_rate)
            self.chain.append(block)
            self.pending_transactions = []
            self.update_balances()
            print(f"[Node {self.node_name}] Mined Block #{block.index} | Time: {mining_time:.2f}s | Txs: {len(transactions_to_mine)} | Hash Rate Factor: {hash_rate}")
            return {
                'block': block,
                'mining_time': round(mining_time, 2),
                'transactions_count': len(transactions_to_mine)
            }
        except Exception as e:
            print(f"Mining error on {self.node_name}: {e}")
            return None
        finally:
            self.is_mining = False
    
    def update_balances(self):
        self.balances = {'Alice': 100, 'Bob': 100, 'Charlie': 100, 'Attacker': 100, 'Victim': 50, 'Merchant': 0}
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.sender != "system":
                    if transaction.sender not in self.balances:
                        self.balances[transaction.sender] = 0
                    self.balances[transaction.sender] -= transaction.amount
                if transaction.recipient not in self.balances:
                    self.balances[transaction.recipient] = 0
                self.balances[transaction.recipient] += transaction.amount
    
    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            if current.hash != current.calculate_hash() or current.previous_hash != previous.hash:
                return False
        return True
    
    def get_chain_info(self):
        return {
            'node_name': self.node_name,
            'chain_length': len(self.chain),
            'pending_transactions': len(self.pending_transactions),
            'difficulty': self.difficulty,
            'is_valid': self.is_chain_valid(),
            'is_mining': self.is_mining,
            'total_transactions': sum(len(b.transactions) for b in self.chain),
            'balances': self.balances.copy()
        }
    
    def to_dict(self):
        return {
            'node_name': self.node_name,
            'chain': [b.to_dict() for b in self.chain],
            'pending_transactions': [tx.to_dict() for tx in self.pending_transactions],
            'balances': self.balances,
            'chain_info': self.get_chain_info()
        }

    def get_chain_summary(self):
        """Get a JSON string summary of the chain for CSV (blocks with TX IDs and hashes)"""
        summary = []
        for block in self.chain:
            tx_ids = [tx.transaction_id for tx in block.transactions] if block.transactions else []
            summary.append({
                'index': block.index,
                'hash': block.hash,
                'previous_hash': block.previous_hash,
                'tx_count': len(block.transactions),
                'tx_ids': tx_ids
            })
        return json.dumps(summary)

class AttackSimulator:
    """Simulates double-spending attacks"""
    
    def __init__(self):
        self.honest_chain = Blockchain("Honest Network")
        self.nodes = [Blockchain(f"Node{i}") for i in range(1, 7)]
        self.attacker_chain = None
        self.attack_in_progress = False
        self.attack_log = []
        self.csv_file = 'attack_transaction_log.csv'
        self.init_csv()
        
    def init_csv(self):
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Attack Timestamp', 'Legit TX ID', 'Legit Sender', 'Legit Recipient', 'Amount',
                    'Double TX ID', 'Double Sender', 'Double Recipient',
                    'Network Delay', 'Hash Rate', 'Success', 'Victim Loss', 'Attacker Gain', 'Node Verifications',
                    'Honest Chain Before Reorg', 'Attacker Private Chain'
                ])
            print(f"[CSV] Created {self.csv_file} with chain summaries")

    def node_verification_consensus(self, transaction):
        """Simulate verification by all 6 nodes - always accepts sig, majority consensus"""
        verifications = []
        for node in self.nodes:
            time.sleep(random.uniform(0.1, 0.5))
            valid_balance = node.validate_transaction(transaction)
            mock_sig_check = True  # Always pass for demo
            is_valid = valid_balance and mock_sig_check
            status = "Accepted" if is_valid else "Rejected"
            print(f"[Verification on {node.node_name}] TX {transaction.transaction_id} ({transaction.sender}→{transaction.recipient}): {status}")
            verifications.append(is_valid)
        
        consensus_count = sum(verifications)
        consensus = consensus_count >= 4  # Majority
        print(f"[Consensus] Transaction {transaction.transaction_id} verified by {consensus_count}/6 nodes: {'YES' if consensus else 'NO'}")
        return consensus
    
    def propagate_to_nodes(self):
        for node in self.nodes:
            node.chain = [block for block in self.honest_chain.chain]
            node.balances = self.honest_chain.balances.copy()
            node.pending_transactions = self.honest_chain.pending_transactions.copy()
        print("[Propagation] Honest chain state synced to all 6 nodes.")

    def setup_initial_state(self):
        """Setup initial blockchain state - no initial TXs"""
        initial_txs = []  # Removed
        
        for tx in initial_txs:
            if self.node_verification_consensus(tx):
                self.honest_chain.add_transaction(tx)
        
        self.propagate_to_nodes()
        return self.get_network_state()
    
    def execute_double_spending_attack(self, victim, amount, network_delay=0, hash_rate=100):
        if self.attack_in_progress:
            return {"success": False, "error": "Attack already in progress"}
        
        self.attack_in_progress = True
        self.attack_log = []
        attack_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Capture honest chain summary before any changes
        honest_chain_before = self.honest_chain.get_chain_summary()
        
        try:
            self.log_event(" ATTACK INITIATED")
            print(f"[ATTACK START] Double-spending attack on {victim} for {amount} coins at {attack_start_time}")
            
            legitimate_tx = Transaction("Attacker", victim, amount)
            double_spend_tx = Transaction("Attacker", "Attacker", amount)
            
            print(f"[Terminal Log] Legitimate TX Created: ID={legitimate_tx.transaction_id} | {legitimate_tx.sender} → {legitimate_tx.recipient} | Amount={amount} | Time={legitimate_tx.to_dict()['date']}")
            print(f"[Terminal Log] Double-Spend TX Created: ID={double_spend_tx.transaction_id} | {double_spend_tx.sender} → {double_spend_tx.recipient} | Amount={amount} | Time={double_spend_tx.to_dict()['date']}")
            
            if not self.honest_chain.validate_transaction(legitimate_tx):
                error_msg = "Insufficient balance for attack"
                self.log_to_csv(attack_start_time, legitimate_tx, double_spend_tx, network_delay, hash_rate, False, honest_chain_before, None, error=error_msg)
                return {"success": False, "error": error_msg}
            
            if not self.honest_chain.add_transaction(legitimate_tx, self.node_verification_consensus):
                error_msg = "Legitimate TX rejected by network nodes"
                self.log_to_csv(attack_start_time, legitimate_tx, double_spend_tx, network_delay, hash_rate, False, honest_chain_before, None, error=error_msg)
                return {"success": False, "error": error_msg}
            
            self.log_event(f"Legitimate TX {legitimate_tx.transaction_id} added to honest pending")

            self.log_event("Creating private attack chain...")
            self.attacker_chain = Blockchain("Attacker Chain")
            self.attacker_chain.chain = [block for block in self.honest_chain.chain]
            self.attacker_chain.balances = self.honest_chain.balances.copy()
            self.attacker_chain.pending_transactions.append(double_spend_tx)
            self.log_event(f"Double-spend TX {double_spend_tx.transaction_id} added secretly to private chain")
            print(f"[Terminal Log] Double-spend TX added to private chain secretly (no public verification)")

            self.log_event("Honest network mining block (includes legitimate TX)...")
            honest_result = self.honest_chain.mine_pending_transactions("Bob")
            if honest_result:
                print(f"[Terminal Log] Honest chain mined Block #{honest_result['block'].index} confirming legitimate TX")
            
            self.propagate_to_nodes()

            if network_delay > 0:
                self.log_event(f"Simulating network delay of {network_delay} seconds...")
                time.sleep(network_delay)

            self.log_event(f"Attacker secretly mining private chain with {hash_rate}% hash power...")
            hash_rate_factor = hash_rate / 100.0
            print(f"[Terminal Log] Attacker starting secret mining on private chain with hash_rate_factor={hash_rate_factor}")
            
            attack_result1 = self.attacker_chain.mine_pending_transactions("Attacker", hash_rate=hash_rate_factor)
            if attack_result1:
                print(f"[Terminal Log] Attacker secretly mined Block #{attack_result1['block'].index} (includes double-spend TX)")

            extra_blocks = 2
            for i in range(extra_blocks):
                self.attacker_chain.pending_transactions.append(Transaction("system", "Attacker", 0))
                extra_result = self.attacker_chain.mine_pending_transactions("Attacker", hash_rate=hash_rate_factor)
                if extra_result:
                    print(f"[Terminal Log] Attacker secretly mined extra empty Block #{extra_result['block'].index} for chain length")
                    self.log_event(f"Secret extra block mined (#{extra_result['block'].index}) to extend private chain")

            # Capture attacker chain summary after mining
            attacker_chain_summary = self.attacker_chain.get_chain_summary()

            # Evaluate success - deterministic (removed random)
            chain_longer = len(self.attacker_chain.chain) > len(self.honest_chain.chain)
            sufficient_power = hash_rate >= 60 and network_delay <= 3
            success_probability = hash_rate_factor * (1.0 - min(network_delay / 5.0, 0.6))
            
            if not chain_longer or not sufficient_power:
                error_msg = "Insufficient hash rate, excessive delay, or failed to overtake chain"
                self.log_event(f" Attack failed: {error_msg} (Prob would have been {success_probability:.2f})")
                self.log_to_csv(attack_start_time, legitimate_tx, double_spend_tx, network_delay, hash_rate, False, honest_chain_before, attacker_chain_summary, error=error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "attack_log": self.attack_log
                }
            
            self.log_event(f"Success probability was {success_probability:.2f} - thresholds met!")
            self.log_event("Broadcasting longer private chain to network...")
            self.log_event("Network accepts longer chain - REORG!")
            print(f"[Terminal Log] Chain reorg: Honest length={len(self.honest_chain.chain)} → Attacker length={len(self.attacker_chain.chain)}")
            
            original_honest = self.honest_chain
            self.honest_chain = self.attacker_chain
            self.propagate_to_nodes()
            self.honest_chain.update_balances()
            
            self.log_event(" DOUBLE-SPENDING ATTACK SUCCESSFUL!")
            self.log_event(f"Victim's transaction reversed - Attacker keeps {amount} coins!")
            
            self.log_to_csv(attack_start_time, legitimate_tx, double_spend_tx, network_delay, hash_rate, True, honest_chain_before, attacker_chain_summary, amount, amount)
            
            return {
                "success": True,
                "legitimate_tx": legitimate_tx.to_dict(),
                "double_spend_tx": double_spend_tx.to_dict(),
                "honest_chain_length": len(original_honest.chain),
                "attack_chain_length": len(self.attacker_chain.chain),
                "attack_log": self.attack_log,
                "victim_loss": amount,
                "attacker_gain": amount
            }
            
        except Exception as e:
            error_msg = str(e)
            self.log_event(f" Attack failed: {error_msg}")
            print(f"[Terminal Error] Attack exception: {error_msg}")
            attacker_chain_summary = self.attacker_chain.get_chain_summary() if self.attacker_chain else None
            self.log_to_csv(attack_start_time, legitimate_tx if 'legitimate_tx' in locals() else None, 
                           double_spend_tx if 'double_spend_tx' in locals() else None, 
                           network_delay, hash_rate, False, honest_chain_before, attacker_chain_summary, error=error_msg)
            return {"success": False, "error": error_msg, "attack_log": self.attack_log}
        finally:
            self.attack_in_progress = False
    
    def log_to_csv(self, attack_time, legit_tx, double_tx, delay, hash_rate, success, honest_chain_before, attacker_chain_summary, victim_loss=0, attacker_gain=0, error=None):
        legit_id = legit_tx.transaction_id if legit_tx else "N/A"
        legit_sender = legit_tx.sender if legit_tx else "N/A"
        legit_recipient = legit_tx.recipient if legit_tx else "N/A"
        legit_amount = legit_tx.amount if legit_tx else 0
        double_id = double_tx.transaction_id if double_tx else "N/A"
        double_sender = double_tx.sender if double_tx else "N/A"
        double_recipient = double_tx.recipient if double_tx else "N/A"
        verif_status = "All Accepted" if success else f"Failed ({error or 'N/A'})"
        honest_summary = honest_chain_before or "N/A"
        attacker_summary = attacker_chain_summary or "N/A"
        
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([attack_time, legit_id, legit_sender, legit_recipient, legit_amount,
                             double_id, double_sender, double_recipient, delay, hash_rate, success, victim_loss, attacker_gain, verif_status,
                             honest_summary, attacker_summary])
        print(f"[CSV Log] Attack details appended to {self.csv_file} (includes chain summaries)")

    def log_event(self, message):
        event = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'message': message
        }
        self.attack_log.append(event)
    
    def get_network_state(self):
        self.propagate_to_nodes()
        return {
            'honest_chain': self.honest_chain.to_dict(),
            'attack_in_progress': self.attack_in_progress,
            'attack_log': self.attack_log,
            'has_attack_chain': self.attacker_chain is not None,
            'attack_chain': self.attacker_chain.to_dict() if self.attacker_chain else None
        }
    
    def reset_simulation(self):
        self.honest_chain = Blockchain("Honest Network")
        self.nodes = [Blockchain(f"Node{i}") for i in range(1, 7)]
        self.attacker_chain = None
        self.attack_in_progress = False
        self.attack_log = []
        print("[Reset] Simulation reset. CSV log preserved.")
        return self.setup_initial_state()

simulator = AttackSimulator()