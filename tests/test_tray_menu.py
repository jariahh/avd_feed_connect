"""build_menu: the tray's right-click menu layout (Favorites / Other desktops)."""

from avd_feed_connect.gui.tray_menu import (
    SEPARATOR, build_menu, build_accounts_menu, display_name)


def _res(rid, tenant, title="SessionDesktop", type="Desktop"):
    return {"id": rid, "title": title, "tenant": tenant, "type": type}


def _labels(items):
    return [i.get("label") for i in items]


def test_desktop_uses_workspace_name_remoteapp_uses_title():
    assert display_name(_res("a", "Contoso")) == "Contoso"
    assert display_name(_res("a", "Contoso", title="SSMS", type="RemoteApp")) == "SSMS"


def test_workspace_falls_back_to_publisher():
    assert display_name({"id": "a", "title": "SessionDesktop", "tenant": "",
                         "publisher": "Pub"}) == "Pub"


def test_no_favorites_is_a_flat_list_without_headers():
    items = build_menu([_res("a", "Dev"), _res("b", "Ops")], {}, include_footer=False)
    assert _labels(items) == ["Dev", "Ops"]
    # resource rows carry their actions as children, not a top-level action
    assert items[0]["action"] is None and items[0]["children"]
    assert items[-1]["children"][0]["action"] == ("connect", "b")


def test_favorites_group_on_top_then_other_desktops():
    items = build_menu([_res("a", "Dev"), _res("b", "Ops"), _res("c", "Qa")],
                       {}, include_footer=False, favorites=["b"])
    assert _labels(items) == ["★ Favorites", "Ops", "Other desktops", "Dev", "Qa"]
    assert not items[0]["enabled"] and not items[2]["enabled"]       # the two headers
    assert items[0]["action"] is None and items[2]["action"] is None


def test_favorites_without_others_omits_the_other_header():
    items = build_menu([_res("a", "Dev")], {}, include_footer=False, favorites=["a"])
    assert _labels(items) == ["★ Favorites", "Dev"]


def test_idle_resource_offers_connect_and_windowed():
    vm = build_menu([_res("a", "Dev")], {}, include_footer=False)[0]
    assert vm["label"] == "Dev"
    assert [(c["label"], c["action"]) for c in vm["children"]] == [
        ("Connect", ("connect", "a")), ("Connect (windowed)", ("connect-windowed", "a"))]


def test_connected_resource_offers_focus_and_disconnect():
    vm = build_menu([_res("a", "Dev")], {"a": {"state": "connected", "running": True}},
                    include_footer=False)[0]
    assert vm["label"] == "● Dev"
    assert [c["action"] for c in vm["children"]] == [("focus", "a"), ("disconnect", "a")]


def test_connecting_without_process_is_not_actionable():
    vm = build_menu([_res("a", "Dev")], {"a": {"state": "connecting", "running": False}},
                    include_footer=False)[0]
    assert vm["label"] == "○ Dev"
    assert [(c["label"], c["enabled"]) for c in vm["children"]] == [("Connecting…", False)]


def test_connecting_with_process_can_be_focused_or_cancelled():
    vm = build_menu([_res("a", "Dev")], {"a": {"state": "connecting", "running": True}},
                    include_footer=False)[0]
    assert [c["label"] for c in vm["children"]] == ["Connecting…", "Focus window", "Disconnect"]


def test_footer_and_empty_feed():
    items = build_menu([], {})
    assert items[0]["label"] == "No workspaces yet" and not items[0]["enabled"]
    assert items[1] == SEPARATOR
    assert [i["action"] for i in items[2:]] == [("refresh",), ("show",), ("quit",)]


def test_account_actions_keep_owner_with_identical_resource_ids():
    accounts = [{'id': 'a', 'upn': 'a@example.com', 'resources': [_res('same', 'Alpha')]},
                {'id': 'b', 'upn': 'b@example.com', 'resources': [_res('same', 'Beta')]}]
    menu = build_accounts_menu(accounts, {('a', 'same'): {'running': True, 'state': 'connected'}})
    assert menu[0]['label'] == 'a@example.com'
    assert menu[0]['children'][0]['children'][0]['action'] == ('focus', 'a', 'same')
    assert menu[1]['children'][0]['children'][0]['action'] == ('connect', 'b', 'same')


def test_removed_account_only_offers_running_session_actions():
    accounts = [{'id': 'a', 'upn': 'old@example.com', 'removed': True,
                 'resources': [_res('running', 'Running'), _res('idle', 'Idle')]}]
    menu = build_accounts_menu(accounts, {('a', 'running'): {'running': True, 'state': 'connected'}})
    assert [r['label'] for r in menu[0]['children']] == ['● Running']
    assert menu[0]['children'][0]['children'][1]['action'] == ('disconnect', 'a', 'running')


def test_favorites_flow_through_accounts_menu():
    accounts = [{'id': 'a', 'upn': 'a@x', 'resources': [_res('p', 'Dev'), _res('q', 'Ops')]}]
    menu = build_accounts_menu(accounts, {}, favorites=['q'])
    assert _labels(menu[0]['children']) == ['★ Favorites', 'Ops', 'Other desktops', 'Dev']
