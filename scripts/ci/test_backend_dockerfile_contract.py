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
        install_start = self.dockerfile.index("RUN uv venv")
        runtime_stage = self.dockerfile.index("FROM python:3.11-slim")
        install_block = self.dockerfile[install_start:runtime_stage]

        self.assertIn("UV_HTTP_TIMEOUT=", self.dockerfile)
        self.assertNotIn("|| true", install_block)
        self.assertIn("test -x /opt/venv/bin/gunicorn", install_block)

    def test_pipeline_smoke_checks_gunicorn_before_packaging_images(self) -> None:
        build_stage = self.pipeline.index("stage('Build Docker Images')")
        package_stage = self.pipeline.index("stage('Package Deployment Artifacts')")
        build_block = self.pipeline[build_stage:package_stage]

        self.assertIn("--entrypoint gunicorn", build_block)
        self.assertIn("--version", build_block)


if __name__ == "__main__":
    unittest.main()
