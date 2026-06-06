from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_required_fixture_categories_exist():
    names=['normal_project','frontend_backend_mixed','express_next','django_fastapi','spring_laravel','go_rust','sourcemap_frontend','service_worker','graphql_ws','docker_k8s_ci','seed_mock_fixture','hidden_api','false_positive_negative','top_tier_info_app']
    missing=[n for n in names if not (ROOT/'tests/fixtures'/n).exists()]
    assert not missing
