"""
Seeds the database with:
  1. The global college directory (countries/regions/cities/institutions/campuses/aliases)
  2. A handful of demo accounts (admin, moderator, students) and sample
     content (tea posts, polls, communities, events, opportunities,
     marketplace listings) so the platform isn't empty on first run.

Run from the backend virtualenv:
    cd backend && source .venv/bin/activate
    python ../seed_data/seed.py
"""
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from institutions import INSTITUTIONS, COUNTRY_CODES  # noqa: E402

from app.database import SessionLocal, engine, Base  # noqa: E402
import app.models  # noqa: E402, F401
from app.models.geo import Country, Region, City, Institution, InstitutionAlias, Campus  # noqa: E402
from app.models.user import User, UserInterest, UserRole  # noqa: E402
from app.models.content import Post, Poll, PollOption, TeaCategory  # noqa: E402
from app.models.social import Community, CommunityMember  # noqa: E402
from app.models.campus_life import Event, Opportunity, MarketplaceListing  # noqa: E402
from app.auth.security import hash_password  # noqa: E402
from app.services.anonymous_identity import generate_anonymous_profile  # noqa: E402


def get_or_create_country(db, name: str) -> Country:
    country = db.query(Country).filter_by(name=name).first()
    if not country:
        country = Country(name=name, code=COUNTRY_CODES.get(name, name[:3].upper()))
        db.add(country)
        db.flush()
    return country


def get_or_create_region(db, country: Country, name: str) -> Region:
    region = db.query(Region).filter_by(name=name, country_id=country.id).first()
    if not region:
        region = Region(name=name, country_id=country.id)
        db.add(region)
        db.flush()
    return region


def get_or_create_city(db, region: Region, name: str) -> City:
    city = db.query(City).filter_by(name=name, region_id=region.id).first()
    if not city:
        city = City(name=name, region_id=region.id)
        db.add(city)
        db.flush()
    return city


def seed_institutions(db) -> dict[str, Institution]:
    print(f"Seeding {len(INSTITUTIONS)} institutions...")
    by_short_name = {}
    for name, short_name, itype, country_name, region_name, city_name, aliases in INSTITUTIONS:
        if db.query(Institution).filter_by(name=name).first():
            continue
        country = get_or_create_country(db, country_name)
        region = get_or_create_region(db, country, region_name)
        city = get_or_create_city(db, region, city_name)

        institution = Institution(
            name=name, short_name=short_name, city_id=city.id,
            institution_type=itype, is_verified=True,
            description=f"{name} is part of the seeded global college directory.",
        )
        db.add(institution)
        db.flush()
        db.add(Campus(institution_id=institution.id, name="Main Campus"))
        for alias in aliases:
            db.add(InstitutionAlias(institution_id=institution.id, alias=alias))
        by_short_name[short_name] = institution
    db.commit()
    print("Institutions seeded.")
    return by_short_name


def seed_demo_accounts(db, iem_campus_id: int) -> dict[str, User]:
    print("Seeding demo accounts...")
    demo_users = [
        ("admin@campus.ai", "Admin12345", "Platform Admin", "admin", UserRole.ADMIN, ["management"]),
        ("mod@campus.ai", "Moderate123", "Moderator One", "mod_priya", UserRole.MODERATOR, ["community"]),
        ("aarav@campus.ai", "Student123", "Aarav Sharma", "aarav_s", UserRole.STUDENT, ["coding", "gaming", "music"]),
        ("diya@campus.ai", "Student123", "Diya Verma", "diya_v", UserRole.STUDENT, ["coding", "photography", "startups"]),
        ("rohan@campus.ai", "Student123", "Rohan Das", "rohan_d", UserRole.STUDENT, ["sports", "cricket", "fitness"]),
    ]
    created = {}
    for email, password, full_name, username, role, interests in demo_users:
        existing = db.query(User).filter_by(email=email).first()
        if existing:
            created[username] = existing
            continue
        user = User(
            email=email, hashed_password=hash_password(password), full_name=full_name,
            username=username, role=role, campus_id=iem_campus_id if role == UserRole.STUDENT else None,
            year_of_study=2 if role == UserRole.STUDENT else None,
            is_discoverable=True,
        )
        db.add(user)
        db.flush()
        generate_anonymous_profile(db, user)
        for interest in interests:
            db.add(UserInterest(user_id=user.id, interest=interest))
        created[username] = user
    db.commit()
    print("Demo accounts ready: " + ", ".join(f"{u.email}/{'<see script>'}" for u in created.values()))
    return created


