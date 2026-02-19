# tests/test_search.py
from unittest.mock import patch, MagicMock

def test_search_prints_results(capsys):
    import ntn
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "results": [{"id": "p1", "object": "page", "url": "https://notion.so/test",
                     "properties": {"title": {"title": [{"plain_text": "My Test Page"}]}}}]
    }
    args = MagicMock()
    args.query = "test"
    with patch("ntn.load_config", return_value={"api_key": "t", "databases": {}}):
        with patch("ntn.get_client", return_value=mock_client):
            ntn.cmd_search(args)
    assert "My Test Page" in capsys.readouterr().out

def test_read_prints_content(capsys):
    import ntn
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "results": [{"id": "p1", "properties": {"title": {"title": [{"plain_text": "My Page"}]}}}]
    }
    mock_client.blocks.children.list.return_value = {
        "results": [{"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Content here"}]}}]
    }
    args = MagicMock()
    args.title = "My Page"
    with patch("ntn.load_config", return_value={"api_key": "t", "databases": {}}):
        with patch("ntn.get_client", return_value=mock_client):
            ntn.cmd_read(args)
    assert "Content here" in capsys.readouterr().out
