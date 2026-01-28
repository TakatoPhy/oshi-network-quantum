#!/usr/bin/env python3
"""Compare strategies across multiple network structures"""

import numpy as np
import networkx as nx
from itertools import combinations
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

os.makedirs('images', exist_ok=True)
np.random.seed(42)

def simulate_spread(G, initial_seeds, max_rounds=20):
    """Simulate spread on a networkx graph"""
    nodes = list(G.nodes())
    converted = set(initial_seeds)
    converted.add("You")  # You is always a fan

    for round_num in range(max_rounds):
        new_converts = set()
        for node in nodes:
            if node in converted:
                continue
            neighbors = list(G.neighbors(node))
            if not neighbors:
                continue
            converted_neighbors = sum(1 for n in neighbors if n in converted)
            if converted_neighbors >= len(neighbors) / 2:
                new_converts.add(node)

        if not new_converts:
            break
        converted = converted | new_converts

    return len(converted), round_num + 1 if new_converts else round_num

def find_independent_set_greedy(G, size=3, exclude=None):
    """Find an independent set of given size using greedy algorithm"""
    if exclude is None:
        exclude = {"You"}
    else:
        exclude = set(exclude) | {"You"}

    candidates = [n for n in G.nodes() if n not in exclude]
    selected = []

    # Sort by degree (prefer lower degree nodes for independent set)
    candidates.sort(key=lambda x: G.degree(x))

    for node in candidates:
        # Check if this node is independent from already selected
        is_independent = all(not G.has_edge(node, s) for s in selected)
        if is_independent:
            selected.append(node)
            if len(selected) >= size:
                break

    return selected

def get_direct_friends(G, size=3):
    """Get direct friends of 'You'"""
    neighbors = list(G.neighbors("You"))
    return neighbors[:size]

def generate_hub_spoke_network(n_friends=9, n_direct=3, cross_links=5):
    """Generate hub-and-spoke network with cross links"""
    G = nx.Graph()
    nodes = ["You"] + [chr(65+i) for i in range(n_friends)]  # You, A, B, C, ...
    G.add_nodes_from(nodes)

    # Connect You to direct friends
    direct_friends = nodes[1:n_direct+1]
    for f in direct_friends:
        G.add_edge("You", f)

    # Add outer ring connections
    outer = nodes[n_direct+1:]
    for i, f in enumerate(direct_friends):
        # Each direct friend connects to 1-2 outer friends
        for j in range(min(2, len(outer))):
            idx = (i * 2 + j) % len(outer)
            G.add_edge(f, outer[idx])

    # Add random cross links
    for _ in range(cross_links):
        n1, n2 = np.random.choice(nodes[1:], 2, replace=False)
        if not G.has_edge(n1, n2):
            G.add_edge(n1, n2)

    return G

def generate_random_network(n_friends=9, edge_prob=0.3):
    """Generate random Erdos-Renyi network with You as hub"""
    G = nx.Graph()
    nodes = ["You"] + [chr(65+i) for i in range(n_friends)]
    G.add_nodes_from(nodes)

    # Connect You to some friends
    for node in nodes[1:]:
        if np.random.random() < 0.4:  # 40% chance to be direct friend
            G.add_edge("You", node)

    # Ensure You has at least 3 friends
    if G.degree("You") < 3:
        non_friends = [n for n in nodes[1:] if not G.has_edge("You", n)]
        for f in np.random.choice(non_friends, min(3 - G.degree("You"), len(non_friends)), replace=False):
            G.add_edge("You", f)

    # Add random edges between others
    for n1, n2 in combinations(nodes[1:], 2):
        if np.random.random() < edge_prob:
            G.add_edge(n1, n2)

    return G

def generate_clustered_network(n_friends=9, n_clusters=3):
    """Generate network with clear clusters"""
    G = nx.Graph()
    nodes = ["You"] + [chr(65+i) for i in range(n_friends)]
    G.add_nodes_from(nodes)

    # Divide into clusters
    cluster_size = n_friends // n_clusters
    clusters = []
    for i in range(n_clusters):
        start = 1 + i * cluster_size
        end = start + cluster_size if i < n_clusters - 1 else n_friends + 1
        clusters.append(nodes[start:end])

    # Connect You to one node in each cluster
    for cluster in clusters:
        G.add_edge("You", cluster[0])

    # Dense connections within clusters
    for cluster in clusters:
        for n1, n2 in combinations(cluster, 2):
            if np.random.random() < 0.7:
                G.add_edge(n1, n2)

    # Sparse connections between clusters
    for i, c1 in enumerate(clusters):
        for c2 in clusters[i+1:]:
            if np.random.random() < 0.3:
                n1 = np.random.choice(c1)
                n2 = np.random.choice(c2)
                G.add_edge(n1, n2)

    return G

def evaluate_strategies(G, n_trials=10):
    """Evaluate direct vs independent set strategies"""
    direct_friends = get_direct_friends(G, 3)
    independent_set = find_independent_set_greedy(G, 3)

    results = {
        'direct': {'converted': [], 'rounds': []},
        'independent': {'converted': [], 'rounds': []},
    }

    # Test direct friends strategy
    if len(direct_friends) >= 3:
        converted, rounds = simulate_spread(G, direct_friends[:3])
        results['direct']['converted'].append(converted)
        results['direct']['rounds'].append(rounds)

    # Test independent set strategy
    if len(independent_set) >= 3:
        converted, rounds = simulate_spread(G, independent_set[:3])
        results['independent']['converted'].append(converted)
        results['independent']['rounds'].append(rounds)

    return results

