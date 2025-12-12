\# THN CLI – Release Checklist



This checklist standardizes release steps for TestPyPI, PyPI, and internal THN builds.



---



\## 1. Pre-Release Validation



\- \[ ] All tests pass locally (`pytest -q`)

\- \[ ] Version updated in `thn\_cli/\_\_init\_\_.py`

\- \[ ] CHANGELOG updated

\- \[ ] No uncommitted changes (`git status`)

\- \[ ] Dependencies reviewed for correctness

\- \[ ] No leftover build artifacts:

&nbsp;     ```

&nbsp;     rmdir /s /q dist build thn\_cli.egg-info

&nbsp;     ```



---



\## 2. TestPyPI Release



Use when validating a new release before production deployment.



\- \[ ] Push version commit to main

\- \[ ] Go to GitHub → Actions → “THN CLI – Publish to TestPyPI”

\- \[ ] Run workflow with version input (ex: `2.0.0`)

\- \[ ] Install and validate:

&nbsp;     ```

&nbsp;     pip install --index-url https://test.pypi.org/simple --extra-index-url https://pypi.org/simple thn-cli

&nbsp;     ```

\- \[ ] Run core commands:

&nbsp;     ```

&nbsp;     thn diag

&nbsp;     thn sync web --dry-run

&nbsp;     thn list

&nbsp;     ```



---



\## 3. Production PyPI Release



Triggered by pushing a version tag.



\- \[ ] Create tag:

&nbsp;     ```

&nbsp;     git tag v2.0.0

&nbsp;     git push origin v2.0.0

&nbsp;     ```

\- \[ ] GitHub Actions auto-publishes to PyPI

\- \[ ] Validate installation:

&nbsp;     ```

&nbsp;     pip install --upgrade thn-cli

&nbsp;     ```



---



\## 4. Post-Release



\- \[ ] Confirm version appears on PyPI

\- \[ ] Draft GitHub release notes

\- \[ ] Update Sync Delta docs if envelope schema changed

\- \[ ] Run THN Master Control self-tests:

&nbsp;     ```

&nbsp;     scripts/selftest\_thn\_cli.sh

&nbsp;     ```

\- \[ ] Start planning next release (bump pre-release version)



---



