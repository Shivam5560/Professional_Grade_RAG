from pathlib import Path
import shlex
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = REPOSITORY_ROOT / "backend" / "Dockerfile"
JENKINSFILE = REPOSITORY_ROOT / "Jenkinsfile"
CONTRACT_COMMAND = "python3 -m unittest discover -s scripts/ci -p 'test_*.py' -v"
EXPECTED_CONTRACT_STAGE_LINES = [
    "stage('CI Contract Tests') {",
    "steps {",
    f'sh "{CONTRACT_COMMAND}"',
    "}",
    "}",
]
EXPECTED_BACKEND_BUILD = [
    "docker",
    "build",
    "--label",
    "org.opencontainers.image.revision=${SOURCE_COMMIT}",
    "--label",
    "org.opencontainers.image.source=${REPO_URL}",
    "--tag",
    "nexusmind-backend:${IMAGE_TAG}",
    "backend",
]
EXPECTED_BACKEND_SMOKE = [
    "docker",
    "run",
    "--rm",
    "--network",
    "none",
    "--read-only",
    "--cap-drop=ALL",
    "--security-opt",
    "no-new-privileges",
    "--entrypoint",
    "gunicorn",
    "nexusmind-backend:${IMAGE_TAG}",
    "--version",
]
EXPECTED_FRONTEND_BUILD = [
    "docker",
    "build",
    "--label",
    "org.opencontainers.image.revision=${SOURCE_COMMIT}",
    "--label",
    "org.opencontainers.image.source=${REPO_URL}",
    "--tag",
    "nexusmind-frontend:${IMAGE_TAG}",
    "frontend",
]


class BackendDockerfileContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dockerfile = DOCKERFILE.read_text(encoding="utf-8")
        cls.pipeline = JENKINSFILE.read_text(encoding="utf-8")

    @staticmethod
    def _stage_block(pipeline: str, stage_name: str, next_stage_name: str) -> str:
        start = pipeline.index(f"stage('{stage_name}')")
        end = pipeline.index(f"stage('{next_stage_name}')", start)
        return pipeline[start:end]

    @classmethod
    def _contract_stage_lines(cls, pipeline: str) -> list[str]:
        stage = cls._stage_block(pipeline, "CI Contract Tests", "Backend Tests")
        return [line.strip() for line in stage.splitlines() if line.strip()]

    @classmethod
    def _docker_build_commands(cls, pipeline: str) -> list[list[str]]:
        stage = cls._stage_block(
            pipeline,
            "Build Docker Images",
            "Package Deployment Artifacts",
        )
        shell_marker = "sh '''"
        shell_start = stage.index(shell_marker) + len(shell_marker)
        shell_end = stage.index("'''", shell_start)
        shell_body = stage[shell_start:shell_end]

        commands: list[list[str]] = []
        command_parts: list[str] = []
        for raw_line in shell_body.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.endswith("\\"):
                command_parts.append(line[:-1].rstrip())
                continue
            command_parts.append(line)
            commands.append(shlex.split(" ".join(command_parts)))
            command_parts = []

        if command_parts:
            raise AssertionError("Jenkins shell block ends with an incomplete command")
        return commands

    def test_dependency_install_is_fail_fast_and_tolerates_slow_downloads(self) -> None:
        install_start = self.dockerfile.index("RUN uv venv /opt/venv")
        cleanup_start = self.dockerfile.index("RUN (find /opt/venv", install_start)
        install_block = self.dockerfile[install_start:cleanup_start]

        self.assertIn("ENV UV_HTTP_TIMEOUT=300", self.dockerfile)
        self.assertNotIn("|| true", install_block)
        expected_install = "\n".join(
            (
                "RUN uv venv /opt/venv && \\",
                "    uv pip install --no-cache --python /opt/venv -r requirements.txt && \\",
                "    test -x /opt/venv/bin/gunicorn",
            )
        )
        self.assertIn(expected_install, install_block)

    def test_optional_cleanup_cannot_mask_dependency_install_failure(self) -> None:
        cleanup_start = self.dockerfile.index("RUN (find /opt/venv")
        cleanup_end = self.dockerfile.index("\n\n", cleanup_start)
        cleanup_block = self.dockerfile[cleanup_start:cleanup_end]

        self.assertNotIn("uv pip install", cleanup_block)
        self.assertTrue(cleanup_block.startswith("RUN ("))
        self.assertTrue(cleanup_block.endswith(") || true"))

    def test_contract_stage_executes_suite_before_every_build_stage(self) -> None:
        self.assertEqual(
            EXPECTED_CONTRACT_STAGE_LINES,
            self._contract_stage_lines(self.pipeline),
        )
        contract_stage = self.pipeline.index("stage('CI Contract Tests')")
        for stage_name in (
            "Frontend Tests and Build",
            "MCP Build",
            "Build Docker Images",
        ):
            with self.subTest(stage=stage_name):
                self.assertLess(
                    contract_stage,
                    self.pipeline.index(f"stage('{stage_name}')"),
                )

    def test_contract_stage_parser_rejects_echo_only_mutation(self) -> None:
        mutated = self.pipeline.replace(
            f'sh "{CONTRACT_COMMAND}"',
            f'echo "{CONTRACT_COMMAND}"',
            1,
        )
        self.assertNotEqual(
            EXPECTED_CONTRACT_STAGE_LINES,
            self._contract_stage_lines(mutated),
        )

    def test_backend_smoke_is_exact_command_immediately_after_backend_build(self) -> None:
        commands = self._docker_build_commands(self.pipeline)
        self.assertEqual(
            [
                EXPECTED_BACKEND_BUILD,
                EXPECTED_BACKEND_SMOKE,
                EXPECTED_FRONTEND_BUILD,
            ],
            commands,
        )

    def test_smoke_parser_rejects_wrong_image_with_backend_comment_mutation(self) -> None:
        mutated = self.pipeline.replace(
            '"nexusmind-backend:${IMAGE_TAG}" \\\n                        --version',
            '"nexusmind-frontend:${IMAGE_TAG}" \\\n'
            '                        --version\n'
            '                    # "nexusmind-backend:${IMAGE_TAG}"',
            1,
        )
        commands = self._docker_build_commands(mutated)
        self.assertNotEqual(EXPECTED_BACKEND_SMOKE, commands[1])


if __name__ == "__main__":
    unittest.main()
