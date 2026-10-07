# NEAT Chess

An evolutionary chess evaluation engine built upon Neuroevolution of Augmenting Topologies (NEAT). Rather than relying on handcrafted piece-square tables, minimax depth brute-forcing, or gradient-based backpropagation, the engine evolves both the neural network topology (neurons and synapses) and connection weights over generations to develop board evaluation intuition and positional understanding from self-play and champion benchmarking.

---

## Overview

NEAT Chess provides a complete laboratory for evolving, optimizing, evaluating, and playing against neural chess engines. The repository integrates a tailored fork of `neat-python`, an algebraic graph optimization compiler, an incremental Elo rating system, curriculum learning against an evolving pool of historical champions, and data pipelines for tactical puzzles and grandmaster game mining.

### Core Capabilities

- **Topological and Weight Evolution**: Genomes start from minimal acyclic feed-forward structures (768 direct input connections to a single evaluation output neuron without initial hidden nodes) and gradually complexify by adding neurons, inserting synapses, and tuning weights through genetic mutations.
- **Harmonic Hyperparameter Oscillators**: Mutation rates for structural changes (node additions/deletions, connection additions/deletions) and parameter alterations (weights, biases, and responses) follow continuous sinusoidal waves across generations. This prevents premature speciation collapse and periodically alternates between aggressive topological search and fine-grained weight tuning.
- **Dynamic Speciation Homeostasis**: Rather than maintaining a rigid compatibility threshold, the population dynamically tunes `compatibility_threshold` to stabilize around a target of 7 species.
- **Logarithmic Champion Curriculum**: Evolving bots are evaluated against a historical archive of prior champions. The evaluation selects a logarithmically stratified cohort spanning from the earliest basic bots to the reigning champion, ensuring consistent curriculum progression.
- **Incremental Elo Engine**: Genomes that defeat the benchmark curriculum without conceding losses are crowned champions, saved to disk, evaluated via parallel round-robin tournaments against earlier champions, and assigned an Elo rating using a dynamic K-factor model.
- **Ascending Champion Hierarchy**: Following tournament ranking, champion pickle files are sorted and indexed by Elo ascending: `champ_0.pickle` represents the baseline champion, while the highest-numbered file represents the highest-rated champion.
- **High-Performance Inference**: `fast_evaluator.py` simplifies NEAT directed acyclic graphs (DAGs) through dead-node elimination, parallel synapse merging, constant folding, and dead ReLU pruning, compiling champions into unrolled Python functions or Numba JIT kernels.
- **Interactive Interfaces**: Pygame-based graphical chess boards for human-versus-bot matches (supporting 1-ply static evaluation or deeper Alpha-Beta minimax search) and puzzle solving, supplemented by a CustomTkinter puzzle viewer.

---

## System Architecture

The engine is structured into five decoupled architectural layers that operate across training, evaluation, and inference:

### 1. Evolutionary Orchestration Layer
Located in `custom_neat_lib/population.py`, this layer drives generational cycles, species diversity, and genetic hyperparameters:
- **Adaptive Speciation Control**: The system compares the active species count against `AMOUNT_SPECIES_WANTED = 7.0`. When species count diverges from this setpoint, `compatibility_threshold` increments or decrements by `0.03` per generation to maintain species balance.
- **Harmonic Parameter Oscillators**: Uses the function `oscillator(V_ref, P, gen) = V_ref * (sin(gen / P + pi) + 1)` with periods $P \in [40, 50]$ generations to cycle mutation probabilities (nodes, connections, weights, biases, and responses) between $0$ and $2 \times V_{\text{ref}}$. Population size similarly oscillates by $\pm 30\%$ around its base value.
- **Dynamic Stagnation Adaptation**: Species stagnation limits (`max_stagnation`) adjust between 5 and 200 generations depending on population diversity.

