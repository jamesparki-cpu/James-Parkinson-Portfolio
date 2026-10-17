"""Alpha-beta minimax chess agent evaluated against a random baseline.

Usage:
    python chess_agent.py                    # 50-game tournament + demo GIF
    python chess_agent.py --games 10 --depth 2 --no-gif

Outputs (written to ./outputs and ./videos):
    chess_results.csv   one row per game
    chess_summary.csv   win / draw / loss rates
    chess_results.png   bar chart of outcomes
    chess_demo_game.gif replay of one agent-vs-random game
"""
from __future__ import annotations

import argparse
import random
import time
from dataclasses import dataclass
from pathlib import Path

import chess
import imageio.v2 as imageio
import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


@dataclass
class ChessConfig:
    """Configuration for the tournament and output locations."""

    seed: int = 532
    search_depth: int = 3
    evaluation_games: int = 50
    max_plies: int = 200
    output_dir: Path = Path("outputs")
    video_dir: Path = Path("videos")


PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}
CENTER_SQUARES = {chess.D4, chess.E4, chess.D5, chess.E5}


class RandomAgent:
    """Uniform random baseline over legal moves."""

    name = "Random"

    def __init__(self, rng: random.Random):
        self.rng = rng

    def get_move(self, board: chess.Board) -> chess.Move:
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            raise ValueError("No legal moves available")
        return self.rng.choice(legal_moves)


class AlphaBetaAgent:
    """Depth-limited minimax agent with alpha-beta pruning."""

    name = "AlphaBeta-Minimax"

    def __init__(self, depth: int = 3):
        self.depth = depth
        self.nodes_searched = 0

    def evaluate(self, board: chess.Board) -> int:
        """Score a board from White's perspective: material, mobility, centre control."""
        if board.is_checkmate():
            return -100_000 if board.turn == chess.WHITE else 100_000
        if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
            return 0

        score = 0
        for piece_type, value in PIECE_VALUES.items():
            score += len(board.pieces(piece_type, chess.WHITE)) * value
            score -= len(board.pieces(piece_type, chess.BLACK)) * value

        def mobility_for(color: chess.Color) -> int:
            temp = board.copy(stack=False)
            temp.turn = color
            return len(list(temp.legal_moves))

        score += 2 * (mobility_for(chess.WHITE) - mobility_for(chess.BLACK))

        for square in CENTER_SQUARES:
            piece = board.piece_at(square)
            if piece is not None:
                score += 15 if piece.color == chess.WHITE else -15
        return score

    def get_move(self, board: chess.Board) -> chess.Move:
        """Return the best legal move found by depth-limited alpha-beta search."""
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            raise ValueError("No legal moves available")
        self.nodes_searched = 0
        maximizing = board.turn == chess.WHITE
        best_score = -float("inf") if maximizing else float("inf")
        best_move = legal_moves[0]
        alpha, beta = -float("inf"), float("inf")

        for move in self.order_moves(board, legal_moves):
            board.push(move)
            score = self.alphabeta(board, self.depth - 1, alpha, beta)
            board.pop()
            if maximizing and score > best_score:
                best_score, best_move = score, move
            elif not maximizing and score < best_score:
                best_score, best_move = score, move
            if maximizing:
                alpha = max(alpha, best_score)
            else:
                beta = min(beta, best_score)
        return best_move

    def alphabeta(self, board: chess.Board, depth: int, alpha: float, beta: float) -> int:
        """Recursive minimax search with alpha-beta cutoffs."""
        self.nodes_searched += 1
        if depth == 0 or board.is_game_over(claim_draw=True):
            return self.evaluate(board)

        legal_moves = self.order_moves(board, list(board.legal_moves))
        if board.turn == chess.WHITE:
            value = -float("inf")
            for move in legal_moves:
                board.push(move)
                value = max(value, self.alphabeta(board, depth - 1, alpha, beta))
                board.pop()
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return int(value)

        value = float("inf")
        for move in legal_moves:
            board.push(move)
            value = min(value, self.alphabeta(board, depth - 1, alpha, beta))
            board.pop()
            beta = min(beta, value)
            if alpha >= beta:
                break
        return int(value)

    def order_moves(self, board: chess.Board, moves: list[chess.Move]) -> list[chess.Move]:
        """Try captures, promotions and centre moves first to improve pruning."""

        def move_score(move: chess.Move) -> int:
            score = 0
            if board.is_capture(move):
                victim = board.piece_at(move.to_square)
                attacker = board.piece_at(move.from_square)
                if board.is_en_passant(move):
                    score += 10 * PIECE_VALUES[chess.PAWN]
                elif victim and attacker:
                    score += 10 * PIECE_VALUES[victim.piece_type] - PIECE_VALUES[attacker.piece_type]
            if move.promotion:
                score += PIECE_VALUES.get(move.promotion, 0)
            if move.to_square in CENTER_SQUARES:
                score += 20
            return score

        return sorted(moves, key=move_score, reverse=True)


