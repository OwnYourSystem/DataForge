from conftest import LESSON, MODEL


def make_project(client, headers):
    response = client.post("/v1/projects", json={"lesson_id": LESSON}, headers=headers)
    assert response.status_code == 200
    return response.json()["id"]


def test_requests_without_identity_are_rejected(client):
    assert client.get("/v1/lessons").status_code == 401
    assert client.get("/healthz").status_code == 200


def test_lesson_has_instructions_but_no_solution(client, alice, solution):
    body = client.get(f"/v1/lessons/{LESSON}", headers=alice).json()
    assert body["editable_files"] == [MODEL]
    assert "LAB-001" in body["instructions"]
    assert "upper(trim(country))" not in str(body)


def test_project_starts_with_starter_file_and_is_idempotent(client, alice, solution):
    first = make_project(client, alice)
    assert make_project(client, alice) == first
    files = client.get(f"/v1/projects/{first}/files", headers=alice).json()
    assert [f["path"] for f in files] == [MODEL]
    assert files[0]["content"] != solution


def test_saved_file_persists(client, alice, solution):
    project = make_project(client, alice)
    put = client.put(
        f"/v1/projects/{project}/files/{MODEL}", json={"content": solution}, headers=alice
    )
    assert put.status_code == 200
    files = client.get(f"/v1/projects/{project}/files", headers=alice).json()
    assert files[0]["content"] == solution


def test_only_approved_paths_can_be_written(client, alice):
    project = make_project(client, alice)
    for path in ["profiles.yml", "macros/x.sql", "../x.sql", "models/staging/_staging.yml"]:
        response = client.put(
            f"/v1/projects/{project}/files/{path}", json={"content": "select 1"}, headers=alice
        )
        assert response.status_code in (403, 404), path


def test_token_leak_jinja_is_rejected_on_save(client, alice):
    project = make_project(client, alice)
    response = client.put(
        f"/v1/projects/{project}/files/{MODEL}",
        json={"content": "select '{{ env_var('DBX_TOKEN') }}' as t"},
        headers=alice,
    )
    assert response.status_code == 422


def test_learner_cannot_reach_another_learners_project(client, alice, bob):
    project = make_project(client, alice)
    assert client.get(f"/v1/projects/{project}/files", headers=bob).status_code == 404
    assert client.get(f"/v1/projects/{project}", headers=bob).status_code == 404
    put = client.put(
        f"/v1/projects/{project}/files/{MODEL}", json={"content": "select 1"}, headers=bob
    )
    assert put.status_code == 404
    run = client.post(
        f"/v1/projects/{project}/executions", json={"operation_id": "dbt_build"}, headers=bob
    )
    assert run.status_code == 404
    mine = client.post(
        f"/v1/projects/{project}/executions", json={"operation_id": "dbt_build"}, headers=alice
    ).json()
    assert client.get(f"/v1/executions/{mine['id']}", headers=bob).status_code == 404


def test_unknown_operation_is_rejected(client, alice):
    project = make_project(client, alice)
    response = client.post(
        f"/v1/projects/{project}/executions",
        json={"operation_id": "dbt run-operation x; rm -rf /"},
        headers=alice,
    )
    assert response.status_code == 422


def test_one_active_execution_for_each_user(client, alice, bob):
    project = make_project(client, alice)
    url = f"/v1/projects/{project}/executions"
    assert client.post(url, json={"operation_id": "dbt_build"}, headers=alice).status_code == 202
    assert client.post(url, json={"operation_id": "dbt_build"}, headers=alice).status_code == 409
    other = make_project(client, bob)
    response = client.post(
        f"/v1/projects/{other}/executions", json={"operation_id": "dbt_build"}, headers=bob
    )
    assert response.status_code == 202