### 2. Distributed Evaluation and Curriculum Pipeline
Implemented across `__main.py` and `custom_neat_lib/parallel.py`:
- **Worker Process Isolation**: Evaluations run across available CPU cores via `multiprocessing.Pool`. Workers maintain an in-memory cache of champion models with file timestamp checks, eliminating inter-process communication serialization bottlenecks.
- **Logarithmic Stratified Curriculum**: Each candidate genome plays against $k$ sampled champions, where:
  $$k_{\text{games}} = \max\left(\left\lfloor \log_2\left(N_{\text{champions}}^2\right) \right\rfloor, 1\right)$$
  Candidate bots play two games (White and Black) against each selected champion. The selection uses uniform index stepping from `champions_arr[0]` (weakest) to `champions_arr[-1]` (strongest).
- **Multi-Factor Fitness Function**:
  - Victory bonus: $1.0 + \frac{0.5}{\text{moves}}$ (incentivizing faster, decisive wins).
  - Defeat penalty: $-1.0 - \frac{0.5}{\text{moves}}$, plus an extra $-1.0$ penalty if defeated by the reigning top champion.
  - Draw evaluation: Scaled fractionally by pawn material differential $\min(0.8, \frac{\Delta_{\text{pawns}}}{20})$.
  - Double-win bonus ($+0.1$) and champion sweep bonus ($+1.0$).

### 3. Champion Promotion and Incremental Elo Rating
Handled in `custom_neat_lib/parallel.py`:
- **Promotion Threshold**: A candidate genome that wins at least one game against the benchmark cohort without suffering any defeats is crowned a new champion.
- **Graph Optimization and Compilation**: Promoted champions are processed by `fast_evaluator.py`, stripping dead subgraphs and compiling the DAG into an optimized evaluation model.
- **Incremental Tournament**: The new champion plays parallel games against all existing champions in `champions/`.
- **Dynamic K-Factor Elo**: Initialized at an Elo of $10.0$ (floor of $1.0$). The K-factor decreases with game experience:
  $$K = \max\left(5.0, 32.0 - \log_2\left(\text{games\_played} + 1\right)\right)$$
- **Automatic File Re-indexing**: All champion files are sorted by Elo and renamed in ascending order. Consequently, `champ_0.pickle` always holds the lowest Elo rating, while `champ_N.pickle` holds the highest Elo rating. Standings are recorded in `leaderboard_elo.txt`.

### 4. Position Featurization and Search Engine
Contained in `classes.py` and `aux_neat_funcs.py`:
- **768-Input Bitplane Tensor**: Board state is mapped to 12 binary planes (6 piece types for White, 6 for Black) across 64 squares:
  - Planes 0 to 5: White Pawn, Knight, Bishop, Rook, Queen, King
  - Planes 6 to 11: Black Pawn, Knight, Bishop, Rook, Queen, King
  - Indexing: $\text{plane} \times 64 + \text{square}$
- **Static Scalar Evaluation**: The network outputs a single float in $[-1.0, 1.0]$ via a `tanh` activation representing White advantage. During move selection, this output is multiplied by $+1$ (White) or $-1$ (Black) so that both colors maximize their score.
- **Decision Modes**:
  - *1-Ply Greedy Evaluation*: Evaluates all legal successor positions and immediately plays checkmate if detected.
  - *Alpha-Beta Minimax Search*: Implemented in `make_decision_depth()` in `classes.py`, providing recursive game tree exploration with alpha-beta pruning and terminal state scoring (`float('inf')` for checkmate, `0` for draw).

### 5. Concurrency and Process Management
Managed in `aux_funcs_random.py` and `aux_backup_managemment.py`:
- **File Semaphores**: Training checks for the presence of `___CONTINUE.txt`. Deleting or renaming this file causes worker threads to sleep safely without interrupting active generational jobs or corrupting checkpoints.
- **Checkpoint Resilience**: Generational states are gzipped into `backups/backup_<gen>`, capturing population topology, species sets, and random states for automatic resumption.

---

## Board Representation and Input Encoding