def play_game(white_agent, black_agent, max_plies: int) -> dict:
    """Play one legal game. Games that reach the ply cap are scored as draws."""
    board = chess.Board()
    move_history = []
    start_time = time.time()

    for _ in range(max_plies):
        if board.is_game_over(claim_draw=True):
            break
        agent = white_agent if board.turn == chess.WHITE else black_agent
        move = agent.get_move(board)
        if move not in board.legal_moves:
            raise ValueError(f"Illegal move selected: {move}")
        board.push(move)
        move_history.append(move.uci())

    if not board.is_game_over(claim_draw=True):
        result, termination = "1/2-1/2", "max_plies_draw"
    else:
        outcome = board.outcome(claim_draw=True)
        result = board.result(claim_draw=True)
        termination = outcome.termination.name if outcome else "unknown"

    return {
        "result": result,
        "termination": termination,
        "plies": len(move_history),
        "moves": move_history,
        "final_fen": board.fen(),
        "duration_seconds": time.time() - start_time,
    }


def tournament(agent: AlphaBetaAgent, baseline: RandomAgent, cfg: ChessConfig):
    """Evaluate the agent against the baseline, alternating colours each game."""
    rows = []
    for game_idx in range(cfg.evaluation_games):
        agent_is_white = game_idx % 2 == 0
        white, black = (agent, baseline) if agent_is_white else (baseline, agent)
        game = play_game(white, black, cfg.max_plies)
        res = game["result"]
        if res == "1/2-1/2":
            outcome = "draw"
        elif (res == "1-0") == agent_is_white:
            outcome = "win"
        else:
            outcome = "loss"
        rows.append({
            "game": game_idx + 1,
            "agent_colour": "white" if agent_is_white else "black",
            "result": res,
            "agent_outcome": outcome,
            "termination": game["termination"],
            "plies": game["plies"],
            "duration_seconds": round(game["duration_seconds"], 3),
        })
        print(f"game {game_idx + 1:>3}/{cfg.evaluation_games}: agent {outcome:<4} "
              f"as {rows[-1]['agent_colour']:<5} in {game['plies']} plies")

    game_df = pd.DataFrame(rows)
    counts = game_df["agent_outcome"].value_counts().reindex(["win", "draw", "loss"], fill_value=0)
    summary_df = pd.DataFrame({"outcome": counts.index, "games": counts.values,
                               "rate": counts.values / len(game_df)})
    summary_df["average_game_length"] = float(game_df["plies"].mean())
    return game_df, summary_df


