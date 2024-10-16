from unittest import mock

import pytest
from lingqhandler import check_for_valid_token_or_exit


def test_check_for_valid_token_or_exit_wrong_input_type():
    with pytest.raises(NotImplementedError):
        check_for_valid_token_or_exit(3)


def test_check_for_valid_token_or_exit_invalid_token():
    with mock.patch("sys.exit") as mock_exit:
        check_for_valid_token_or_exit({"detail": "Invalid token."})
        mock_exit.assert_called_once()
