#!/usr/bin/env python3
"""推しの布教ネットワーク最適化 - Neutral Atom QC Simulation"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pulser import Register, Sequence, Pulse
from pulser.devices import AnalogDevice
from pulser.waveforms import InterpolatedWaveform
from pulser_simulation import QutipEmulator
import matplotlib.patches as mpatches
import networkx as nx
import os

OUTPUT_DIR = 'images'
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 60)
print("推しの布教ネットワーク最適化")
print("=" * 60)

# =============================================================
# 1. 友達ネットワークの定義
# =============================================================
print("\n[1] Creating Friend Network")

# Friends (nodes) - 10 people network
friends = ["You", "A", "B", "C", "D", "E", "F", "G", "H", "I"]

# Social connections (edges) - who influences who
# Designed as a "hub and spoke" with some cross-links
connections = [
    ("You", "A"),  # Your direct friends (3 people)
    ("You", "B"),
    ("You", "C"),
    ("A", "D"),    # A's friends
    ("A", "E"),
    ("B", "E"),    # B's friends
    ("B", "F"),
    ("C", "F"),    # C's friends
    ("C", "G"),
    ("D", "H"),    # Outer ring
    ("E", "H"),
    ("E", "I"),
    ("F", "I"),
    ("G", "I"),
]

# Create networkx graph for visualization
G = nx.Graph()
G.add_nodes_from(friends)
G.add_edges_from(connections)

# Visualize the network
fig, ax = plt.subplots(figsize=(10, 8))

# Layout
pos = nx.spring_layout(G, seed=42, k=2)

# Draw edges
nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.5, width=2)

# Draw nodes
node_colors = ['#FF6B6B' if n == "You" else '#4ECDC4' for n in G.nodes()]
nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                       node_size=1500, edgecolors='black', linewidths=2)

# Draw labels
nx.draw_networkx_labels(G, pos, ax=ax, font_size=12, font_weight='bold')

ax.set_title('Your Friend Network\n(Red = You, Cyan = Friends)', fontsize=14)
ax.axis('off')

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/oshi_network.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: oshi_network.png")

# =============================================================
# 2. 問題設定: 影響力最大化 → 独立集合
# =============================================================
print("\n[2] Problem Formulation")

# The idea:
# - We want to find the best "seed" set of people to convert first
# - People who are NOT directly connected can be converted simultaneously
#   (they won't "cancel out" each other's influence)
# - This is related to finding an Independent Set in the graph!

# For MIS on Rydberg atoms:
# - Place atoms at positions corresponding to graph nodes
# - Connect nodes (edges) = within blockade radius
# - MIS = maximum set of non-adjacent nodes = optimal seed set

print(f"Nodes: {len(friends)}")
print(f"Edges: {len(connections)}")

# =============================================================
# 3. Map graph to atom positions
# =============================================================
print("\n[3] Mapping to Atom Positions")

# Use spring layout positions, scaled for Rydberg blockade
# Connected nodes should be within ~5-6 μm (blockade)
# Non-connected nodes should be > 8 μm

pos_array = np.array([pos[f] for f in friends])

# Scale: connected pairs within blockade, others outside
# First, normalize
pos_array -= pos_array.mean(axis=0)
pos_array /= np.max(np.abs(pos_array))

# Scale to have connected pairs at ~5 μm
# and non-connected pairs at > 8 μm (hopefully)
scale = 5.0
pos_array *= scale

# Create coordinate dict
coords = {f: (pos_array[i, 0], pos_array[i, 1]) for i, f in enumerate(friends)}

# Verify distances
print("\nEdge distances (should be < 7 μm for blockade):")
for f1, f2 in connections[:5]:  # Show first 5
    dist = np.sqrt((coords[f1][0]-coords[f2][0])**2 + (coords[f1][1]-coords[f2][1])**2)
    print(f"  {f1}-{f2}: {dist:.2f} μm")

# =============================================================
# 4. Alternative: Manual layout for better control
# =============================================================
print("\n[4] Using manual layout for better blockade control")

# Create a layout where connected nodes are close
# The graph structure is roughly:
#     D --- G
#     |     |
# A - You - E
#     |   \ |
#     B --- F
#     |
#     C

# Layout: optimized for blockade
# Connected pairs within ~5-6 μm, minimum >= 5 μm
coords = {
    'You': (0, 0),
    'A': (5, 2),       # You-A
    'B': (2, -5),      # You-B
    'C': (-5, 2),      # You-C
    'D': (10, 5),      # A-D
    'E': (7, -3),      # A-E, B-E
    'F': (-4, -5),     # B-F, C-F
    'G': (-10, 5),     # C-G
    'H': (11, 0),      # D-H, E-H
    'I': (-9, -4),     # F-I, G-I
}

# Verify edge distances
print("\nEdge distances with manual layout:")
edge_dists = []
for f1, f2 in connections:
    dist = np.sqrt((coords[f1][0]-coords[f2][0])**2 + (coords[f1][1]-coords[f2][1])**2)
    edge_dists.append(dist)
    status = "OK" if dist < 7 else "FAR"
    print(f"  {f1}-{f2}: {dist:.2f} μm [{status}]")

print(f"\nEdge distance range: {min(edge_dists):.1f} - {max(edge_dists):.1f} μm")

# =============================================================
# 5. Visualize atom register
# =============================================================
print("\n[5] Creating Atom Register Visualization")

fig, ax = plt.subplots(figsize=(10, 8))

# Draw edges (connections)
for f1, f2 in connections:
    x1, y1 = coords[f1]
    x2, y2 = coords[f2]
    ax.plot([x1, x2], [y1, y2], 'gray', linewidth=1.5, alpha=0.5, zorder=1)

# Draw atoms
for f in friends:
    x, y = coords[f]
    color = '#FF6B6B' if f == "You" else '#4ECDC4'
    circle = plt.Circle((x, y), 0.8, color=color, ec='black', linewidth=2, zorder=10)
    ax.add_patch(circle)
    ax.text(x, y, f, ha='center', va='center', fontsize=10, fontweight='bold', zorder=11)

ax.set_xlim(-10, 13)
ax.set_ylim(-10, 10)
ax.set_aspect('equal')
ax.set_xlabel('x (μm)', fontsize=12)
ax.set_ylabel('y (μm)', fontsize=12)
ax.set_title('Atom Register: Friend Network\nConnected friends = Within blockade radius', fontsize=14)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/oshi_atom_register.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: oshi_atom_register.png")

# =============================================================
# 6. Pulser Simulation
# =============================================================
print("\n[6] Running Pulser Simulation")

coord_list = [coords[f] for f in friends]
reg = Register.from_coordinates(coord_list, prefix="friend_")

# Create sequence
seq = Sequence(reg, AnalogDevice)
seq.declare_channel("rydberg", "rydberg_global")

# Adiabatic pulse for MIS
duration = 4000  # ns
t = np.linspace(0, duration, 100)
omega = 10 * np.sin(np.pi * t / duration) ** 2
delta = -10 + 20 * t / duration

pulse = Pulse(
    amplitude=InterpolatedWaveform(duration, omega),
    detuning=InterpolatedWaveform(duration, delta),
    phase=0
)
seq.add(pulse, "rydberg")

# Run simulation
print("Running simulation...")
sim = QutipEmulator.from_sequence(seq)
results = sim.run()
counts = results.sample_final_state(N_samples=1000)

# =============================================================
# 7. Analyze results
# =============================================================
print("\n[7] Analyzing Results")

def get_selected_friends(state, friends):
    """Get list of friends selected (excited) in this state"""
    return [friends[i] for i, s in enumerate(state) if s == '1']

def is_independent_set(selected, connections):
    """Check if selected set is an independent set (no edges between selected nodes)"""
    for f1, f2 in connections:
        if f1 in selected and f2 in selected:
            return False
    return True

sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)

print("\nTop 10 布教シード候補:")
valid_results = []
for state, count in sorted_counts[:15]:
    selected = get_selected_friends(state, friends)
    is_valid = is_independent_set(selected, connections)

    if is_valid and len(selected) > 0:
        valid_results.append((state, count, selected))
        includes_you = "You" in selected
        you_status = "(自分も含む)" if includes_you else "(自分以外に布教)"
        print(f"  {count:3d}回: {selected} {you_status}")

print(f"\nValid independent sets found: {len(valid_results)}")

# =============================================================
# 8. Visualize best result
# =============================================================
print("\n[8] Visualizing Best Strategy")

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Left: Bar chart of top results
top_n = 8
states_top = [s for s, c, sel in valid_results[:top_n]]
counts_top = [c for s, c, sel in valid_results[:top_n]]
labels_top = [','.join(sel) for s, c, sel in valid_results[:top_n]]

colors = ['#2ECC71' if 'You' not in valid_results[i][2] else '#3498DB'
          for i in range(min(top_n, len(valid_results)))]

axes[0].barh(range(len(counts_top)), counts_top, color=colors, edgecolor='black')
axes[0].set_yticks(range(len(counts_top)))
axes[0].set_yticklabels(labels_top, fontsize=9)
axes[0].set_xlabel('Occurrences', fontsize=12)
axes[0].set_title('Top Seed Strategies\n(Green=Friends only, Blue=Including yourself)', fontsize=13)
axes[0].invert_yaxis()

# Right: Network visualization of best strategy
if valid_results:
    best_state, best_count, best_selected = valid_results[0]

    # Draw network
    for f1, f2 in connections:
        x1, y1 = coords[f1]
        x2, y2 = coords[f2]
        # Scale for visualization
        x1, y1 = x1/2, y1/2
        x2, y2 = x2/2, y2/2
        axes[1].plot([x1, x2], [y1, y2], 'gray', linewidth=1.5, alpha=0.4, zorder=1)

    # Draw nodes
    for f in friends:
        x, y = coords[f]
        x, y = x/2, y/2  # Scale

        if f in best_selected:
            color = '#FF6B6B'  # Selected = 布教ターゲット
            size = 1.0
        else:
            color = '#BDC3C7'  # Not selected
            size = 0.6

        circle = plt.Circle((x, y), size, color=color, ec='black', linewidth=2, zorder=10)
        axes[1].add_patch(circle)

        # Add star marker for selected
        if f in best_selected:
            axes[1].plot(x+0.8, y+0.8, '*', color='gold', markersize=15, zorder=12)

        axes[1].text(x, y, f, ha='center', va='center', fontsize=9, fontweight='bold', zorder=11)

    axes[1].set_xlim(-6, 8)
    axes[1].set_ylim(-5, 5)
    axes[1].set_aspect('equal')
    axes[1].set_title(f'Best Strategy: First, convert {best_selected}!\n({best_count} occurrences)', fontsize=13)
    axes[1].axis('off')

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/oshi_results.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: oshi_results.png")

# =============================================================
# 9. Spread simulation (bonus visualization)
# =============================================================
print("\n[9] Simulating Spread from Best Seeds")

if valid_results:
    best_selected = valid_results[0][2]

    # Simple spread model: each round, non-converted friends
    # become converted if majority of their friends are converted

    converted = set(best_selected)
    history = [set(converted)]

    for round in range(5):
        new_converts = set()
        for f in friends:
            if f in converted:
                continue
            # Count converted neighbors
            neighbors = [n for n1, n2 in connections for n in [n1, n2]
                        if (n1 == f or n2 == f) and n != f]
            converted_neighbors = sum(1 for n in neighbors if n in converted)

            # Convert if majority of neighbors are converted
            if converted_neighbors >= len(neighbors) / 2:
                new_converts.add(f)

        if not new_converts:
            break
        converted = converted | new_converts
        history.append(set(converted))

    print(f"\nSpread simulation from {best_selected}:")
    for i, conv in enumerate(history):
        print(f"  Round {i}: {sorted(conv)} ({len(conv)}/{len(friends)} converted)")

    # Visualize spread
    n_rounds = len(history)
    fig, axes = plt.subplots(1, min(n_rounds, 4), figsize=(4*min(n_rounds, 4), 4))
    if n_rounds == 1:
        axes = [axes]

    for round_idx, conv in enumerate(history[:4]):
        ax = axes[round_idx]

        # Draw edges
        for f1, f2 in connections:
            x1, y1 = coords[f1]
            x2, y2 = coords[f2]
            x1, y1 = x1/3, y1/3
            x2, y2 = x2/3, y2/3
            ax.plot([x1, x2], [y1, y2], 'gray', linewidth=1, alpha=0.3)

        # Draw nodes
        for f in friends:
            x, y = coords[f]
            x, y = x/3, y/3

            if f in conv:
                color = '#FF6B6B'  # Converted!
            else:
                color = '#E0E0E0'  # Not yet

            circle = plt.Circle((x, y), 0.5, color=color, ec='black', linewidth=1.5)
            ax.add_patch(circle)
            ax.text(x, y, f, ha='center', va='center', fontsize=7, fontweight='bold')

        ax.set_xlim(-4, 5)
        ax.set_ylim(-4, 4)
        ax.set_aspect('equal')
        ax.set_title(f'Round {round_idx}\n{len(conv)}/{len(friends)} fans', fontsize=11)
        ax.axis('off')

    plt.suptitle('How your oshi spreads through the network!', fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/oshi_spread.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: oshi_spread.png")

# =============================================================
# 10. Compare different strategies
# =============================================================
print("\n[10] Comparing Different Strategies")

def simulate_spread(initial_seeds, friends, connections, max_rounds=10, enemies=None):
    """Simulate spread and return history

    enemies: list of tuples (a, b) where if a is fan, b will never become fan (and vice versa)
    """
    if enemies is None:
        enemies = []

    converted = set(initial_seeds)
    # You is always a fan
    converted.add("You")

    # Check which people are blocked due to enemies
    blocked = set()
    for a, b in enemies:
        if a in converted:
            blocked.add(b)
        if b in converted:
            blocked.add(a)

    history = [set(converted)]

    for round_num in range(max_rounds):
        new_converts = set()
        for f in friends:
            if f in converted or f in blocked:
                continue
            # Count converted neighbors
            neighbors = [n for n1, n2 in connections for n in [n1, n2]
                        if (n1 == f or n2 == f) and n != f]
            converted_neighbors = sum(1 for n in neighbors if n in converted)

            # Convert if majority of neighbors are converted
            if converted_neighbors >= len(neighbors) / 2:
                new_converts.add(f)

        if not new_converts:
            break

        # Update blocked based on new converts
        for a, b in enemies:
            if a in new_converts:
                blocked.add(b)
            if b in new_converts:
                blocked.add(a)

        converted = converted | new_converts
        history.append(set(converted))

    return history, blocked

# Find best 3-person strategies from simulation results
print("\n=== Finding Best 3-Person Strategies ===")
three_person_results = [(s, c, sel) for s, c, sel in valid_results if len(sel) == 3]
print(f"Found {len(three_person_results)} valid 3-person strategies")
for s, c, sel in three_person_results[:5]:
    print(f"  {c}回: {sel}")

# Strategy 1: Best 3-person from quantum (should be something like F, G, H or D, F, G)
if three_person_results:
    best_3 = three_person_results[0][2]
else:
    best_3 = ["D", "F", "G"]  # fallback
strategy_optimal = best_3
history_optimal, _ = simulate_spread(strategy_optimal, friends, connections)

# Strategy 2: Direct friends (A, B, C)
strategy_direct = ["A", "B", "C"]
history_direct, _ = simulate_spread(strategy_direct, friends, connections)

# Strategy 3: Bad strategy - one side only (D, E, H) - 3 people but clustered
strategy_bad = ["D", "E", "H"]
history_bad, _ = simulate_spread(strategy_bad, friends, connections)

print("\n=== Strategy Comparison (3 people each) ===")
print(f"\n1. Quantum Optimal ({', '.join(strategy_optimal)}) - 3 people:")
for i, conv in enumerate(history_optimal):
    print(f"   Round {i}: {len(conv)}/10 fans - {sorted(conv)}")

print(f"\n2. Direct friends (A, B, C) - 3 people:")
for i, conv in enumerate(history_direct):
    print(f"   Round {i}: {len(conv)}/10 fans - {sorted(conv)}")

print(f"\n3. Bad strategy (D, E, H) - 3 people, one side:")
for i, conv in enumerate(history_bad):
    print(f"   Round {i}: {len(conv)}/10 fans - {sorted(conv)}")

final_optimal = len(history_optimal[-1])
final_direct = len(history_direct[-1])
final_bad = len(history_bad[-1])

print(f"\n=== Summary ===")
print(f"Optimal ({','.join(strategy_optimal)}): {len(history_optimal)-1} rounds -> {final_optimal}/10 {'✓ Complete!' if final_optimal == 10 else '✗ Stuck'}")
print(f"Direct (A,B,C):        {len(history_direct)-1} rounds -> {final_direct}/10 {'✓ Complete!' if final_direct == 10 else '✗ Stuck'}")
print(f"Bad (D,E,H):           {len(history_bad)-1} rounds -> {final_bad}/10 {'✓ Complete!' if final_bad == 10 else '✗ Stuck'}")

# =============================================================
# 12. Enemy simulation
# =============================================================
print("\n" + "=" * 60)
print("[12] Enemy Simulation - What if some people don't get along?")
print("=" * 60)

# Define enemies: if one becomes fan, the other NEVER will
enemies = [
    ("A", "G"),  # AとGは犬猿の仲
]

print(f"\nEnemies: {enemies}")
print("Rule: If one becomes a fan, the other will NEVER become a fan!")

# Test different strategies with enemies
print("\n=== With Enemies: A and G are rivals ===")

# Strategy 1: Optimal (F, G, H) - G is in the seed, so A will be blocked!
history_enemy_optimal, blocked_optimal = simulate_spread(strategy_optimal, friends, connections, enemies=enemies)
print(f"\n1. Optimal ({', '.join(strategy_optimal)}):")
print(f"   Blocked: {blocked_optimal}")
for i, conv in enumerate(history_enemy_optimal):
    print(f"   Round {i}: {len(conv)}/10 fans - {sorted(conv)}")

# Strategy 2: Direct friends (A, B, C) - A is in the seed, so G will be blocked!
history_enemy_direct, blocked_direct = simulate_spread(strategy_direct, friends, connections, enemies=enemies)
print(f"\n2. Direct friends (A, B, C):")
print(f"   Blocked: {blocked_direct}")
for i, conv in enumerate(history_enemy_direct):
    print(f"   Round {i}: {len(conv)}/10 fans - {sorted(conv)}")

# Strategy 3: Avoid both enemies - try D, F, H
strategy_avoid = ["D", "F", "H"]
history_enemy_avoid, blocked_avoid = simulate_spread(strategy_avoid, friends, connections, enemies=enemies)
print(f"\n3. Avoid enemies ({', '.join(strategy_avoid)}):")
print(f"   Blocked: {blocked_avoid}")
for i, conv in enumerate(history_enemy_avoid):
    print(f"   Round {i}: {len(conv)}/10 fans - {sorted(conv)}")

# Strategy 4: B, F, H (completely avoid both A and G initially)
strategy_neutral = ["B", "F", "H"]
history_enemy_neutral, blocked_neutral = simulate_spread(strategy_neutral, friends, connections, enemies=enemies)
print(f"\n4. Neutral start ({', '.join(strategy_neutral)}):")
print(f"   Blocked: {blocked_neutral}")
for i, conv in enumerate(history_enemy_neutral):
    print(f"   Round {i}: {len(conv)}/10 fans - {sorted(conv)}")

print(f"\n=== Enemy Simulation Summary ===")
print(f"Optimal (F,G,H) with enemies: {len(history_enemy_optimal[-1])}/10 (blocked: {blocked_optimal})")
print(f"Direct (A,B,C) with enemies:  {len(history_enemy_direct[-1])}/10 (blocked: {blocked_direct})")
print(f"Avoid (D,F,H) with enemies:   {len(history_enemy_avoid[-1])}/10 (blocked: {blocked_avoid})")
print(f"Neutral (B,F,H) with enemies: {len(history_enemy_neutral[-1])}/10 (blocked: {blocked_neutral})")

# =============================================================
# 11. Visualize strategy comparison
# =============================================================
print("\n[11] Visualizing Strategy Comparison")

fig, axes = plt.subplots(3, 4, figsize=(14, 10))

strategies = [
    (f"Optimal: {','.join(strategy_optimal)}", strategy_optimal, history_optimal, '#2ECC71'),
    ("Direct: A,B,C", strategy_direct, history_direct, '#3498DB'),
    ("Bad: D,E,H", strategy_bad, history_bad, '#E74C3C'),
]

for row_idx, (name, seeds, history, color) in enumerate(strategies):
    for col_idx in range(4):
        ax = axes[row_idx, col_idx]

        if col_idx < len(history):
            conv = history[col_idx]
        else:
            conv = history[-1]  # Final state

        # Draw edges
        for f1, f2 in connections:
            x1, y1 = coords[f1]
            x2, y2 = coords[f2]
            x1, y1 = x1/3, y1/3
            x2, y2 = x2/3, y2/3
            ax.plot([x1, x2], [y1, y2], 'gray', linewidth=0.8, alpha=0.3)

        # Draw nodes
        for f in friends:
            x, y = coords[f]
            x, y = x/3, y/3

            if f in conv:
                node_color = '#FF6B6B'  # Fan
            else:
                node_color = '#E0E0E0'  # Not fan

            circle = plt.Circle((x, y), 0.45, color=node_color, ec='black', linewidth=1)
            ax.add_patch(circle)
            ax.text(x, y, f, ha='center', va='center', fontsize=6, fontweight='bold')

        ax.set_xlim(-4.5, 5)
        ax.set_ylim(-3.5, 3.5)
        ax.set_aspect('equal')
        ax.axis('off')

        if col_idx == 0:
            ax.set_title(f'{name}\nRound 0: {len(conv)}/10', fontsize=9, color=color, fontweight='bold')
        else:
            round_label = col_idx if col_idx < len(history) else f'{len(history)-1} (Final)'
            ax.set_title(f'Round {round_label}: {len(conv)}/10', fontsize=9)

plt.suptitle('Strategy Comparison: Which initial targets work best?', fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/oshi_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: oshi_comparison.png")

print("\n" + "=" * 60)
print("Simulation complete!")
print("=" * 60)
