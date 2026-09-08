# Error assertion semantics

For `unsatisfiable` tests, this suite deliberately asserts more than conda's
own test suite does when running under conda-libmamba-solver.

Upstream's `assert_unsatisfiable` helper only checks that the raised
exception is an `UnsatisfiableError` subclass there, because its entries
comparison is gated on the exact `UnsatisfiableError` type — libmamba raises
a different subclass with a different message shape, so upstream's own
assertion on the conflict entries is effectively skipped for that backend.

This project's runner goes further: it additionally checks that the endpoint
package names of each expected conflict chain appear in the libmamba error
message, and the `message_includes` / `message_excludes` fields in the YAML
add further content checks. Those fields may be given as a single value or
list that applies to every solver, or as a mapping keyed by solver name when
upstream itself asserts solver-specific message content — a missing key for
a solver a test runs on is treated as an error, rather than silently skipping
the check for that backend.

This strengthening is intentional. Cross-solver consistency of error
reporting — not just of the final decision to fail — is part of what this
plugin exists to verify (see [Motivation](motivation)). See
[Adding a test](../how-to/adding-a-test) for the general convention of
documenting this kind of strengthening in a case's `description` field, and
the [test schema](../reference/test-schema) for the full shape of the four
error types.
