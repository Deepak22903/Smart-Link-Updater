from backend.app import push_notifications


def test_should_cleanup_token_for_senderid_mismatch():
    assert push_notifications._should_cleanup_token_for_error("SenderId mismatch") is True
    assert push_notifications._should_cleanup_token_for_error("sender id mismatch") is True


def test_should_cleanup_token_for_unregistered_patterns():
    assert push_notifications._should_cleanup_token_for_error("Requested entity was not found") is True
    assert push_notifications._should_cleanup_token_for_error("Not registered") is True


def test_should_not_cleanup_token_for_temporary_errors():
    assert push_notifications._should_cleanup_token_for_error("Quota exceeded") is False
    assert push_notifications._should_cleanup_token_for_error("Internal server error") is False
