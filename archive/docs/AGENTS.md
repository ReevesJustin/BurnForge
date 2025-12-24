# AGENTS.md - Custom Instructions for IB_Solver Project

## Overview
This file contains custom instructions for AI agents working on the IB_Solver project, a scientific numerical simulation for firearm internal ballistics.

## Key Principles

### Scientific Accuracy
- **Physics First**: All changes must maintain physical accuracy. Verify equations against literature (Noble-Abel EOS, burn rate models, etc.)
- **Numerical Stability**: Ensure ODE solvers converge reliably. Avoid parameters that cause numerical instability.
- **Units Consistency**: All calculations use consistent imperial units (psi, lbm, in, ft, s).

### Development Workflow
- **Iterative Changes**: Prefer small, incremental edits over large rewrites.
- **Test After Changes**: Always run relevant tests and diagnostics after modifications:
  - `pytest tests/` for unit tests
  - `python verify_phase2.py` for integration checks
  - `python analyze_fit.py` for fitting validation
- **Type Safety**: Maintain mypy compatibility. Fix type errors before committing.

### Documentation Standards
- **NumPy Docstring Format**: Use standardized docstrings with Parameters, Returns, Notes sections
- **Physics References**: Include literature citations for equations and models
- **Code Comments**: Explain complex physics in comments, not just implementation

### Database Management
- **Version Control**: Use schema migrations for database changes
- **Data Integrity**: Validate propellant/ballistic data against known references
- **System-Specific Storage**: Store fitted parameters per firearm/bullet/propellant/temperature combination

### Fitting and Optimization
- **Parameter Bounds**: Use physics-based bounds to prevent unrealistic values
- **Convergence Criteria**: Ensure fits converge to physically meaningful solutions
- **Validation**: Cross-validate fits against held-out data or known benchmarks

## Phase Context
Reference these completed phases for implementation context:
- **Phase 1**: Core lumped-parameter ODE solver with event detection
- **Phase 2**: CSV/GRT import, vivacity polynomial fitting, database integration
- **Physics V3**: Heat loss models, temperature sensitivity, Noble-Abel EOS extensions

## Common Pitfalls to Avoid
- **Over-parameterization**: Don't add parameters without clear physical justification
- **Numerical Instability**: Lambda_base > 0.15 or extreme polynomial coefficients can cause ODE failures
- **Unit Mismatches**: Imperial vs SI unit conversions are error-prone
- **Database Corruption**: Always backup before schema changes

## Available Agents

The following specialized agents are available for different aspects of IB_Solver development:

### Core Agents
- **Code Review Agent** (`.opencode/agent/code-review.md`): Reviews code for physics accuracy, numerical stability, and best practices
- **Testing & Validation Agent** (`.opencode/agent/testing-validation.md`): Ensures test coverage and validates physics models
- **Documentation Agent** (`.opencode/agent/documentation.md`): Maintains comprehensive and accurate documentation
- **Status Reporter Agent** (`.opencode/agent/status-reporter.md`): Automatically generates project status summaries

### Research Agents
- **Propellant Grain Researcher** (`.opencode/agent/propellant-researcher.md`): Researches smokeless propellant grain properties for database expansion

### Agent Usage
- Agents can be invoked via `/agent [name]` commands or triggered automatically
- Each agent has specific triggers and output formats
- Agents work together to maintain code quality and project documentation

## Quality Checks
Before finalizing changes:
1. Run full test suite: `pytest tests/ -v`
2. Check mypy: `mypy src/ballistics`
3. Validate physics: Run diagnostics on known test cases
4. Update docs: Ensure README and docstrings reflect changes
5. Consider agent reviews: Use appropriate agents for specialized validation</content>
<parameter name="filePath">AGENTS.md