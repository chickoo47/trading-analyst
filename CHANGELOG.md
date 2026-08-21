# Changelog

All notable changes to Trading Analyst are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Rebranded the project as Trading Analyst: removed inherited third-party
  branding (CLI banner, welcome ASCII art, screenshots, logo/QR assets),
  disabled the third-party announcements endpoint, and updated outbound
  User-Agent strings and package metadata to point at this repository.
- Clarified README language around entry/exit price levels: these are
  LLM-estimated figures produced alongside the agents' reasoning, not
  values from a deterministic pricing or backtesting engine.

## [0.2.5]

### Added

- Groq TPM rate limiting in the LLM client layer.
- Simplified CLI flow.
- Tweaked the Market Analyst prompt.