| Feature | Specification | Details |
|---|---|---|
| Input Dimension | 768 float nodes | 12 piece planes $\times$ 64 squares |
| Input Values | 0.0 or 1.0 | Binary presence of a piece on a square |
| Output Dimension | 1 float node | Position score from White's perspective |
| Output Activation | `tanh` | Range $[-1.0, 1.0]$ |
| Alternative Encoding | 64 float nodes | Piece-value scalar mapping via `get_numeric_board_ai_64()` |

---

## Project Structure

```
NEAT_CHESS/
│
├── __main.py                       # Evolutionary training loop and parallel evaluator
├── _chess_config.txt               # NEAT configuration parameters
├── classes.py                      # Bot engine, Alpha-Beta search, and puzzle structures
├── fast_evaluator.py               # DAG graph optimizer and Numba/unrolled compiler
│
├── ____play_against_bot.py         # Pygame GUI for human vs champion bot matches
├── ___GUI_puzzles.py               # Pygame interactive chess board
├── view_puzzles.py                 # CustomTkinter puzzle viewer with clipboard FEN export
├── ____full_bots_analisys.py       # Exhaustive round-robin tournament and plot generator
├── ___full_champions_leaderboard.py# Standalone winrate leaderboard script
├── test_NN.py                      # Headless bot validation match and PGN printer
├── ______FULL_RESET______.py       # Environment reset utility (clears champions and backups)
│
├── custom_neat_lib/                # Tailored NEAT library
│   ├── population.py               # Evolution cycle, adaptive speciation, and oscillators
│   ├── parallel.py                 # Multiprocessing evaluator and incremental Elo ranking
│   ├── math_util.py                # Mathematical oscillator definitions
│   ├── nn/                         # Feed-forward network implementation
│   └── _added.py                   # Backup routines and puzzle synchronization
│
├── champions/                      # Champion archive sorted by Elo (champ_0 to champ_N)
├── backups/                        # Generational checkpoint files (backup_<gen>)
├── leaderboard_elo.txt             # Active champion Elo rankings
├── bot_analisys_plots/             # Output folder for tournament visualization charts
├── images/                         # Graphical piece sprites for Pygame interfaces
├── stockfish_16/                   # Stockfish 16 engine binaries for ground-truth analysis
└── human_puzzles/                  # Grandmaster PGN parsers and puzzle generation pipelines
```

---

## Installation

### Prerequisites

- Python 3.10 or higher
- Supported on Windows, Linux, and macOS (Stockfish binary in `stockfish_16/` is Windows x86-64 AVX2)

### Setup

Clone the repository and navigate into the workspace:

```bash
git clone https://github.com/your-username/NEAT_CHESS.git
cd NEAT_CHESS
```

Install core dependencies:

```bash
pip install python-chess pygame numpy matplotlib tqdm pyperclip
```

Optional dependencies:
- `customtkinter`: Required for `view_puzzles.py` (`pip install customtkinter`).
- `numba`: Recommended for JIT evaluation in `fast_evaluator.py` (`pip install numba`).
- `stockfish`: Required for Stockfish opening analysis and puzzle generation (`pip install stockfish`).

---

## Configuration

Core evolution parameters are configured in `_chess_config.txt`:

| Section | Parameter | Default | Description |
|---|---|---|---|
| `[NEAT]` | `pop_size` | `200` | Population size (oscillates $\pm 30\%$ dynamically) |
| `[NEAT]` | `fitness_threshold` | `10000` | Termination fitness threshold |
| `[DefaultGenome]` | `num_inputs` | `768` | 12 piece planes $\times$ 64 squares |
| `[DefaultGenome]` | `num_outputs` | `1` | Scalar position evaluation |
| `[DefaultGenome]` | `num_hidden` | `0` | Initial hidden neuron count |
| `[DefaultGenome]` | `feed_forward` | `True` | Enforces acyclic feed-forward networks |
| `[DefaultGenome]` | `initial_connection` | `full_direct` | Connects every input directly to output initially |
| `[DefaultGenome]` | `activation_default` | `tanh` | Node activation function |
| `[DefaultGenome]` | `conn_add_prob` | `0.12` | Synapse addition probability (oscillated) |
| `[DefaultGenome]` | `node_add_prob` | `0.03` | Neuron addition probability (oscillated) |
| `[DefaultGenome]` | `weight_mutate_rate` | `0.70` | Connection weight mutation rate |
| `[DefaultSpeciesSet]` | `compatibility_threshold` | `2.5` | Speciation distance metric (dynamically steered) |
| `[DefaultStagnation]` | `max_stagnation` | `50` | Maximum stagnant generations per species |

