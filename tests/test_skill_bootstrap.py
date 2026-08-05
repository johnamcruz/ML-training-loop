from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from ml_training_loop.skills import BundledSkillBootstrapper, directory_sha256


class BundledSkillBootstrapperTests(unittest.TestCase):
    def test_installs_missing_skill_and_never_overwrites_existing_skill(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = root / "bundle"
            destination = root / "installed"
            source = bundle / "ml-example"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text(
                "---\nname: ml-example\ndescription: Example.\n---\nUse it.\n"
            )
            (bundle / "skills.lock.json").write_text(json.dumps({
                "schema": "ml-training-loop-skills-lock-v1",
                "skills": [{
                    "name": "ml-example",
                    "sha256": directory_sha256(source),
                }],
            }))
            bootstrapper = BundledSkillBootstrapper(bundle, destination)

            installed = bootstrapper.ensure(("ml-example",))
            self.assertTrue(installed.ready)
            self.assertEqual(installed.statuses[0].status, "installed")
            self.assertEqual(
                (destination / "ml-example/SKILL.md").read_text(),
                (source / "SKILL.md").read_text(),
            )

            (destination / "ml-example/SKILL.md").write_text("local version\n")
            preserved = bootstrapper.ensure(("ml-example",))
            self.assertTrue(preserved.ready)
            self.assertEqual(preserved.statuses[0].status, "already_present")
            self.assertEqual(
                (destination / "ml-example/SKILL.md").read_text(),
                "local version\n",
            )

    def test_hash_mismatch_fails_closed_without_partial_install(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = root / "bundle"
            destination = root / "installed"
            source = bundle / "ml-example"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text("changed\n")
            (bundle / "skills.lock.json").write_text(json.dumps({
                "schema": "ml-training-loop-skills-lock-v1",
                "skills": [{"name": "ml-example", "sha256": "0" * 64}],
            }))

            receipt = BundledSkillBootstrapper(bundle, destination).ensure(
                ("ml-example",)
            )

            self.assertFalse(receipt.ready)
            self.assertEqual(receipt.statuses[0].status, "bundle_hash_mismatch")
            self.assertFalse((destination / "ml-example").exists())


if __name__ == "__main__":
    unittest.main()
