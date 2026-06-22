from types import SimpleNamespace

import pytest

import checkin
from checkin import build_playwright_cookies, check_in_account
from utils.config import AccountConfig


def test_build_playwright_cookies_normalizes_cookie_domain_and_path():
	cookies = build_playwright_cookies({'session': 'abc', 'new-api-user': 123}, 'https://anyrouter.top')

	assert cookies == [
		{
			'name': 'session',
			'value': 'abc',
			'domain': 'anyrouter.top',
			'path': '/',
			'secure': True,
			'sameSite': 'Lax',
		},
		{
			'name': 'new-api-user',
			'value': '123',
			'domain': 'anyrouter.top',
			'path': '/',
			'secure': True,
			'sameSite': 'Lax',
		},
	]


@pytest.mark.asyncio
async def test_anyrouter_browser_flow_runs_between_before_and_after_balance_checks(monkeypatch):
	calls = []

	class FakeCookies(dict):
		def update(self, value):
			calls.append(('client_cookies_update', dict(value)))
			super().update(value)

	class FakeClient:
		def __init__(self, *args, **kwargs):
			self.cookies = FakeCookies()

		def close(self):
			calls.append(('client_close',))

	provider_config = SimpleNamespace(
		domain='https://anyrouter.top',
		login_path='/login',
		user_info_path='/api/user/self',
		api_user_key='new-api-user',
		browser_check_in_paths=['/'],
		needs_waf_cookies=lambda: False,
		needs_browser_check_in=lambda: True,
		needs_manual_check_in=lambda: True,
	)
	account = AccountConfig(cookies={'session': 'abc'}, api_user='uid', provider='anyrouter', name='AnyRouter')
	app_config = SimpleNamespace(get_provider=lambda _provider: provider_config)

	async def fake_prepare_cookies(account_name, provider_config, user_cookies):
		calls.append(('prepare', account_name, dict(user_cookies)))
		return {'session': 'abc'}

	async def fake_trigger_browser_login_checkin(account_name, provider_config, cookies):
		calls.append(('browser_flow', account_name, dict(cookies)))
		return {'session': 'abc', 'acw_tc': 'waf'}

	user_infos = [
		{'success': True, 'quota': 10.0, 'used_quota': 0.0, 'display': 'before'},
		{'success': True, 'quota': 35.0, 'used_quota': 0.0, 'display': 'after'},
	]

	def fake_get_user_info(*args, **kwargs):
		info = user_infos.pop(0)
		calls.append(('user_info', info['quota']))
		return info

	def fail_if_sign_in_api_is_called(*args, **kwargs):
		raise AssertionError('AnyRouter browser flow should not call /api/user/sign_in')

	monkeypatch.setattr(checkin, 'prepare_cookies', fake_prepare_cookies)
	monkeypatch.setattr(checkin, 'trigger_browser_login_checkin', fake_trigger_browser_login_checkin)
	monkeypatch.setattr(checkin, 'get_user_info', fake_get_user_info)
	monkeypatch.setattr(checkin, 'execute_check_in', fail_if_sign_in_api_is_called)
	monkeypatch.setattr(checkin.httpx, 'Client', FakeClient)

	success, before, after = await check_in_account(account, 0, app_config)

	assert success is True
	assert before['quota'] == 10.0
	assert after['quota'] == 35.0
	assert [call[0] for call in calls] == [
		'prepare',
		'client_cookies_update',
		'user_info',
		'browser_flow',
		'client_cookies_update',
		'user_info',
		'client_close',
	]
