import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from chatopsllm_api.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get('/health')

    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_generate_llm_response_wraps_provider_errors() -> None:
    from chatopsllm_api.llms.litellm import generate_llm_response

    with patch('chatopsllm_api.llms.litellm.client.chat.completions.create', new_callable=AsyncMock) as create:
        create.side_effect = RuntimeError('provider unavailable')

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(generate_llm_response(prompt='hello', model='test-model'))

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == 'Internal Server Error'


def test_generate_llm_response_parses_json_prompt_response() -> None:
    from chatopsllm_api.llms.litellm import generate_llm_response
    from chatopsllm_api.schemas.prompt_schema import PromptType

    message = MagicMock(content='{"body":"done","final_prompt":"improved"}')
    completion = MagicMock(choices=[MagicMock(message=message)])

    with patch('chatopsllm_api.llms.litellm.client.chat.completions.create', new_callable=AsyncMock) as create:
        create.return_value = completion

        response = asyncio.run(
            generate_llm_response(
                prompt='hello',
                model='test-model',
                prompt_type=PromptType.ENHANCE_PROMPT,
                json_mode=True,
            )
        )

    assert response.final_prompt == 'improved'
