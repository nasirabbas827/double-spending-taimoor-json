"""
app.py - Main Flask Web Application
Blockchain Double-Spending Attack Simulation with Web Interface
"""

import csv
import io , os
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server
import matplotlib.pyplot as plt
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response
from blockchain import Transaction, simulator

app = Flask(__name__)
app.secret_key = 'blockchain_simulation_key_2024'

# Initialize the simulation
simulator.setup_initial_state()

@app.route('/', methods=['GET'])
def index():
    """Main dashboard page"""
    state = simulator.get_network_state()
    honest_chain = state['honest_chain']
    chain_info = honest_chain['chain_info']
    balances = honest_chain['balances']
    chain = honest_chain['chain']
    pending_transactions = honest_chain['pending_transactions']
    accounts = list(balances.keys())
    attack_log = state['attack_log']
    attack_in_progress = state['attack_in_progress']
    is_mining = chain_info['is_mining']

    return render_template(
        'index.html',
        chain_info=chain_info,
        balances=balances,
        chain=chain,
        pending_transactions=pending_transactions,
        accounts=accounts,
        attack_log=attack_log,
        attack_in_progress=attack_in_progress,
        is_mining=is_mining
    )

@app.route('/create_transaction', methods=['POST'])
def create_transaction():
    """Create a new transaction"""
    try:
        sender = request.form['sender'].strip()
        recipient = request.form['recipient'].strip()
        amount = float(request.form['amount'])

        if amount <= 0:
            flash('Amount must be positive', 'error')
            return redirect(url_for('index'))

        transaction = Transaction(sender, recipient, amount)
        print(f"[App Terminal] New Transaction Request: {sender} → {recipient} ({amount} coins)")

        if simulator.honest_chain.add_transaction(transaction, simulator.node_verification_consensus):
            flash(f'Transaction created: {sender} → {recipient} ({amount} coins)', 'success')
        else:
            flash(f'Transaction failed: {sender} has insufficient balance or rejected by nodes', 'error')

    except ValueError:
        flash('Invalid amount format', 'error')
    except Exception as e:
        flash(str(e), 'error')

    return redirect(url_for('index'))

@app.route('/mine', methods=['POST'])
def mine_block():
    """Mine a new block"""
    try:
        if simulator.honest_chain.is_mining:
            flash('Mining already in progress', 'error')
            return redirect(url_for('index'))

        if not simulator.honest_chain.pending_transactions:
            flash('No pending transactions to mine', 'error')
            return redirect(url_for('index'))

        result = simulator.honest_chain.mine_pending_transactions("Miner")

        if result:
            flash(f'Block mined successfully! Block #{result["block"].index}, Time: {result["mining_time"]}s, Txs: {result["transactions_count"]}', 'success')
        else:
            flash('Mining failed', 'error')

    except Exception as e:
        flash(str(e), 'error')

    return redirect(url_for('index'))

@app.route('/attack', methods=['POST'])
def execute_attack():
    """Execute double-spending attack"""
    try:
        victim = request.form['victim'].strip()
        amount = float(request.form['amount'])
        network_delay = float(request.form['network_delay'])
        hash_rate = float(request.form['hash_rate'])

        if amount <= 0:
            flash('Amount must be positive', 'error')
            return redirect(url_for('index'))

        if network_delay < 0:
            flash('Network delay cannot be negative', 'error')
            return redirect(url_for('index'))

        if hash_rate < 1 or hash_rate > 100:
            flash('Hash rate must be between 1 and 100', 'error')
            return redirect(url_for('index'))

        attack_result = simulator.execute_double_spending_attack(victim, amount, network_delay, hash_rate)

        if attack_result['success']:
            flash(f'Attack successful! Victim loss: {attack_result["victim_loss"]}, Attacker gain: {attack_result["attacker_gain"]}', 'success')
        else:
            flash(f'Attack failed: {attack_result["error"]}', 'error')

    except ValueError:
        flash('Invalid input format', 'error')
    except Exception as e:
        flash(str(e), 'error')

    return redirect(url_for('index'))