---

## Operational Flags and Defaults

To maintain a self-contained environment without external binary dependencies, default configurations are initialized as follows:

- **Puzzle Evaluation**: In `__main.py`, `ENABLE_PUZZLES = False` by default. Set to `True` to incorporate puzzle batches alongside champion games.
- **Opening Theory**: In `openings_theory.py`, `DISABLE_OPENINGS = True` by default. Set to `False` to force theoretical opening book lines.
- **Checkpoint Resumption**: In `__main.py`, `CONTINUE_FROM_CHECKPOINT = True` automatically resumes from `backups/backup_<latest>`. Set to `False` to force a new population from generation 0.

---

## Usage Guide

### 1. Training the Evolutionary Engine

Run the primary training pipeline:

```bash
python __main.py
```

- Training runs parallel evaluations across all available CPU cores.
- If checkpoints exist in `backups/`, training resumes automatically.
- To pause training gracefully, delete or rename `___CONTINUE.txt`. Workers will sleep safely without dropping state. Restore the file to continue.

### 2. Playing Against a Champion Bot

To play against a bot via the Pygame interface:

```bash
python ____play_against_bot.py
```

Before launching, verify the bot index in `____play_against_bot.py`:

```python
BOT_NUMBER = 2          # Must correspond to an existing champ_N.pickle in champions/
DEPTH = 1               # 1 for fast 1-ply static evaluation, >= 2 for Alpha-Beta search
BOT_CONTROLS_WHITE = True
```

Played games are automatically saved as PGN files in `_pgns_to_merge_2/`.

### 3. Running Leaderboard and Analysis Tournaments

To execute a round-robin tournament among saved champions:

```bash
python ___full_champions_leaderboard.py
```

To run detailed statistical analysis with superiority metrics and visualization plots:

```bash
python ____full_bots_analisys.py
```

*Note: Ensure `BOT_NUMBER` in both scripts is adjusted to reflect the highest index currently available in `champions/`.*

### 4. Viewing Tactical Puzzles

To browse generated tactical puzzles with board visualization and clipboard FEN export:

```bash
python view_puzzles.py
```

To interact with the Pygame chessboard sandbox:

```bash
python ___GUI_puzzles.py
```

### 5. Headless Model Testing

To simulate a game between the best saved genome and a baseline opponent:

```bash
python test_NN.py
```

Outputs the game result and mainline PGN notation directly to the terminal.

### 6. Resetting the Environment

To clear existing champions, generation checkpoints, and evaluation caches:

```bash
python ______FULL_RESET______.py
```

Prompts a 5-second safety countdown before clearing runtime data.

---

## Graph Optimization Details

When a bot is promoted to champion status, `fast_evaluator.py` optimizes its topological graph:

1. **Parallel Synapse Folding**: Combines duplicate edges between identical nodes into a single consolidated weight:
   $$w_{\text{final}} = \sum w_i$$
2. **Dead Node Elimination**: Identifies and removes neurons whose activation paths do not reach the output neuron.
3. **Zero-Input Constant Folding**: Propagates constant neuron biases into downstream nodes and removes the orphaned neurons.
4. **Dead ReLU Elimination**: Prunes ReLU units whose input bounds ensure they can never fire.
5. **Compilation**: Emits unrolled Python execution code or Numba JIT kernels, eliminating dictionary lookups during move search.
