from shared.schemas.job import JobSubmitRequest


def test_job_submit_request_accepts_model_config_alias() -> None:
    payload = {
        "model_config": {"architecture": "resnet34", "num_classes": 5},
        "training_config": {"epochs": 2, "batch_size": 16},
        "name": "alias-check",
    }

    req = JobSubmitRequest.model_validate(payload)

    assert req.architecture_config.architecture == "resnet34"
    assert req.architecture_config.num_classes == 5

    dumped = req.model_dump(by_alias=True)
    assert "model_config" in dumped
    assert dumped["model_config"]["num_classes"] == 5


def test_job_submit_request_internal_field_not_reserved_name() -> None:
    fields = JobSubmitRequest.model_fields
    assert "architecture_config" in fields
    assert "model_config" not in fields
