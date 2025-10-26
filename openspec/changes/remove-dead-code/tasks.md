## 1. Prepare for Cleanup
- [ ] 1.1 Review redundancy analysis document (`docs/REDUNDANCY-ANALYSIS.md`)
- [ ] 1.2 Verify all production code is documented and essential
- [ ] 1.3 Ensure current branch is `cleanup/remove-redundant-code`
- [ ] 1.4 Run full test suite to establish baseline (`python -m pytest tests/ -v`)

## 2. Phase 1 - Remove Non-Functional Test File (Zero Risk)
- [ ] 2.1 Verify `test_llm_condensing.py` is not imported anywhere
- [ ] 2.2 Delete `test_llm_condensing.py`
- [ ] 2.3 Run tests to confirm no breakage
- [ ] 2.4 Commit: "chore: remove non-functional test_llm_condensing.py"

## 3. Phase 2 - Remove Auto-Generated Cache Files (Zero Risk)
- [ ] 3.1 Delete all `__pycache__/` directories recursively
- [ ] 3.2 Delete `.coverage` file if exists
- [ ] 3.3 Update `.gitignore` to include `__pycache__/` and `.coverage` if not already present
- [ ] 3.4 Run tests to confirm functionality intact
- [ ] 3.5 Commit: "chore: remove auto-generated cache files and update gitignore"

## 4. Phase 3 - Consolidate Redundant Documentation (Low Risk)
- [ ] 4.1 Verify `docs/SESSION-FIXES-2025-10-06.md` contains all critical information
- [ ] 4.2 Compare content between overlapping docs to ensure no information loss
- [ ] 4.3 Delete `docs/FIX-SUMMARY.md`
- [ ] 4.4 Delete `docs/LLM-CONDENSING-FIX.md`
- [ ] 4.5 Delete `docs/CRITICAL-BUG-FIX.md`
- [ ] 4.6 Commit: "docs: consolidate redundant documentation files"

## 5. Phase 4 - Review Optional Test Files (Requires Decision)
- [ ] 5.1 Review `test_fixes.py` - determine if needed for regression testing
- [ ] 5.2 Review `test_examples.py` - determine if validates EXAMPLES.md correctly
- [ ] 5.3 Review `test_api_doc.py` - determine if validates API.md correctly
- [ ] 5.4 If keeping: Move to `tests/` directory for consistency
- [ ] 5.5 If removing: Delete and commit with justification
- [ ] 5.6 Commit (if changes made): "test: reorganize/remove optional validation tests"

## 6. Verification and Testing
- [ ] 6.1 Run full test suite: `python -m pytest tests/ -v`
- [ ] 6.2 Verify all tests pass
- [ ] 6.3 Check test coverage: `python -m pytest tests/ --cov=src --cov-report=html`
- [ ] 6.4 Ensure no production functionality broken
- [ ] 6.5 Review git diff to confirm only intended files removed

## 7. Documentation Updates
- [ ] 7.1 Update `README.md` if any test file references need removal
- [ ] 7.2 Update `TESTING-GUIDE.md` to reflect current test structure
- [ ] 7.3 Update `CLEANUP-PLAN.md` to mark completed items
- [ ] 7.4 Commit: "docs: update documentation for cleanup changes"

## 8. Final Review and Merge Preparation
- [ ] 8.1 Review all commits on cleanup branch
- [ ] 8.2 Ensure commit messages follow conventional commits
- [ ] 8.3 Squash commits if needed for cleaner history
- [ ] 8.4 Push branch: `git push origin cleanup/remove-redundant-code`
- [ ] 8.5 Create pull request with summary of changes
- [ ] 8.6 Request code review (if applicable)

## 9. Merge and Archive
- [ ] 9.1 Merge to main: `git checkout main && git merge cleanup/remove-redundant-code`
- [ ] 9.2 Run tests on main to final verification
- [ ] 9.3 Push to remote: `git push origin main`
- [ ] 9.4 Delete cleanup branch: `git branch -d cleanup/remove-redundant-code`
- [ ] 9.5 Archive this change proposal: `openspec archive remove-dead-code --skip-specs --yes`

## Dependencies
- Tasks 2-3 can be done in parallel (both zero risk)
- Task 4 depends on tasks 2-3 completion (ensure baseline stable)
- Task 5 is independent and can be done anytime
- Tasks 6-9 are sequential and must follow all code changes