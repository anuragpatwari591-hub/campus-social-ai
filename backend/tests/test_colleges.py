from app.database import Base
from app.models.geo import Country, Region, City, Institution, InstitutionAlias


def _seed_iit_kgp(db_session):
    country = Country(name="India", code="IND")
    db_session.add(country)
    db_session.flush()
    region = Region(name="West Bengal", country_id=country.id)
    db_session.add(region)
    db_session.flush()
    city = City(name="Kharagpur", region_id=region.id)
    db_session.add(city)
    db_session.flush()
    inst = Institution(name="Indian Institute of Technology Kharagpur", short_name="IIT Kharagpur", city_id=city.id, institution_type="IIT")
    db_session.add(inst)
    db_session.flush()
    db_session.add(InstitutionAlias(institution_id=inst.id, alias="IIT KGP"))
    db_session.commit()
    return inst


def _get_session():
    from tests.conftest import TestSessionLocal
    return TestSessionLocal()


def test_exact_search(client):
    db = _get_session()
    _seed_iit_kgp(db)
    db.close()

    resp = client.get("/api/colleges/search", params={"q": "Kharagpur"})
    assert resp.status_code == 200
    results = resp.json()
    assert any("Kharagpur" in r["name"] for r in results)


def test_alias_search_resolves_to_same_institution(client):
    db = _get_session()
    inst = _seed_iit_kgp(db)
    inst_id = inst.id
    db.close()

    resp = client.get("/api/colleges/search", params={"q": "IIT KGP"})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert results[0]["id"] == inst_id
    assert results[0]["matched_alias"] == "IIT KGP"


def test_fuzzy_search_handles_typo(client):
    db = _get_session()
    _seed_iit_kgp(db)
    db.close()

    resp = client.get("/api/colleges/search", params={"q": "Kharagpr"})  # typo
    assert resp.status_code == 200
    results = resp.json()
    assert any("Kharagpur" in r["name"] for r in results)


def test_search_no_match_returns_empty_or_closest(client):
    resp = client.get("/api/colleges/search", params={"q": "zzz_nonexistent_zzz"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
