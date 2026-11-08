from schedule_agent.cli import main


def test_help(monkeypatch, capsys):
    import pytest
    monkeypatch.setattr("sys.argv", ["schedule-agent", "--help"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    assert "usage:" in capsys.readouterr().out
