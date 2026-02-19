# tests/test_today.py
from unittest.mock import patch, MagicMock
from datetime import datetime

def test_today_prints_content(capsys):
    import ntn
    mock_client = MagicMock()
    mock_config = {"api_key": "test", "brain_dump_page_id": "parent-id", "databases": {}}
    today = datetime.now().strftime("%d-%m-%Y")
    mock_client.search.return_value = {
        "results": [{"id": "page-id", "parent": {"page_id": "parent-id"},
                     "properties": {"title": {"title": [{"plain_text": today}]}}}]
    }
    mock_client.blocks.children.list.return_value = {
        "results": [{"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "My thought"}]}}]
    }
    args = MagicMock()
    with patch("ntn.load_config", return_value=mock_config):
        with patch("ntn.get_client", return_value=mock_client):
            ntn.cmd_today(args)
    assert "My thought" in capsys.readouterr().out

def test_today_no_page_message(capsys):
    import ntn
    mock_client = MagicMock()
    mock_config = {"api_key": "test", "brain_dump_page_id": "parent-id", "databases": {}}
    mock_client.search.return_value = {"results": []}
    args = MagicMock()
    with patch("ntn.load_config", return_value=mock_config):
        with patch("ntn.get_client", return_value=mock_client):
            ntn.cmd_today(args)
    assert "No dump yet today" in capsys.readouterr().out
