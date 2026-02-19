# tests/test_posts.py
from unittest.mock import patch, MagicMock

def test_post_add_creates_row():
    import ntn
    mock_client = MagicMock()
    mock_config = {"api_key": "test", "databases": {"posts": "posts-db-id"}}
    mock_client.pages.create.return_value = {"id": "new-row"}

    args = MagicMock()
    args.url = "https://linkedin.com/posts/example"
    args.note = "Great hook"
    args.source = "LinkedIn"

    with patch("ntn.load_config", return_value=mock_config):
        with patch("ntn.get_client", return_value=mock_client):
            ntn.cmd_post_add(args)

    kwargs = mock_client.pages.create.call_args[1]
    assert kwargs["parent"]["database_id"] == "posts-db-id"

def test_post_add_no_db_configured(capsys):
    import ntn
    args = MagicMock()
    args.url = "https://linkedin.com/posts/example"
    args.note = ""
    args.source = "LinkedIn"
    with patch("ntn.load_config", return_value={"api_key": "t", "databases": {}}):
        with patch("ntn.get_client", return_value=MagicMock()):
            ntn.cmd_post_add(args)
    assert "No posts database configured" in capsys.readouterr().out

def test_post_list_prints_results(capsys):
    import ntn
    mock_client = MagicMock()
    mock_config = {"api_key": "test", "databases": {"posts": "posts-db-id"}}
    mock_client.databases.query.return_value = {
        "results": [{
            "properties": {
                "URL": {"url": "https://linkedin.com/posts/foo"},
                "Notes": {"rich_text": [{"plain_text": "Good post"}]},
                "Source": {"select": {"name": "LinkedIn"}},
                "Date": {"date": {"start": "2026-02-19"}}
            }
        }]
    }
    args = MagicMock()
    args.limit = 10
    with patch("ntn.load_config", return_value=mock_config):
        with patch("ntn.get_client", return_value=mock_client):
            ntn.cmd_post_list(args)
    assert "linkedin.com/posts/foo" in capsys.readouterr().out
