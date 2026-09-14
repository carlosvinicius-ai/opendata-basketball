"""Command-line interface (CLI) for running BAV, SCI, and Full Spectrum Player Value pipelines.

Provides clean commands for model execution, scoring, evaluation, and report generation.
Respects Clean Architecture: does NOT import directly from domain.
"""

import argparse
import sys
from pathlib import Path

from infrastructure.event_loader import load_events, load_player_directory
from infrastructure.tracking_loader import load_tracking
from presentation.report_builder import ReportBuilder
from use_cases.bav.action_sequencer import ActionSequencer
from use_cases.bav.bav_model import BAVModel
from use_cases.bav.bav_scorer import BAVScorer
from use_cases.bav.state_extractor import StateExtractor
from use_cases.player_value.combiner import PlayerValueCombiner
from use_cases.player_value.validator import PlayerValueValidator
from use_cases.sci.gnn_model import GNNModel
from use_cases.sci.graph_dataset_builder import GraphDatasetBuilder
from use_cases.sci.sci_calculator import SCICalculator

TRAIN_GAMES = [114243, 114234, 114169, 114099, 114086, 178442, 179612, 184439]
TEST_GAMES = [188630, 191313]
ALL_GAMES = TRAIN_GAMES + TEST_GAMES


def cmd_run_bav(args: argparse.Namespace) -> int:
    """Execute the Ball Action Value (BAV) pipeline."""
    games = [int(g) for g in args.games.split(",")] if args.games else ALL_GAMES
    print(f"[*] Running BAV pipeline across {len(games)} games...")

    sequencer = ActionSequencer()
    extractor = StateExtractor()

    all_features = []
    for gid in games:
        events = load_events(gid)
        sequenced = sequencer.extract_sequences(events, game_id=gid)
        if sequenced.is_empty():
            continue
        tracking_df = load_tracking(gid, max_frames=2000)
        feats = extractor.extract_features(sequenced, events, tracking_df=tracking_df)
        all_features.append(feats)

    if not all_features:
        print("[!] No actions extracted.")
        return 1

    import polars as pl
    full_df = pl.concat(all_features)
    print(f"[*] Extracted {len(full_df)} actions for BAV.")

    model = BAVModel()
    metrics = model.train_and_evaluate(
        full_df,
        train_games=tuple(TRAIN_GAMES),
        test_games=tuple(TEST_GAMES),
        model_save_path="models/bav_xgboost.json",
    )
    print(f"[+] BAV Test Metrics: Brier={metrics.get('brier_score', 0.0):.4f}, AUC={metrics.get('auc_roc', 0.0):.4f}")
    print("[+] BAV model fitted and saved to models/bav_xgboost.json")

    scorer = BAVScorer(model=model)
    scored_actions = scorer.score_actions(full_df)
    bav_scores = scorer.aggregate_player_bav(scored_actions, save_path="outputs/scores/bav_scores.parquet")
    print(f"[+] Computed BAV scores for {len(bav_scores)} players.")
    return 0


def cmd_run_sci(args: argparse.Namespace) -> int:
    """Execute the Space Creation Index (SCI) pipeline."""
    games = [int(g) for g in args.games.split(",")] if args.games else ALL_GAMES
    print(f"[*] Running SCI pipeline across {len(games)} games...")

    dataset_builder = GraphDatasetBuilder()
    graphs = dataset_builder.build_and_save_dataset(
        game_ids=games,
        filename="sci_graph_dataset.pt",
        max_chances_per_game=args.max_chances,
    )
    print(f"[+] Loaded/built {len(graphs)} chance spatial graphs.")

    if not graphs:
        print("[!] No graphs available.")
        return 1

    from torch_geometric.loader import DataLoader
    loader = DataLoader(graphs, batch_size=4, shuffle=True)

    model = GNNModel()
    model.fit(train_loader=loader, epochs=args.epochs, patience=5)
    model.save("models/sci_graphsage.pt")
    print("[+] GraphSAGE model trained and saved to models/sci_graphsage.pt")

    calculator = SCICalculator(model=model)
    sci_scores = calculator.calculate_player_sci(graphs, output_path="outputs/scores/sci_scores.parquet")
    print(f"[+] Computed SCI scores for {len(sci_scores)} players.")
    return 0


def cmd_run_all(args: argparse.Namespace) -> int:
    """Execute both BAV & SCI pipelines and synthesize Full Spectrum Player Value."""
    print("[*] Running Full Spectrum Pipeline (BAV + SCI + FSPV)...")
    cmd_run_bav(args)
    cmd_run_sci(args)

    combiner = PlayerValueCombiner(alpha=args.alpha)
    bav_path = "outputs/scores/bav_scores.parquet"
    sci_path = "outputs/scores/sci_scores.parquet"

    player_meta = load_player_directory()
    rankings = combiner.combine(
        bav_scores=bav_path if Path(bav_path).exists() else [],
        sci_scores=sci_path if Path(sci_path).exists() else [],
        player_metadata=player_meta,
    )
    print(f"[+] FSPV Rankings computed for {len(rankings)} players.")

    validator = PlayerValueValidator()
    val_report = validator.validate(rankings)
    print(f"[+] Validation complete: status={val_report.get('status')}")

    builder = ReportBuilder()
    html_path = builder.build_report()
    print(f"[+] Full Report generated at: {html_path}")
    return 0


def cmd_build_report(args: argparse.Namespace) -> int:
    """Generate the standalone HTML5 report."""
    builder = ReportBuilder()
    output_filename = args.output or "full_spectrum_player_value.html"
    path = builder.build_report(output_filename=output_filename)
    print(f"[+] Standalone HTML5 report ready at: {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="opendata-basketball",
        description="SkillCorner Basketball Analytics Cup — Full Spectrum Player Value CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # run-bav
    p_bav = subparsers.add_parser("run-bav", help="Execute BAV (on-ball action value) pipeline")
    p_bav.add_argument("--games", type=str, default="", help="Comma-separated game IDs")

    # run-sci
    p_sci = subparsers.add_parser("run-sci", help="Execute SCI (off-ball space creation) pipeline")
    p_sci.add_argument("--games", type=str, default="", help="Comma-separated game IDs")
    p_sci.add_argument("--max-chances", type=int, default=10, help="Max chances per game to sample")
    p_sci.add_argument("--epochs", type=int, default=5, help="Number of training epochs")

    # run-all
    p_all = subparsers.add_parser("run-all", help="Execute full end-to-end analytical pipeline")
    p_all.add_argument("--games", type=str, default="", help="Comma-separated game IDs")
    p_all.add_argument("--max-chances", type=int, default=10, help="Max chances per game")
    p_all.add_argument("--epochs", type=int, default=5, help="Training epochs for GNN")
    p_all.add_argument("--alpha", type=float, default=0.5, help="BAV weight in FSPV [0.0, 1.0]")

    # build-report
    p_rep = subparsers.add_parser("build-report", help="Generate standalone HTML5 dashboard")
    p_rep.add_argument("--output", type=str, default="full_spectrum_player_value.html", help="Output HTML filename")

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI main execution entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "run-bav": cmd_run_bav,
        "run-sci": cmd_run_sci,
        "run-all": cmd_run_all,
        "build-report": cmd_build_report,
    }

    cmd_fn = commands.get(args.command)
    if cmd_fn:
        return cmd_fn(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
