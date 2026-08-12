# AI Usage

AI tools were used selectively during the project, mainly for clarification, troubleshooting, and some documentation. The implementation was reviewed and tested before being kept.

## Where AI Help Was Used

### Debugging and Troubleshooting

AI was used when an error or behaviour was unclear. This included questions around:

- SQLite transactions and rollback behaviour
- Flask request validation
- SQL joins affecting report counts
- Render/Gunicorn configuration

Suggested changes were checked against the existing code and tests.

### Documentation

AI was used for some wording and structure in the README and defect notes. The technical details were based on the actual implementation.

### Commit Messages

AI was used occasionally to clean up or suggest commit message wording. The actual changes were made and committed during development.

## Verification

AI suggestions were checked rather than used without testing. The main checks were:

- Supplied smoke tests
- Invalid request data
- Transaction rollback
- Status transitions
- Duplicate events
- Inventory changes
- Fulfilment report results

## Note

AI was used as a support tool for parts of the work. Simple fixes and changes were handled directly while working through the defects.