# Main comparison
print("=" * 60)
print("Network Structure Comparison")
print("=" * 60)

n_networks = 50
all_results = {
    'hub_spoke': [],
    'random': [],
    'clustered': [],
}

network_generators = {
    'hub_spoke': lambda: generate_hub_spoke_network(9, 3, np.random.randint(3, 8)),
    'random': lambda: generate_random_network(9, np.random.uniform(0.2, 0.5)),
    'clustered': lambda: generate_clustered_network(9, 3),
}

for net_type, generator in network_generators.items():
    print(f"\n{net_type.upper()} Networks ({n_networks} samples):")

    direct_wins = 0
    independent_wins = 0
    ties = 0

    direct_converted_total = []
    independent_converted_total = []
    direct_rounds_total = []
    independent_rounds_total = []

    for i in range(n_networks):
        G = generator()

        # Make sure graph is connected to You
        if G.degree("You") == 0:
            continue

        results = evaluate_strategies(G)

        if results['direct']['converted'] and results['independent']['converted']:
            d_conv = results['direct']['converted'][0]
            i_conv = results['independent']['converted'][0]
            d_rounds = results['direct']['rounds'][0]
            i_rounds = results['independent']['rounds'][0]

            direct_converted_total.append(d_conv)
            independent_converted_total.append(i_conv)
            direct_rounds_total.append(d_rounds)
            independent_rounds_total.append(i_rounds)

            # Compare: prefer more converted, then fewer rounds
            if d_conv > i_conv or (d_conv == i_conv and d_rounds < i_rounds):
                direct_wins += 1
            elif i_conv > d_conv or (i_conv == d_conv and i_rounds < d_rounds):
                independent_wins += 1
            else:
                ties += 1

    total = direct_wins + independent_wins + ties
    print(f"  Direct friends wins: {direct_wins}/{total} ({100*direct_wins/total:.1f}%)")
    print(f"  Independent set wins: {independent_wins}/{total} ({100*independent_wins/total:.1f}%)")
    print(f"  Ties: {ties}/{total} ({100*ties/total:.1f}%)")

    if direct_converted_total:
        print(f"  Avg converted - Direct: {np.mean(direct_converted_total):.1f}, Independent: {np.mean(independent_converted_total):.1f}")
        print(f"  Avg rounds - Direct: {np.mean(direct_rounds_total):.1f}, Independent: {np.mean(independent_rounds_total):.1f}")

    all_results[net_type] = {
        'direct_wins': direct_wins,
        'independent_wins': independent_wins,
        'ties': ties,
        'direct_converted': direct_converted_total,
        'independent_converted': independent_converted_total,
        'direct_rounds': direct_rounds_total,
        'independent_rounds': independent_rounds_total,
    }

# Overall summary
print("\n" + "=" * 60)
print("OVERALL SUMMARY")
print("=" * 60)

total_direct = sum(r['direct_wins'] for r in all_results.values())
total_independent = sum(r['independent_wins'] for r in all_results.values())
total_ties = sum(r['ties'] for r in all_results.values())
total = total_direct + total_independent + total_ties

print(f"\nAcross all {total} networks:")
print(f"  Direct friends strategy wins: {total_direct} ({100*total_direct/total:.1f}%)")
print(f"  Independent set strategy wins: {total_independent} ({100*total_independent/total:.1f}%)")
print(f"  Ties: {total_ties} ({100*total_ties/total:.1f}%)")

# Visualization
fig, axes = plt.subplots(1, 3, figsize=(14, 5))

for idx, (net_type, results) in enumerate(all_results.items()):
    ax = axes[idx]

    wins = [results['direct_wins'], results['independent_wins'], results['ties']]
    labels = ['Direct\nFriends', 'Independent\nSet', 'Tie']
    colors = ['#3498DB', '#2ECC71', '#95A5A6']

    bars = ax.bar(labels, wins, color=colors, edgecolor='black')
    ax.set_title(f'{net_type.replace("_", " ").title()} Networks', fontsize=12)
    ax.set_ylabel('Number of Wins')

    for bar, win in zip(bars, wins):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                str(win), ha='center', va='bottom', fontsize=10)

plt.suptitle('Strategy Comparison Across Network Types\n(50 random networks each)', fontsize=14)
plt.tight_layout()
plt.savefig('images/network_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nSaved: network_comparison.png")

# Additional analysis: when does independent set win?
print("\n" + "=" * 60)
print("WHEN DOES EACH STRATEGY WIN?")
print("=" * 60)

# Test with varying network density
print("\nEffect of network density (random networks):")
for density in [0.2, 0.3, 0.4, 0.5]:
    direct_wins = 0
    independent_wins = 0
    ties = 0

    for _ in range(30):
        G = generate_random_network(9, density)
        if G.degree("You") == 0:
            continue
        results = evaluate_strategies(G)

        if results['direct']['converted'] and results['independent']['converted']:
            d_conv = results['direct']['converted'][0]
            i_conv = results['independent']['converted'][0]
            d_rounds = results['direct']['rounds'][0]
            i_rounds = results['independent']['rounds'][0]

            if d_conv > i_conv or (d_conv == i_conv and d_rounds < i_rounds):
                direct_wins += 1
            elif i_conv > d_conv or (i_conv == d_conv and i_rounds < d_rounds):
                independent_wins += 1
            else:
                ties += 1

    total = direct_wins + independent_wins + ties
    if total > 0:
        print(f"  Density {density}: Direct {direct_wins}/{total}, Independent {independent_wins}/{total}, Tie {ties}/{total}")
