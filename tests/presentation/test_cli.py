"""Unit tests for presentation CLI entrypoint."""


from presentation.cli import build_parser, main


def test_cli_parser_subcommands():
    """Verify CLI parser registers all expected subcommands."""
    parser = build_parser()

    # Test run-bav args
    args_bav = parser.parse_args(["run-bav", "--games", "114243"])
    assert args_bav.command == "run-bav"
    assert args_bav.games == "114243"

    # Test run-sci args
    args_sci = parser.parse_args(["run-sci", "--max-chances", "5", "--epochs", "2"])
    assert args_sci.command == "run-sci"
    assert args_sci.max_chances == 5
    assert args_sci.epochs == 2

    # Test run-all args
    args_all = parser.parse_args(["run-all", "--alpha", "0.6"])
    assert args_all.command == "run-all"
    assert args_all.alpha == 0.6

    # Test build-report args
    args_rep = parser.parse_args(["build-report", "--output", "custom.html"])
    assert args_rep.command == "build-report"
    assert args_rep.output == "custom.html"


def test_cli_main_build_report_execution(tmp_path):
    """Verify build-report subcommand executes successfully via main()."""
    target = str(tmp_path / "cli_report.html")
    exit_code = main(["build-report", "--output", target])
    assert exit_code == 0
