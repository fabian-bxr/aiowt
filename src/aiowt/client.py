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
from aiowt.models.gamechat import GameChat, Message
from aiowt.models.hud_msg import HudMsg, Damage, Event
from aiowt.models.common import InvalidState


class Endpoints(StrEnum):
    INDICATORS = (
        "/indicators"  # Always valid for planes and tanks, invalid state with ships
    )
    STATE = "/state"  # Only valid when plane selected
    MISSION = "/mission.json"  # Always valid
    MAP_OBJ = (
        "/map_obj.json"  # Empty response outside of a game, valid also inside naval
    )
    MAP_INFO = "/map_info.json"  # Invalid outside games
    MAP_IMG = "/map.img"  # Always returns an image, stock image outsome of games
    GAMECHAT = "/gamechat"  # Empty array outside games, inside game only displays all chat messages from this game, id counts up between games
    HUD_MSG = "/hudmsg"  # Always valid, gets kept the entire game, keeps last 238? values, id counts up TODO kept even in real games? Whats inside events


class WtTelemetry:
    def __init__(self, base_url: str = "http://localhost:8111"):
        self.base_url = base_url
        self.self_session: Optional[aiohttp.ClientSession] = None

        self._max_event_id = 0
        self._max_damage_id = 0

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=10)
        self.self_session = aiohttp.ClientSession(
            base_url=self.base_url, timeout=timeout
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.self_session.close()

    async def _fetch_endpoint(
        self, endpoint: Endpoints, params: Optional[Dict[str, Any]] = None
    ) -> bytes:
        if not self.self_session:
            raise RuntimeError("Client session not initialized")
        async with self.self_session.get(endpoint, params=params) as response:
            response.raise_for_status()
            return await response.read()

    async def _poll_endpoint(
        self,
        endpoint: Endpoints,
        interval: float = 0.2,
        params: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[bytes, None]:
        if not self.self_session:
            raise RuntimeError("Client session not initialized")

        while True:
            try:
                #logger.debug(f"Fetching Endpoint {endpoint}, params={params}")
                resp = await self._fetch_endpoint(endpoint, params)
                yield resp
            except aiohttp.ClientError as e:
                logger.error(f"Network error polling {endpoint}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error polling {endpoint}: {e}")

            await asyncio.sleep(interval)

    def _is_valid_resp(self, resp: bytes) -> bool:
        if resp == b'':
            return False

        resp_json = json.loads(resp.decode("utf-8", errors="ignore"))
        valid = resp_json.get("valid", False)
        return valid

    async def indicators(self) -> AsyncGenerator[TankIndicator | InvalidState | Dict]:
        async for resp in self._poll_endpoint(Endpoints.INDICATORS, interval=0):
            # Needs to check if Army == 'tank' or 'air', don't yield anything for ships as there are no indicators
            # Yield each query
            try:
                if not self._is_valid_resp(resp):
                    yield InvalidState()
                    continue

                resp_json = json.loads(resp.decode("utf-8"))
                army = resp_json.get("army")

                if army == "tank":
                    yield TankIndicator.model_validate_json(resp)
                elif army == "air":
                    yield resp_json
                else:
                    yield {}

            except ValidationError as e:
                logger.error(f"Validation error for Indicator: {e}")

    async def map_infos(self) -> AsyncGenerator[MapInfo | InvalidState, None]:
        # Yield when updated
        last_info: Optional[MapInfo | InvalidState] = None

        async for resp in self._poll_endpoint(Endpoints.MAP_INFO, interval=1):
            if not self._is_valid_resp(resp):
                # Yield invalid state once
                if not isinstance(last_info, InvalidState):
                    last_info = InvalidState()
                    yield InvalidState()
                continue

            try:
                logger.debug(resp)
                info = MapInfo.model_validate_json(resp)
                if info != last_info:
                    yield info
                    last_info = info

            except ValidationError as e:
                logger.error(f"Validation error for MapInfo: {e}")

    async def map_objs(self) -> AsyncGenerator[MapObj | InvalidState, None]:
        # Yield each query
        async for resp in self._poll_endpoint(Endpoints.MAP_OBJ, interval=0):
            if not self._is_valid_resp(resp) or resp == b"":
                yield InvalidState()
                continue

            try:
                yield MapObj.model_validate_json(resp)
            except ValidationError as e:
                logger.error(f"Validation error for MapObj: {e}")

    async def missions(self) -> AsyncGenerator[Mission, None]:
        # Yield when updated
        last_mission: Optional[Mission] = None
        async for resp in self._poll_endpoint(Endpoints.MISSION, interval=1):
            try:
                mission = Mission.model_validate_json(resp)
                if mission != last_mission:
                    yield mission
                    last_mission = mission

            except ValidationError as e:
                logger.error(f"Validation error for Mission: {e}")

    async def states(self) -> AsyncGenerator[State | InvalidState, None]:
        # Yield each query
        async for resp in self._poll_endpoint(Endpoints.STATE, interval=0):
            if not self._is_valid_resp(resp):
                yield InvalidState()
                continue

            try:
                continue
                raise NotImplementedError("State for Aircraft not yet implemented")
                yield State.model_validate_json(resp)
            except ValidationError as e:
                logger.error(f"Validation error for State: {e}")

    async def chat_messages(self) -> AsyncGenerator[Message, None]:
        # Yield each chat message when a new one is received
        max_id = 0  # For tracking highest ID received
        params = {"lastId": 0}  # Mutable dict to query chat messages
        async for resp in self._poll_endpoint(
            Endpoints.GAMECHAT, interval=1, params=params
        ):
            try:
                chat_batch = GameChat.model_validate_json(resp)

                # Request last and current chat message, if empty array is returned instead of last message, reset ID
                # to account for game restarts
                if not chat_batch.root and max_id > 0:
                    max_id = 0
                    params["lastId"] = 0
                    continue

                for msg in chat_batch:
                    # Don't yield last chat message, only newer ones
                    if msg.id > max_id:
                        max_id = msg.id
                        params["lastEvt"] = max(0, msg.id - 1)
                        yield msg

            except ValidationError as e:
                logger.error(f"Validation error for Message: {e}")

    async def hud_messages(self) -> AsyncGenerator[Damage | Event, None]:
        max_evt_id = 0
        max_dmg_id = 0
        params = {"lastEvt": 0, "lastDmg": 0}

        async for resp in self._poll_endpoint(Endpoints.HUD_MSG, interval=1, params=params):
            try:
                hud_batch = HudMsg.model_validate_json(resp)

                # Reset if empty arrays are returned
                if not hud_batch.events and max_evt_id > 0:
                    max_evt_id = 0
                    params["lastEvt"] = 0

                if not hud_batch.damage and max_dmg_id > 0:
                    max_dmg_id = 0
                    params["lastDmg"] = 0

                for event in hud_batch.events:
                    if event.id > max_evt_id:
                        max_evt_id = event.id
                        params["lastEvt"] = max(0, event.id - 1)
                        yield event

                for dmg in hud_batch.damage:
                    if dmg.id > max_dmg_id:
                        max_dmg_id = dmg.id
                        params["lastDmg"] = max(0, dmg.id - 1)
                        yield dmg

            except ValidationError as e:
                logger.error(f"Validation error for HUDMessage: {e}")

    async def map_imgs(self) -> AsyncGenerator[bytes, None]:
        last_image = b""  # yield when map image changed
        async for resp in self._poll_endpoint(Endpoints.MAP_IMG, interval=1):
            if resp != last_image:
                last_image = resp
                yield resp

async def main():
    async with WtTelemetry() as telemetry:
        async for msg in telemetry.hud_messages():
            if isinstance(msg, Damage):
                logger.debug(msg)
            if isinstance(msg, Event):
                logger.error(msg)



if __name__ == "__main__":
    asyncio.run(main())
