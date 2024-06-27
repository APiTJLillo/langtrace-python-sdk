import json
from langtrace_python_sdk.constants.instrumentation.cohere import APIS
from langtrace_python_sdk.constants.instrumentation.common import SERVICE_PROVIDERS
import pytest
import importlib
from langtrace_python_sdk.constants import LANGTRACE_SDK_NAME
from tests.utils import assert_response_format, assert_token_count
from importlib_metadata import version as v
from langtrace.trace_attributes import SpanAttributes


@pytest.mark.vcr
def test_cohere_chat(cohere_client, exporter):
    llm_model_value = "command"
    messages_value = "Tell me a story in 3 sentences or less?"
    preamble_value = "answer like a pirate"
    connectors = [{"id": "web-search"}]
    kwargs = {
        "model": llm_model_value,
        "message": messages_value,
        "preamble": preamble_value,
        "connectors": connectors,
        "temperature": 0.1,
        "chat_history": [
            {"role": "USER", "message": "Who discovered gravity?"},
            {
                "role": "CHATBOT",
                "message": "The man who is widely credited with discovering gravity is Sir Isaac Newton",
            },
        ],
    }
    res = cohere_client.chat(**kwargs)
    spans = exporter.get_finished_spans()
    cohere_span = spans[-1]
    assert cohere_span.name == APIS["CHAT_CREATE"]["METHOD"]
    attributes = cohere_span.attributes

    assert attributes.get(SpanAttributes.LANGTRACE_SDK_NAME.value) == LANGTRACE_SDK_NAME
    assert (
        attributes.get(SpanAttributes.LANGTRACE_SERVICE_NAME.value)
        == SERVICE_PROVIDERS["COHERE"]
    )
    assert attributes.get(SpanAttributes.LANGTRACE_SERVICE_TYPE.value) == "llm"
    assert attributes.get(SpanAttributes.LANGTRACE_SERVICE_VERSION.value) == v("cohere")
    assert attributes.get(SpanAttributes.LANGTRACE_VERSION.value) == v(
        LANGTRACE_SDK_NAME
    )
    assert attributes.get(SpanAttributes.LLM_URL.value) == APIS["CHAT_CREATE"]["URL"]
    assert (
        attributes.get(SpanAttributes.LLM_PATH.value) == APIS["CHAT_CREATE"]["ENDPOINT"]
    )
    assert attributes.get(SpanAttributes.LLM_REQUEST_MODEL.value) == llm_model_value
    assert attributes.get(SpanAttributes.LLM_REQUEST_TEMPERATURE.value) == kwargs.get(
        "temperature"
    )
    assert attributes.get(SpanAttributes.LLM_GENERATION_ID.value) == res.generation_id

    assert json.loads(attributes.get("llm_connectors")) == connectors
    assert (
        json.loads(attributes.get(SpanAttributes.LLM_PROMPTS.value))[-1]["content"]
        == messages_value
    )
    assert (
        json.loads(attributes.get(SpanAttributes.LLM_COMPLETIONS.value))[-1]["content"]
        == res.text
    )

    assert_token_count(attributes)
    assert_response_format(attributes)


@pytest.mark.vcr
def test_cohere_chat_streaming(cohere_client, exporter):
    llm_model_value = "command"
    messages_value = "Tell me a story in 3 sentences or less?"
    preamble_value = "answer like a pirate"
    connectors = [{"id": "web-search"}]
    kwargs = {
        "model": llm_model_value,
        "message": messages_value,
        "preamble": preamble_value,
        "connectors": connectors,
        "temperature": 0.1,
        "chat_history": [
            {"role": "USER", "message": "Who discovered gravity?"},
            {
                "role": "CHATBOT",
                "message": "The man who is widely credited with discovering gravity is Sir Isaac Newton",
            },
        ],
    }

    res = cohere_client.chat_stream(**kwargs)

    chunks_count = 0
    streamed_response = ""
    for chunk in res:
        if chunk.event_type == "text-generation":
            streamed_response += chunk.text
        chunks_count += 1

    spans = exporter.get_finished_spans()
    cohere_span = spans[-1]
    assert cohere_span.name == APIS["CHAT_STREAM"]["METHOD"]
    attributes = cohere_span.attributes

    assert attributes.get(SpanAttributes.LANGTRACE_SDK_NAME.value) == LANGTRACE_SDK_NAME
    assert (
        attributes.get(SpanAttributes.LANGTRACE_SERVICE_NAME.value)
        == SERVICE_PROVIDERS["COHERE"]
    )
    assert attributes.get(SpanAttributes.LANGTRACE_SERVICE_TYPE.value) == "llm"
    assert attributes.get(SpanAttributes.LANGTRACE_SERVICE_VERSION.value) == v("cohere")
    assert attributes.get(SpanAttributes.LANGTRACE_VERSION.value) == v(
        LANGTRACE_SDK_NAME
    )
    assert attributes.get(SpanAttributes.LLM_URL.value) == APIS["CHAT_STREAM"]["URL"]
    assert (
        attributes.get(SpanAttributes.LLM_PATH.value) == APIS["CHAT_STREAM"]["ENDPOINT"]
    )
    assert attributes.get(SpanAttributes.LLM_REQUEST_MODEL.value) == llm_model_value
    assert attributes.get(SpanAttributes.LLM_REQUEST_TEMPERATURE.value) == kwargs.get(
        "temperature"
    )
    assert attributes.get(SpanAttributes.LLM_IS_STREAMING.value) is True

    assert json.loads(attributes.get("llm_connectors")) == connectors
    assert (
        json.loads(attributes.get(SpanAttributes.LLM_PROMPTS.value))[-1]["content"]
        == messages_value
    )
    events = cohere_span.events
    assert events[-1].name == "stream.end"
    assert len(events) - 2 == chunks_count
    assert (
        json.loads(attributes.get(SpanAttributes.LLM_COMPLETIONS.value))[-1]["content"]
        == streamed_response
    )

    assert_token_count(attributes)
    assert_response_format(attributes)
