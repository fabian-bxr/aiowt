from pydantic import BaseModel


class TankIndicator(BaseModel):
    valid: bool
    army: str
    type: str
    stabilizer: float
    gear: float
    gear_neutral: float
    speed: float
    has_speed_warning: float
    rpm: float
    driving_direction_mode: float
    cruise_control: float
    lws: float
    ircm: float
    roll_indicators_is_available: float
    first_stage_ammo: float
    crew_total: float
    crew_current: float
    crew_distance: float
    gunner_state: float
    driver_state: float
