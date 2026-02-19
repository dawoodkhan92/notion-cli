# tests/test_dump.py
from unittest.mock import patch, MagicMock

def test_dump_creates_today_page_if_missing():
    import ntn
    mock_client = MagicMock()
    mock_config = {"api_key": "test", "brain_dump_page_id": "parent-id-123", "databases": {}}
    mock_client.search.return_value = {"results": []}
    mock_client.pages.create.return_value = {"id": "new-page-id"}

    args = MagicMock()
    args.text = "Test thought"

    with patch("ntn.load_config", return_value=mock_config):
        with patch("ntn.get_client", return_value=mock_client):
            ntn.cmd_dump(args)

    mock_client.pages.create.assert_called_once()
    kwargs = mock_client.pages.create.call_args[1]
    assert kwargs["parent"]["page_id"] == "parent-id-123"

def test_dump_appends_to_existing_page():
    import ntn
    from datetime import datetime
    mock_client = MagicMock()
    mock_config = {"api_key": "test", "brain_dump_page_id": "parent-id-123", "databases": {}}
    today = datetime.now().strftime("%d-%m-%Y")
    mock_client.search.return_value = {
        "results": [{"id": "existing-id", "parent": {"page_id": "parent-id-123"},
                     "properties": {"title": {"title": [{"plain_text": today}]}}}]
    }

    args = MagicMock()
    args.text = "Appending this"

    with patch("ntn.load_config", return_value=mock_config):
        with patch("ntn.get_client", return_value=mock_client):
            ntn.cmd_dump(args)

    mock_client.pages.create.assert_not_called()
    mock_client.blocks.children.append.assert_called_once()