def plot_summary(summary_df: pd.DataFrame, n_games: int, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(summary_df["outcome"], summary_df["rate"], color=["#2ca25f", "#9e9ac8", "#de2d26"])
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Rate")
    ax.set_title(f"Alpha-beta agent vs random baseline ({n_games} games)")
    for bar, rate in zip(bars, summary_df["rate"]):
        x = bar.get_x() + bar.get_width() / 2
        if rate > 0:
            ax.text(x, bar.get_height() / 2, f"{rate:.0%}", ha="center", va="center",
                    color="white", fontweight="bold")
        else:
            ax.text(x, 0.025, f"{rate:.0%}", ha="center", va="bottom")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


PIECE_GLYPHS = {
    "P": "♙", "N": "♘", "B": "♗", "R": "♖", "Q": "♕", "K": "♔",
    "p": "♟", "n": "♞", "b": "♝", "r": "♜", "q": "♛", "k": "♚",
}


def render_board_frame(board: chess.Board, title: str) -> np.ndarray:
    """Render a board position as an RGB array for GIF writing."""
    light, dark = "#f0d9b5", "#b58863"
    fig, ax = plt.subplots(figsize=(6, 6), dpi=100)
    for square in chess.SQUARES:
        f, r = chess.square_file(square), chess.square_rank(square)
        ax.add_patch(plt.Rectangle((f, r), 1, 1, color=light if (f + r) % 2 == 0 else dark))
        piece = board.piece_at(square)
        if piece is None:
            continue
        fill = "#f8fafc" if piece.color == chess.WHITE else "#111827"
        stroke = "#111827" if piece.color == chess.WHITE else "#f8fafc"
        ax.text(f + 0.5, r + 0.5, PIECE_GLYPHS[piece.symbol()], ha="center", va="center",
                fontsize=34, color=fill,
                path_effects=[path_effects.withStroke(linewidth=1.8, foreground=stroke)])
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 8)
    ax.set_xticks(np.arange(8) + 0.5, labels=list("abcdefgh"))
    ax.set_yticks(np.arange(8) + 0.5, labels=[str(i) for i in range(1, 9)])
    ax.tick_params(length=0)
    ax.set_aspect("equal")
    ax.set_title(title, pad=10)
    fig.tight_layout()
    fig.canvas.draw()
    frame = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
    plt.close(fig)
    return frame


def save_game_gif(moves: list[str], gif_path: Path, frame_duration: float = 0.55) -> int:
    """Replay a UCI move list and save it as an animated GIF. Returns the frame count."""
    board = chess.Board()
    frames = [render_board_frame(board, "Starting position")]
    for ply, uci in enumerate(moves, start=1):
        move = chess.Move.from_uci(uci)
        san = board.san(move)
        board.push(move)
        side = "White" if ply % 2 == 1 else "Black"
        frames.append(render_board_frame(board, f"Move {(ply + 1) // 2}: {side} {san}"))
    imageio.mimsave(gif_path, frames, duration=frame_duration, loop=0)
    return len(frames)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--games", type=int, default=50, help="number of evaluation games")
    parser.add_argument("--depth", type=int, default=3, help="alpha-beta search depth in plies")
    parser.add_argument("--max-plies", type=int, default=200, help="ply cap per game (draw if reached)")
    parser.add_argument("--seed", type=int, default=532)
    parser.add_argument("--no-gif", action="store_true", help="skip the demo game GIF")
    args = parser.parse_args()

    cfg = ChessConfig(seed=args.seed, search_depth=args.depth,
                      evaluation_games=args.games, max_plies=args.max_plies)
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    cfg.video_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(cfg.seed)
    random_agent = RandomAgent(rng)
    minimax_agent = AlphaBetaAgent(depth=cfg.search_depth)

    games, summary = tournament(minimax_agent, random_agent, cfg)
    games.to_csv(cfg.output_dir / "chess_results.csv", index=False)
    summary.to_csv(cfg.output_dir / "chess_summary.csv", index=False)
    plot_summary(summary, cfg.evaluation_games, cfg.output_dir / "chess_results.png")
    print("\n" + summary.to_string(index=False))

    if not args.no_gif:
        demo = play_game(minimax_agent, random_agent, cfg.max_plies)
        frames = save_game_gif(demo["moves"], cfg.video_dir / "chess_demo_game.gif")
        print(f"\nDemo game: {demo['result']} after {demo['plies']} plies ({frames} frames) "
              f"-> {cfg.video_dir / 'chess_demo_game.gif'}")


if __name__ == "__main__":
    main()