@app.route('/reset', methods=['POST'])
def reset_simulation():
    """Reset the simulation"""
    try:
        simulator.reset_simulation()
        flash('Simulation reset successfully. CSV log preserved (attack_transaction_log.csv).', 'success')
    except Exception as e:
        flash(str(e), 'error')

    return redirect(url_for('index'))

@app.route('/download_csv')
def download_csv():
    """Download the attack log CSV"""
    try:
        with open(simulator.csv_file, 'r') as f:
            csv_data = f.read()
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=attack_transaction_log.csv"}
        )
    except FileNotFoundError:
        flash('CSV file not found. Run attacks first.', 'error')
        return redirect(url_for('index'))

@app.route('/view_plots')
def view_plots():
    """Generate and display plots using Matplotlib and Pandas"""
    try:
        if not pd.io.common.is_url(simulator.csv_file) and not os.path.exists(simulator.csv_file):
            flash('No attack data yet. Run attacks to generate plots.', 'error')
            return redirect(url_for('index'))
        
        df = pd.read_csv(simulator.csv_file)
        
        if df.empty:
            flash('No data in CSV. Run attacks first.', 'error')
            return redirect(url_for('index'))
        
        # Plot 1: Success Rate Pie
        plt.figure(figsize=(6, 6))
        success_counts = df['Success'].value_counts()
        plt.pie(success_counts, labels=['Success' if label else 'Failure' for label in success_counts.index], autopct='%1.1f%%', colors=['#28a745', '#dc3545'])
        plt.title('Attack Success Rate')
        pie_io = io.BytesIO()
        plt.savefig(pie_io, format='png')
        pie_io.seek(0)
        plt.close()
        
        # Encode to base64 for HTML
        import base64
        pie_img = base64.b64encode(pie_io.getvalue()).decode('utf-8')
        
        # Plot 2: Hash Rate vs Success (Bar)
        plt.figure(figsize=(8, 5))
        df['Success'] = df['Success'].astype(int)  # True=1, False=0
        success_by_hash = df.groupby('Hash Rate')['Success'].mean() * 100
        success_by_hash.plot(kind='bar', color='#667eea')
        plt.title('Success % by Hash Rate')
        plt.ylabel('Success Rate (%)')
        plt.xlabel('Hash Rate (%)')
        bar_io = io.BytesIO()
        plt.savefig(bar_io, format='png')
        bar_io.seek(0)
        plt.close()
        
        bar_img = base64.b64encode(bar_io.getvalue()).decode('utf-8')
        
        # Plot 3: Network Delay vs Success (Scatter)
        plt.figure(figsize=(8, 5))
        plt.scatter(df['Network Delay'], df['Success'], color='#f5576c', alpha=0.7)
        plt.title('Success by Network Delay')
        plt.ylabel('Success (1=Yes, 0=No)')
        plt.xlabel('Network Delay (s)')
        scatter_io = io.BytesIO()
        plt.savefig(scatter_io, format='png')
        scatter_io.seek(0)
        plt.close()
        
        scatter_img = base64.b64encode(scatter_io.getvalue()).decode('utf-8')
        
        # Plot 4: Victim Loss Distribution (Hist)
        plt.figure(figsize=(8, 5))
        df['Victim Loss'].hist(bins=10, color='#00f2fe')
        plt.title('Victim Loss Distribution')
        plt.xlabel('Loss Amount')
        plt.ylabel('Frequency')
        hist_io = io.BytesIO()
        plt.savefig(hist_io, format='png')
        hist_io.seek(0)
        plt.close()
        
        hist_img = base64.b64encode(hist_io.getvalue()).decode('utf-8')
        
        return render_template(
            'plots.html',
            pie_img=pie_img,
            bar_img=bar_img,
            scatter_img=scatter_img,
            hist_img=hist_img
        )
    except Exception as e:
        flash(f'Error generating plots: {str(e)}', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    print(" Starting Blockchain Double-Spending Attack Simulation")
    print(" Dashboard: http://localhost:5000")
    print(" Blockchain initialized with sample data")
    print(" Ready for transactions and attacks!")
    print("-" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)