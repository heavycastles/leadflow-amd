import pytest

from app.leads import LeadStore, normalize_email, normalize_phone, score_lead


def test_normalize_email():
    assert normalize_email("  Foo@Example.COM ") == "foo@example.com"
    assert normalize_email("") is None
    assert normalize_email(None) is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("+998 (90) 123-45-67", "+998901234567"), ("90 123 45 67", "901234567"), ("12-34", None)],
)
def test_normalize_phone(raw, expected):
    assert normalize_phone(raw) == expected


def test_score_is_bounded_and_rewards_intent():
    low = score_lead("web", None, has_email=True, has_phone=False)
    high = score_lead("referral", "Need a price quote today, urgent", True, True)
    assert 0 <= low < high <= 100


def test_dedupe_by_email_and_phone():
    store = LeadStore()
    first, created = store.add("Ann", "web", email="ann@example.com")
    assert created
    again, created = store.add("Ann B", "whatsapp", email="ANN@example.com")
    assert not created and again.id == first.id and again.duplicates == 1
    by_phone, _ = store.add("Bob", "phone", phone="+1 555 000 1111")
    same_phone, created = store.add("Bobby", "web", phone="+15550001111")
    assert not created and same_phone.id == by_phone.id


def test_requires_contact():
    with pytest.raises(ValueError):
        LeadStore().add("Nobody", "web")


def test_unknown_source_becomes_other_and_list_sorted():
    store = LeadStore()
    store.add("A", "carrier-pigeon", email="a@example.com")
    store.add("B", "referral", email="b@example.com", phone="+15550002222", message="demo")
    leads = store.list()
    assert leads[0].name == "B"
    assert leads[1].source == "other"
    assert store.list(min_score=101) == []
