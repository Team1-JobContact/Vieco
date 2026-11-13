from src.models import Industry, Province


def test_employer_form_catalog_returns_only_active_database_options(client, db_session):
    industry = Industry(name="Công nghệ", slug="cong-nghe")
    province = Province(name="Hà Nội", code="HN")
    db_session.add_all([
        industry, province,
        Industry(name="Ngành ẩn", slug="an", is_active=False),
        Province(name="Tỉnh ẩn", code="AN", is_active=False),
    ])
    db_session.commit()

    response = client.get("/api/v1/categories")
    assert response.status_code == 200
    assert response.json() == {
        "industries": [{"id": industry.id, "name": "Công nghệ"}],
        "provinces": [{"id": province.id, "name": "Hà Nội"}],
    }
