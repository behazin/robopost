import pytest
from unittest.mock import patch, MagicMock

from sqlalchemy.exc import SQLAlchemyError

from common_utils.db import session_scope


@patch("common_utils.db.get_session")
def test_session_scope_rolls_back_on_exception(mock_get_session):
    """
    Tests that session_scope rolls back the session when an exception occurs.
    """
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    with pytest.raises(SQLAlchemyError):
        with session_scope():
            # Simulate an error during the transaction
            raise SQLAlchemyError("Something went wrong")

    mock_session.commit.assert_not_called()
    mock_session.rollback.assert_called_once()
    mock_session.close.assert_called_once()