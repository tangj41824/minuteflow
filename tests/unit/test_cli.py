import json

from minuteflow.cli import build_parser, main


def test_parser_accepts_stdin_and_markdown() -> None:
    args = build_parser().parse_args(["-", "--format", "markdown"])
    assert args.input == "-"
    assert args.format == "markdown"


def test_cli_returns_structured_empty_input_error(tmp_path, capsys) -> None:
    source = tmp_path / "empty.md"
    source.write_text(" \n", encoding="utf-8")

    exit_code = main([str(source), "--format", "json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output["errors"] == ["The meeting notes are empty."]
