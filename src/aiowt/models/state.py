from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Any


class EngineData(BaseModel):
    throttle: int
    rpm_throttle: Optional[int] = None
    mixture: Optional[int] = None
    radiator: Optional[int] = None
    magneto: int
    power_hp: float
    rpm: int
    manifold_pressure_atm: float
    water_temp_c: Optional[int] = None
    oil_temp_c: int
    pitch_deg: float
    thrust_kgs: int
    efficiency: int


class State(BaseModel):
    valid: bool
    aileron: int = Field(alias="aileron, %")
    elevator: int = Field(alias="elevator, %")
    rudder: int = Field(alias="rudder, %")
    flaps: Optional[int] = Field(None, alias="flaps, %")
    gear: Optional[int] = Field(None, alias="gear, %")
    h_m: int = Field(alias="H, m")
    tas_kmh: int = Field(alias="TAS, km/h")
    ias_kmh: int = Field(alias="IAS, km/h")
    m: float = Field(alias="M")
    aoa_deg: float = Field(alias="AoA, deg")
    aos_deg: float = Field(alias="AoS, deg")
    ny: float = Field(alias="Ny")
    vy_ms: float = Field(alias="Vy, m/s")
    wx_degs: int = Field(alias="Wx, deg/s")
    mfuel_kg: int = Field(alias="Mfuel, kg")
    mfuel0_kg: int = Field(alias="Mfuel0, kg")
    engines: Dict[int, EngineData] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def extract_engines(cls, data: Any) -> Any:
        if isinstance(data, dict):
            engines = {}
            engine_fields = {}

            # Group engine data by engine number
            for key, value in list(data.items()):
                # Check if this is an engine-specific field
                parts = key.rsplit(" ", 1)
                if len(parts) == 2:
                    field_base = parts[0]
                    last_part = parts[1].rstrip(",%")

                    if last_part.isdigit():
                        engine_num = int(last_part)
                        if engine_num not in engine_fields:
                            engine_fields[engine_num] = {}
                        engine_fields[engine_num][field_base] = value

            # Convert to EngineData objects
            for engine_num, fields in engine_fields.items():
                engine_data = {
                    "throttle": fields.get("throttle, %"),
                    "rpm_throttle": fields.get("RPM throttle, %"),
                    "mixture": fields.get("mixture, %"),
                    "radiator": fields.get("radiator, %"),
                    "magneto": fields.get("magneto"),
                    "power_hp": fields.get("power, hp"),
                    "rpm": fields.get("RPM"),
                    "manifold_pressure_atm": fields.get("manifold pressure, atm"),
                    "water_temp_c": fields.get("water temp, C"),
                    "oil_temp_c": fields.get("oil temp, C"),
                    "pitch_deg": fields.get("pitch, deg"),
                    "thrust_kgs": fields.get("thrust, kgs"),
                    "efficiency": fields.get("efficiency, %"),
                }
                # Only create engine if we have the required fields
                if all(
                    engine_data[k] is not None
                    for k in [
                        "throttle",
                        "magneto",
                        "power_hp",
                        "rpm",
                        "manifold_pressure_atm",
                        "oil_temp_c",
                        "pitch_deg",
                        "thrust_kgs",
                        "efficiency",
                    ]
                ):
                    engines[engine_num] = EngineData(**engine_data)

            data["engines"] = engines

        return data
