import json
import aiohttp
import asyncio
from loguru import logger
from typing import AsyncGenerator, Any, Optional, Dict
from enum import StrEnum
from pydantic import ValidationError

from aiowt.models.map_info import MapInfo
from aiowt.models.indicator_tank import TankIndicator
from aiowt.models.indicator_air import AirIndicator
from aiowt.models.map_obj import MapObj
from aiowt.models.mission import Mission
from aiowt.models.state import State
from aiowt.models.gamechat import GameChat
from aiowt.models.hud_msg import HudMsg


class Endpoints(StrEnum):
    INDICATORS = "/indicators"
    STATE = "/state"
    MISSION = "/mission.json"
    MAP_OBJ = "/map_obj.json"
    MAP_INFO = "/map_info.json"
    MAP_IMG = "/map.img"
    GAMECHAT = "/gamechat"
    HUD_MSG = "/hudmsg"


class WtTelemetry:
    def __init__(self, base_url: str = "http://localhost:8111"):
        self.base_url = base_url
        self.self_session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=10)
        self.self_session = aiohttp.ClientSession(
            base_url=self.base_url, timeout=timeout
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.self_session.close()

    async def _poll_endpoint(
        self,
        endpoint: Endpoints,
        interval: float = 0.2,
        params: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[bytes, None]:
        if not self.self_session:
            raise RuntimeError("Client session not initialized")

        while True:
            #logger.debug(f"Polling endpoint: {endpoint}, params: {params}")
            async with self.self_session.get(endpoint, params=params) as response:
                try:
                    resp = await response.read()

                    if resp == b'': # Skip empty responses
                        continue

                    yield resp
                except aiohttp.ClientError as e:
                    logger.error(f"Network error polling {endpoint}: {e}")

                except asyncio.TimeoutError as e:
                    logger.error(f"Timeout error polling {endpoint}: {e}")

                except Exception as e:
                    logger.error(f"Unexpected error polling {endpoint}: {e}")

                await asyncio.sleep(interval)

    async def indicators(self) -> AsyncGenerator[TankIndicator | Dict, None]:
        async for resp in self._poll_endpoint(Endpoints.INDICATORS):
            # Needs to check if Army == 'tank' or 'air', don't yield anything for ships as there are no indicators
            try:
                resp_json = json.loads(resp.decode("utf-8"))
                army = resp_json.get("army")

                if army == "tank":
                    yield TankIndicator.model_validate_json(resp)

                elif army == "air":
                    yield resp_json

            except ValidationError as e:
                logger.error(f"Validation error for Indicator: {e}")

    async def map_infos(self) -> AsyncGenerator[MapInfo, None]:
        async for resp in self._poll_endpoint(Endpoints.MAP_INFO, interval=1):
            try:
                yield MapInfo.model_validate_json(resp)
            except ValidationError as e:
                logger.error(f"Validation error for MapInfo: {e}")

    async def map_objs(self) -> AsyncGenerator[MapObj, None]:
        async for resp in self._poll_endpoint(Endpoints.MAP_OBJ, interval=0):
            try:
                yield MapObj.model_validate_json(resp)
            except ValidationError as e:
                logger.error(f"Validation error for MapObj: {e}")

    async def missions(self) -> AsyncGenerator[Mission, None]:
        async for resp in self._poll_endpoint(Endpoints.MISSION, interval=1):
            try:
                yield Mission.model_validate_json(resp)
            except ValidationError as e:
                logger.error(f"Validation error for Mission: {e}")

    async def states(self) -> AsyncGenerator[State, None]:
        raise NotImplementedError("State for Aircraft not yet implemented")
        async for resp in self._poll_endpoint(Endpoints.STATE, interval=1):
            try:
                yield State.model_validate_json(resp)
            except ValidationError as e:
                logger.error(f"Validation error for State: {e}")

    async def chat_messages(self) -> AsyncGenerator[GameChat, None]:
        params = {"lastId": 0} # Mutable dict to query chat messages
        async for resp in self._poll_endpoint(Endpoints.GAMECHAT, interval=1, params=params):
            try:
                # logger.debug(resp)
                data = json.loads(resp.decode("utf-8"))
                if data:
                    highest_id = max([msg.get("id", 0) for msg in data], default=params["lastId"])
                    params["lastId"] = highest_id

                    # Only yield when there is a new message
                    yield GameChat.model_validate_json(resp)
            except ValidationError as e:
                logger.error(f"Validation error for GameChat: {e}")

    async def hud_messages(self) -> AsyncGenerator[HudMsg, None]:
        params = {"lastEvt": 0, "lastDmg": 0}

        async for resp in self._poll_endpoint(Endpoints.HUD_MSG, interval=1, params=params):
            try:
                data = json.loads(resp.decode())

                # Update ID Counters to only query new messages
                events = data.get("events", [])
                if events:
                    params["lastEvt"] = max([evt.get("id", 0) for evt in events], default=params["lastEvt"])

                damage = data.get("damage", [])
                if damage:
                    params["lastDmg"] = max([dmg.get("id", 0) for dmg in damage], default=params["lastDmg"])

                if events or damage:
                    # Only yield when there is a new message
                    yield HudMsg.model_validate_json(resp)

            except ValidationError as e:
                logger.error(f"Validation error for HUDMessage: {e}")
            except Exception as e:
                logger.error(f"Error parsing HUDMessage data: {e}")

    async def map_imgs(self) -> AsyncGenerator[bytes, None]:
        async for resp in self._poll_endpoint(Endpoints.MAP_IMG, interval=1):
            yield resp


async def main():
    async with WtTelemetry() as telemetry:
        async for indicators in telemetry.map_objs():
            print(indicators)


if __name__ == "__main__":
    asyncio.run(main())
