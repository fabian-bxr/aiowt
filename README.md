<div align="center">
<h1> aiowt - War Thunder Telemetry </h1>
<hr>

Asynchronous Python Wrapper for the War Thunder local telemetry API using asyncio and Pydantic.  
Query live vehicle state, map data, missions and messages.   
Compatible with **both Air- and Ground-Battles**.
</div>


## Installation
````shell
uv add git+https://github.com/fabian-bxr/aiowt.git

# alternative
pip install git+https://github.com/fabian-bxr/aiowt.git
````
## Usage
````python
import asyncio
from aiowt import WtTelemetry

async def query_once():
    ...


async def loop():
    async with WtTelemetry() as wt:
        async for data in wt.indicators():
            print(data)

asyncio.gather(
    query_once(),
    loop()
)
````
## Endpoints 
### `indicators`
### `state`
### `mission`
### `map_obj`
### `map_info`
### `map_img`
### `gamechat`
### `hud_message`


## Data

## License