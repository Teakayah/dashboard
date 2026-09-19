## 2025-02-23 - Switch ThreadPoolExecutor to Asyncio for Network Calls
**Learning:** Using ThreadPoolExecutor + urllib for HTTP requests has higher overhead than asyncio + aiohttp for parallel networking requests.
**Action:** Used `asyncio.create_task` with `aiohttp` for fetching data from the API concurrently for significant performance boost.
