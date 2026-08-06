"""Service interfaces defining the Internal API from the Design Pack.

Per the Engineering/Design Pack rules: the UI never calls external APIs or
the database directly, all AI requests go through :class:`AIService`, and
services communicate through these well-defined interfaces rather than
loose dictionaries.
"""
