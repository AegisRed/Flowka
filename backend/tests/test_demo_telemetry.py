from app.services.telemetry import DemoTelemetry


async def test_demo_telemetry_has_warning_lag_consumer() -> None:
    telemetry = DemoTelemetry()

    snapshot = await telemetry.snapshot()

    assert snapshot.overview.topic_count == len(snapshot.topics)
    assert any(group.group_id == "slow-consumer" for group in snapshot.consumer_groups)
    assert any(group.lag > 0 for group in snapshot.consumer_groups)


async def test_demo_messages_are_limited() -> None:
    telemetry = DemoTelemetry()

    messages = await telemetry.messages("orders.created", limit=3)

    assert len(messages) == 3
    assert messages[0].topic == "orders.created"

