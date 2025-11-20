# Plan Creation & Organization

## Directory Structure

### Plan Location
Save plans in `./plans` directory with timestamp and descriptive name.

**Format:** `plans/YYYYMMDD-HHmm-your-plan-name/`

**Example:** `plans/20251101-1505-authentication-and-profile-implementation/`

### File Organization

```
plans/
├── 20251101-1505-authentication-and-profile-implementation/
    ├── research/
    │   ├── researcher-XX-report.md
    │   └── ...
│   ├── reports/
│   │   ├── scout-report.md
│   │   ├── researcher-report.md
│   │   └── ...
│   ├── plan.md                                # Overview access point
│   ├── phase-01-setup-environment.md          # Setup environment
│   ├── phase-02-implement-database.md         # Database models
│   ├── phase-03-implement-api-endpoints.md    # API endpoints
│   ├── phase-04-implement-ui-components.md    # UI components
│   ├── phase-05-implement-authentication.md   # Auth & authorization
│   ├── phase-06-implement-profile.md          # Profile page
│   ├── phase-07-write-tests.md                # Tests
│   ├── phase-08-run-tests.md                  # Test execution
│   ├── phase-09-code-review.md                # Code review
│   ├── phase-10-project-management.md         # Project management
│   ├── phase-11-onboarding.md                 # Onboarding
│   └── phase-12-final-report.md               # Final report
└── ...
```

## File Structure

### Overview Plan (plan.md)
- Keep generic and under 80 lines
- List each phase with status/progress
- Link to detailed phase files
- High-level timeline
- Key dependencies

### Phase Files (phase-XX-name.md)
Fully respect the `./docs/development-rules.md` file.
Each phase file should contain:

**Context Links**
- Links to related reports, files, documentation

**Overview**
- Date and priority
- Current status
- Brief description

**Key Insights**
- Important findings from research
- Critical considerations

**Requirements**
- Functional requirements
- Non-functional requirements

**Architecture**
- System design
- Component interactions
- Data flow

**Related Code Files**
- List of files to modify
- List of files to create
- List of files to delete

**Implementation Steps**
- Detailed, numbered steps
- Specific instructions

**Todo List (Required - Actionable Checkboxes)**
- Must include checkbox items `- [ ]` for every actionable task
- Items should be specific and completable (not vague)
- Group by priority: P0 (Critical), P1 (Important), P2 (Nice-to-have)
- Mark completed items with `- [x]` during implementation
- Format example:
  ```markdown
  ## Todo List

  ### P0 - Critical
  - [ ] Create database migration for user table
  - [ ] Implement user model with validations
  - [ ] Add API endpoint POST /api/users

  ### P1 - Important
  - [ ] Add input validation middleware
  - [ ] Implement error handling
  - [ ] Write unit tests for user service

  ### P2 - Nice-to-have
  - [ ] Add request rate limiting
  - [ ] Implement caching layer
  ```

**Success Criteria**
- Definition of done
- Validation methods

**Risk Assessment**
- Potential issues
- Mitigation strategies

**Security Considerations**
- Auth/authorization
- Data protection

**Next Steps**
- Dependencies
- Follow-up tasks
