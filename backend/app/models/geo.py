"""
Global college directory hierarchy:

    Country -> Region (state/province) -> City -> Institution -> Campus

An Institution can have multiple Campuses (e.g. IIT campuses are each their
own institution here, but a private university with a main + satellite
campus would use this). InstitutionAlias lets "IIT KGP", "IIT Kharagpur" and
"Indian Institute of Technology Kharagpur" all resolve to one Institution.
"""
from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)  # ISO-3166 alpha-2/3

    regions: Mapped[list["Region"]] = relationship(back_populates="country", cascade="all, delete-orphan")


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), nullable=False)

    country: Mapped["Country"] = relationship(back_populates="regions")
    cities: Mapped[list["City"]] = relationship(back_populates="region", cascade="all, delete-orphan")


class City(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id"), nullable=False)

    region: Mapped["Region"] = relationship(back_populates="cities")
    institutions: Mapped[list["Institution"]] = relationship(back_populates="city")


class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    short_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), nullable=False)
    institution_type: Mapped[str] = mapped_column(String(50), default="university")  # IIT, NIT, private, etc.
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(default=False)

    city: Mapped["City"] = relationship(back_populates="institutions")
    aliases: Mapped[list["InstitutionAlias"]] = relationship(back_populates="institution", cascade="all, delete-orphan")
    campuses: Mapped[list["Campus"]] = relationship(back_populates="institution", cascade="all, delete-orphan")


class InstitutionAlias(Base):
    """Alternate names/abbreviations used to resolve fuzzy search, e.g. 'IIT KGP'."""
    __tablename__ = "institution_aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id"), nullable=False)
    alias: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    institution: Mapped["Institution"] = relationship(back_populates="aliases")


class Campus(Base):
    """A specific physical campus belonging to an institution (default: 'Main Campus')."""
    __tablename__ = "campuses"

    id: Mapped[int] = mapped_column(primary_key=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), default="Main Campus")
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)

    institution: Mapped["Institution"] = relationship(back_populates="campuses")
