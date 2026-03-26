# Changelog

## [1.0.3] - 2026-03-26
- Add configurable API host (host) for local/self-hosted Sure instances (add-on and HA integration)
- Migrate cache from aioredis to redis.asyncio for Python 3.11 compatibility
- Fix s6-overlay v3 compatibility (with-contenv path) and ensure service scripts are executable

## [1.0.2] - 2026-03-24
- Initial release
- Basic integration with Sure Finance API
- Support for cashflow, outflow, and liability tracking
- Home Assistant sensor creation
- Web dashboard interface
- Configurable update intervals
- Data caching functionality