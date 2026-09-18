import os
from pathlib import Path

from app.schema.repository import SchemaRepository


def test_cache_is_bound_to_source_identity(tmp_path: Path) -> None:
    first = tmp_path / 'first.sql'
    second = tmp_path / 'second.sql'
    cache = tmp_path / 'orm.json'
    first.write_text('CREATE TABLE first_model (id integer PRIMARY KEY);', encoding='utf-8')
    second.write_text('CREATE TABLE second_model (id integer PRIMARY KEY);', encoding='utf-8')
    assert set(SchemaRepository(first, cache).load_or_build_orm_schema().models) == {'first.model'}
    assert set(SchemaRepository(second, cache).load_or_build_orm_schema().models) == {'second.model'}
    assert set(SchemaRepository(first, cache).load_or_build_orm_schema().models) == {'first.model'}


def test_cache_detects_content_change_with_unchanged_mtime(tmp_path: Path) -> None:
    source = tmp_path / 'source.sql'
    source.write_text('CREATE TABLE first_model (id integer PRIMARY KEY);', encoding='utf-8')
    repository = SchemaRepository(source, tmp_path / 'orm.json')
    repository.load_or_build_orm_schema()
    original = source.stat()
    source.write_text('CREATE TABLE other_model (id integer PRIMARY KEY);', encoding='utf-8')
    os.utime(source, ns=(original.st_atime_ns, original.st_mtime_ns))
    assert set(repository.load_or_build_orm_schema().models) == {'other.model'}


def test_valid_cache_is_reused(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / 'source.sql'
    source.write_text('CREATE TABLE first_model (id integer PRIMARY KEY);', encoding='utf-8')
    repository = SchemaRepository(source, tmp_path / 'orm.json')
    repository.load_or_build_orm_schema()

    def unexpected_build():
        raise AssertionError('Fresh cache should not rebuild')

    monkeypatch.setattr(repository, 'build_orm_schema', unexpected_build)
    assert set(repository.load_or_build_orm_schema().models) == {'first.model'}


def test_modified_cache_artifact_is_rebuilt(tmp_path: Path) -> None:
    source = tmp_path / 'source.sql'
    source.write_text('CREATE TABLE first_model (id integer PRIMARY KEY);', encoding='utf-8')
    repository = SchemaRepository(source, tmp_path / 'orm.json')
    repository.load_or_build_orm_schema()
    repository.orm_schema_path.write_text('{"models": {}}', encoding='utf-8')
    assert set(repository.load_or_build_orm_schema().models) == {'first.model'}
