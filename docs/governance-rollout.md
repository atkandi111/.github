# Governance rollout

The portfolio GitHub Project remains the canonical view of status and priority. Repository workflows do not use Project fields as task authorization.

The reusable governance workflow validates only deterministic naming rules and is disabled by default through `GOVERNANCE_NAMING_ENFORCED`. Observe it before enabling. Cloud-generated branch names are accepted as automation and should not drive new parsing or classification logic.

Do not add semantic Issue classification, AI review, automated priority assignment, convergence loops, or auto-merge. Human-authored Issue contracts and Merge Briefs are the simpler control surface for a solo developer.

## Portfolio membership

The Project's native auto-add workflow targets `atkandi111/demandph-website` with `is:issue,pr is:open`. GitHub permits only one native auto-add workflow on the current plan, and each workflow targets one repository, so `dev-platform` provides the narrow fallback for the rest of the portfolio:

- `config/portfolio-repositories.txt` is the reviewed inventory of active repositories.
- `.github/workflows/portfolio-project.yml` audits every listed repository and reconciles missing open Issues and pull requests hourly.
- `scripts/reconcile-portfolio-project audit` reports exact missing URLs without changing the Project.
- `scripts/reconcile-portfolio-project reconcile` adds only missing open items. It never removes or archives items and never edits Status, Priority, Waiting On, or other fields.

The Project's enabled **Item added to project** workflow supplies the normal initial `Todo` status. Its lifecycle workflows move closed and merged items to `Done`, reopened items to `Todo`, linked or changes-requested work to `In Progress`, and approved pull requests to `Review`.

The Actions workflow requires the repository secret `PORTFOLIO_PROJECT_TOKEN`. Use a dedicated credential able to read the registered private repositories and read/write the user-owned Project. For a classic personal access token, GitHub requires `repo` for private repository records and `project` for Project queries and mutations. Never pass the token as a command argument or print it.

## Future repository onboarding

1. Add `OWNER/REPOSITORY` to `config/portfolio-repositories.txt` in alphabetical order through a reviewed `dev-platform` pull request.
2. If the GitHub plan has an unused native auto-add slot, add a repository-specific rule with `is:issue,pr is:open`; otherwise the scheduled reconciler is the auto-add coverage.
3. Run `./client-setup onboard TARGET PLATFORM_OWNER/REPOSITORY CLIENT_OWNER/REPOSITORY`. It refuses unregistered clients.
4. Run the **Portfolio Project reconciliation** workflow in `audit` mode and confirm there are no missing open items.
5. Open one disposable Issue in the new repository, run or await reconciliation, and confirm one Project item appears with `Status: Todo` and no Priority. Close and reopen it once to verify `Done` then `Todo`, confirm no duplicate appears, and close it afterward.

Treat a missing secret, Project access error, inventory omission, duplicate repository, or audit gap as failed onboarding. Do not compensate by using Project fields as execution authority.
