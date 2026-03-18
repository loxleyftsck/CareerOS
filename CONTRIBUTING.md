# Contributing to CareerOS

Thank you for contributing to CareerOS! To maintain a high-quality codebase and clean development lifecycle, please follow these guidelines.

## 🌳 Branching Model

We use a multi-phase branching strategy:

1.  **main**: Stable, production-ready code. Only merged from `staging`.
2.  **staging**: Pre-release integration and testing. Merged from `dev`.
3.  **dev**: Main development branch. Features and R&D results are integrated here.
4.  **rnd/***: Experimental work and research. Once validated, ported to `dev`.
5.  **feature/***: Specific feature implementation.
6.  **hotfix/***: Urgent fixes for production issues.

### Workflow Flow:
`rnd/*` -> `dev` -> `staging` -> `main`

## 🧪 Commit Convention

We use **Conventional Commits** to keep our history readable.

### Format:
`<type>(<scope>): <description>`

### Types:
- `feat`: New feature.
- `fix`: Bug fix.
- `chore`: Maintenance, config, dependencies.
- `refactor`: Code restructuring without changing behavior.
- `test`: Adding or fixing tests.
- `docs`: Documentation updates.

### Scopes:
- `(rnd)`: Research and Experimentation phase.
- `(dev)`: Development phase.
- `(staging)`: Integration and testing phase.
- `(prod)`: Production-level changes.

### Examples:
- `feat(rnd): initial RL routing experiment`
- `feat(dev): implement job matching engine v1`
- `fix(staging): resolve matching edge cases`
- `release: v1.0.0 – initial CareerOS engine`

## 🧬 Development Phases

1.  **R&D Phase**: Prototype new ideas in `rnd/` branches. Expect changes and isolation.
2.  **Dev Phase**: Implement clean, modular code in `dev`.
3.  **Staging Phase**: Verify integration in `staging`. Final bug squash.
4.  **Production Phase**: Tag stable releases on `main`.

---
Happy Coding!