def seed_demo_content(db, users: dict[str, User], campus_id: int):
    print("Seeding demo content...")
    aarav, diya, rohan = users["aarav_s"], users["diya_v"], users["rohan_d"]

    if not db.query(Post).first():
        db.add(Post(author_id=aarav.id, campus_id=campus_id, is_anonymous=False, category=TeaCategory.CAMPUS,
                     text="Hackathon this weekend is going to be huge! Who's forming teams?"))
        db.add(Post(author_id=diya.id, campus_id=campus_id, is_anonymous=True, category=TeaCategory.CONFESSION,
                     text="I may have fallen asleep in the middle of a viva today... send help."))
        db.add(Post(author_id=rohan.id, campus_id=campus_id, is_anonymous=True, category=TeaCategory.FUNNY,
                     text="Canteen samosa prices just doubled and nobody is talking about it."))

        poll_post = Post(author_id=aarav.id, campus_id=campus_id, is_anonymous=True, category=TeaCategory.QUESTIONS,
                          text="Quick poll for campus foodies:")
        db.add(poll_post)
        db.flush()
        poll = Poll(post_id=poll_post.id, question="Best campus food?")
        db.add(poll)
        db.flush()
        for opt in ["Canteen", "Food Court", "Cafe", "Outside Campus"]:
            db.add(PollOption(poll_id=poll.id, text=opt))

    if not db.query(Community).first():
        coding = Community(name="Coding Club", description="For students who love building things.", category="coding", campus_id=campus_id, created_by=aarav.id)
        gaming = Community(name="Gamers United", description="Casual and competitive gaming.", category="gaming", campus_id=campus_id, created_by=rohan.id)
        db.add_all([coding, gaming])
        db.flush()
        db.add(CommunityMember(community_id=coding.id, user_id=aarav.id, role="owner"))
        db.add(CommunityMember(community_id=coding.id, user_id=diya.id))
        db.add(CommunityMember(community_id=gaming.id, user_id=rohan.id, role="owner"))

    if not db.query(Event).first():
        now = datetime.now(timezone.utc)
        db.add(Event(campus_id=campus_id, created_by=aarav.id, title="Annual Tech Fest",
                      description="A weekend of hackathons, workshops and live music.", category="fest",
                      location="Main Auditorium", starts_at=now + timedelta(days=5), ends_at=now + timedelta(days=7)))
        db.add(Event(campus_id=campus_id, created_by=diya.id, title="AI/ML Workshop",
                      description="Hands-on workshop on building your first ML model.", category="workshop",
                      location="CS Lab 3", starts_at=now + timedelta(days=2), ends_at=now + timedelta(days=2, hours=3)))

    if not db.query(Opportunity).first():
        db.add(Opportunity(posted_by=diya.id, title="Frontend Intern", opportunity_type="internship",
                            organization="StartupXYZ", location="Remote", apply_url="https://example.com/apply",
                            description="3-month internship building React dashboards.",
                            deadline=datetime.now(timezone.utc) + timedelta(days=14)))

    if not db.query(MarketplaceListing).first():
        db.add(MarketplaceListing(seller_id=rohan.id, campus_id=campus_id, title="Scientific Calculator (Casio fx-991ES)",
                                   description="Barely used, all functions working.", category="electronics", price=450))

    db.commit()
    print("Demo content seeded.")


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_institutions(db)
        iem = db.query(Institution).filter_by(short_name="IEM Kolkata").first()
        iem_campus = db.query(Campus).filter_by(institution_id=iem.id).first()
        users = seed_demo_accounts(db, iem_campus.id)
        seed_demo_content(db, users, iem_campus.id)
        print("\nSeed complete. Demo login credentials:")
        print("  Admin:     admin@campus.ai / Admin12345")
        print("  Moderator: mod@campus.ai / Moderate123")
        print("  Student:   aarav@campus.ai / Student123")
    finally:
        db.close()


if __name__ == "__main__":
    main()
