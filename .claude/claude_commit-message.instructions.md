# GitHub Copilot Commit Message Instructions

## Overview
Generate commit messages following the Conventional Commits 1.0.0 specification to create explicit, machine-readable commit history.

## Commit Message Structure

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

## Required Elements

### Type (REQUIRED)
Must be one of the following:

- **feat**: A new feature (correlates with MINOR in SemVer)
- **fix**: A bug fix (correlates with PATCH in SemVer)
- **docs**: Documentation only changes
- **style**: Changes that don't affect code meaning (white-space, formatting, etc.)
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**: Code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **build**: Changes that affect the build system or external dependencies
- **ci**: Changes to CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files
- **revert**: Reverts a previous commit

### Description (REQUIRED)
- Must immediately follow the colon and space after the type/scope prefix
- Short summary of code changes
- Use imperative, present tense: "change" not "changed" nor "changes"
- Don't capitalize first letter
- No period (.) at the end

## Optional Elements

### Scope (OPTIONAL)
- Noun describing a section of the codebase
- Enclosed in parentheses
- Examples: `feat(parser):`, `fix(api):`, `docs(readme):`

### Body (OPTIONAL)
- Must begin one blank line after the description
- Free-form, can consist of multiple paragraphs
- Provides additional contextual information about code changes
- Use imperative, present tense

### Footer(s) (OPTIONAL)
- Must be provided one blank line after the body
- Format: `<token>: <value>` or `<token> #<value>`
- Use hyphens in tokens: `Reviewed-by:`, `Refs:`
- Common footers: `Reviewed-by:`, `Refs:`, `Fixes:`, `Co-authored-by:`

## Breaking Changes

Breaking changes MUST be indicated using one of these methods:

### Method 1: Exclamation mark before colon
```
feat!: send an email to customer when product is shipped
```

### Method 2: Footer with BREAKING CHANGE
```
feat: allow provided config object to extend other configs

BREAKING CHANGE: `extends` key in config file is now used for extending other config files
```

### Method 3: Scope with exclamation mark
```
feat(api)!: send an email to customer when product is shipped
```

### Method 4: Both exclamation mark and footer
```
chore!: drop support for Node 6

BREAKING CHANGE: use JavaScript features not available in Node 6.
```

## Examples

### Simple commit with type and description
```
docs: correct spelling of CHANGELOG
```

### Commit with scope
```
feat(lang): add Polish language
```

### Commit with body
```
fix: prevent racing of requests

Introduce a request id and a reference to latest request. Dismiss
incoming responses other than from latest request.
```

### Commit with multiple footers
```
fix: prevent racing of requests

Introduce a request id and a reference to latest request. Dismiss
incoming responses other than from latest request.

Remove timeouts which were used to mitigate the racing issue but are
obsolete now.

Reviewed-by: Z
Refs: #123
```

### Revert commit
```
revert: let us never again speak of the noodle incident

Refs: 676104e, a215868
```

## Rules to Follow

1. **Type is mandatory** - Every commit MUST have a type prefix
2. **Use lowercase** - Types should be lowercase for consistency
3. **Be atomic** - If commit conforms to multiple types, split into multiple commits
4. **Be descriptive** - Description should clearly explain what changed
5. **Breaking changes** - MUST be indicated with `!` and/or `BREAKING CHANGE:` footer
6. **Case sensitivity** - All elements are case-insensitive except `BREAKING CHANGE` which MUST be uppercase
7. **No assumptions** - Don't treat missing type as valid

## Semantic Versioning Correlation

- `fix:` → PATCH release (0.0.X)
- `feat:` → MINOR release (0.X.0)
- `BREAKING CHANGE:` → MAJOR release (X.0.0)

## Best Practices

1. Keep the description concise (50 characters or less is ideal)
2. Use the body to explain "what" and "why" vs. "how"
3. Reference issues and pull requests in footers
4. Be consistent with type choices across the project
5. Use scopes to provide additional context when helpful
6. Make commits atomic and focused on a single change