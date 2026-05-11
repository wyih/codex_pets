import json
import unittest

from shinsekai_pet_host.backends import BackendProviderRegistry
from shinsekai_pet_host.codex_cli import CodexCommandBuilder, CodexResponseParser
from shinsekai_pet_host.openai_compatible import build_chat_request, parse_chat_response


class BackendTests(unittest.TestCase):
    def test_backend_registry_has_default_providers(self) -> None:
        registry = BackendProviderRegistry.default()
        self.assertEqual(registry.ids(), ["codex-cli", "openai-compatible"])

    def test_codex_chat_and_work_commands(self) -> None:
        builder = CodexCommandBuilder(codex_bin="codex")
        self.assertEqual(
            builder.chat("hello").args[:4],
            ["codex", "exec", "--ephemeral", "--skip-git-repo-check"],
        )
        self.assertEqual(
            builder.work("hello", "/tmp/work").args[:4],
            ["codex", "exec", "-C", "/tmp/work"],
        )

    def test_codex_jsonl_parser_gets_last_agent_message(self) -> None:
        text = (
            '{"type":"message","role":"assistant","content":"hi"}\n'
            '{"type":"message","role":"assistant","content":"done"}\n'
        )
        self.assertEqual(CodexResponseParser.parse(text), "done")

    def test_openai_compatible_request_and_response(self) -> None:
        request = build_chat_request("gpt-test", "system", "hello")
        self.assertEqual(request["model"], "gpt-test")
        body = {"choices": [{"message": {"content": "reply"}}]}
        self.assertEqual(parse_chat_response(json.dumps(body)), "reply")


if __name__ == "__main__":
    unittest.main()

