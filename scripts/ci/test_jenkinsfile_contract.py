from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
JENKINSFILE = REPOSITORY_ROOT / "Jenkinsfile"


class JenkinsfileContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pipeline = JENKINSFILE.read_text(encoding="utf-8")

    def test_defaults_to_enhancements_and_checks_out_requested_branch(self) -> None:
        self.assertIn("defaultValue: 'enhancements'", self.pipeline)
        self.assertIn(
            "defaultValue: 'https://github.com/Shivam5560/Professional_Grade_RAG.git'",
            self.pipeline,
        )
        self.assertIn("params.GIT_BRANCH", self.pipeline)
        self.assertIn("params.GIT_REPOSITORY", self.pipeline)
        self.assertNotIn("branch: 'main'", self.pipeline)

    def test_pipeline_never_pushes_repository_changes(self) -> None:
        self.assertNotIn("git push", self.pipeline)
        self.assertNotIn("withCredentials", self.pipeline)

    def test_pipeline_runs_quality_gates_before_building_images(self) -> None:
        required_stages = (
            "Backend Tests",
            "Frontend Tests and Build",
            "MCP Build",
            "Build Docker Images",
            "Package Deployment Artifacts",
        )
        stage_positions = [
            self.pipeline.index(f"stage('{stage}')") for stage in required_stages
        ]
        self.assertEqual(stage_positions, sorted(stage_positions))
        self.assertNotIn("--minWorkers", self.pipeline)

    def test_pipeline_archives_versioned_images_with_checksums(self) -> None:
        self.assertIn("docker save", self.pipeline)
        self.assertIn("sha256sum", self.pipeline)
        self.assertIn("archiveArtifacts", self.pipeline)
        self.assertIn("artifacts/*", self.pipeline)


if __name__ == "__main__":
    unittest.main()
