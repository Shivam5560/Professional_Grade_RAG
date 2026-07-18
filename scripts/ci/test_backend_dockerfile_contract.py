from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = REPOSITORY_ROOT / "backend" / "Dockerfile"
JENKINSFILE = REPOSITORY_ROOT / "Jenkinsfile"


class BackendDockerfileContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dockerfile = DOCKERFILE.read_text(encoding="utf-8")
        cls.pipeline = JENKINSFILE.read_text(encoding="utf-8")

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
        self.assertLess(
            install_block.index("uv venv /opt/venv"),
            install_block.index("uv pip install"),
        )
        self.assertLess(
            install_block.index("uv pip install"),
            install_block.index("test -x /opt/venv/bin/gunicorn"),
        )

    def test_optional_cleanup_cannot_mask_dependency_install_failure(self) -> None:
        cleanup_start = self.dockerfile.index("RUN (find /opt/venv")
        cleanup_end = self.dockerfile.index("\n\n", cleanup_start)
        cleanup_block = self.dockerfile[cleanup_start:cleanup_end]

        self.assertNotIn("uv pip install", cleanup_block)
        self.assertTrue(cleanup_block.startswith("RUN ("))
        self.assertTrue(cleanup_block.endswith(") || true"))

    def test_contract_tests_are_invoked_before_docker_builds(self) -> None:
        contract_command = "python3 -m unittest discover -s scripts/ci -p 'test_*.py' -v"
        self.assertIn(contract_command, self.pipeline)
        self.assertLess(
            self.pipeline.index(contract_command),
            self.pipeline.index("stage('Build Docker Images')"),
        )

    def test_backend_smoke_check_immediately_follows_backend_build(self) -> None:
        build_stage = self.pipeline.index("stage('Build Docker Images')")
        package_stage = self.pipeline.index("stage('Package Deployment Artifacts')")
        build_block = self.pipeline[build_stage:package_stage]

        backend_tag = build_block.index('--tag "nexusmind-backend:${IMAGE_TAG}"')
        smoke_start = build_block.index("docker run --rm", backend_tag)
        frontend_tag = build_block.index('--tag "nexusmind-frontend:${IMAGE_TAG}"')
        smoke_block = build_block[smoke_start:frontend_tag]

        self.assertLess(backend_tag, smoke_start)
        self.assertLess(smoke_start, frontend_tag)
        self.assertIn("backend\n                    docker run --rm", build_block)
        self.assertIn("--network none", smoke_block)
        self.assertIn("--read-only", smoke_block)
        self.assertIn("--cap-drop=ALL", smoke_block)
        self.assertIn("--security-opt no-new-privileges", smoke_block)
        self.assertIn("--entrypoint gunicorn", smoke_block)
        self.assertIn('"nexusmind-backend:${IMAGE_TAG}"', smoke_block)
        self.assertIn("--version", smoke_block)


if __name__ == "__main__":
    unittest.main()
