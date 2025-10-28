# Changelog

## v1.0.0 (2025-10-28)
- Initial stable release.
- Added centralized config loader with caching (`scripts/config_loader.py`).
- Implemented unified OutputContract with JSON Schema validation (`scripts/poc_local_validate.py`).
- Enabled async tools and exponential backoff retry strategy.
- Added automated progress generation (`scripts/generate_progress.py`).
- Provided external feature list and developer guide (`docs/feature_list.md`, `docs/dev_guide.md`).
- Fixed progress script `UnboundLocalError` by adjusting detection order.
