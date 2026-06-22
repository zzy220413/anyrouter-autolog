from checkin import evaluate_check_in_success


def user_info(quota: float, used: float = 0.0) -> dict:
	return {'success': True, 'quota': quota, 'used_quota': used}


def test_api_success_without_balance_growth_is_not_effective_checkin():
	assert not evaluate_check_in_success(
		api_success=True,
		already_checked=False,
		user_info_before=user_info(100.0, 10.0),
		user_info_after=user_info(100.0, 10.0),
	)


def test_balance_growth_is_effective_checkin():
	assert evaluate_check_in_success(
		api_success=True,
		already_checked=False,
		user_info_before=user_info(100.0, 10.0),
		user_info_after=user_info(125.0, 10.0),
	)


def test_used_quota_growth_without_balance_growth_is_not_effective_checkin():
	assert not evaluate_check_in_success(
		api_success=True,
		already_checked=False,
		user_info_before=user_info(100.0, 10.0),
		user_info_after=user_info(100.0, 20.0),
	)


def test_explicit_already_checked_is_success_without_balance_growth():
	assert evaluate_check_in_success(
		api_success=True,
		already_checked=True,
		user_info_before=user_info(100.0, 10.0),
		user_info_after=user_info(100.0, 10.0),
	)
