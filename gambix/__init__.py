"""
Gambix v2 — A Verified, Engine-Grounded, Graph-Neural Chess Explanation System.

Architecture layers:
  symbolic    — deterministic tactical/positional detectors (≥99% precision)
  engine      — Stockfish wrapper, counterfactual probes, move-quality classifier
  graph       — heterogeneous graph builder (PyG HeteroData)
  model       — HGT/RGAT GNN with eval/WDL/tension/fragility heads
  explain     — GNNExplainer + Integrated Gradients with fidelity validation
  pipeline    — Fact Sheet assembler (merges all signal sources)
  llm         — constrained LLM chain with multi-provider fallback
  verifier    — claim verifier that gates every output sentence
  report      — game-level coaching report generator
  whatif      — what-if explorer and weakness profiler
  puzzles     — blunder-to-puzzle converter with Stockfish validation

Licence: GPL-3.0-or-later
"""

__version__ = "2.0.0"
__author__ = "Gambix Contributors"
__license__ = "GPL-3.0-or-later"
