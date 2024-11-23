import dataclasses
import typing
from datetime import datetime

import tzlocal
from dateutil import tz


@dataclasses.dataclass
class TimeInfo:
    @classmethod
    def create_from_env(cls) -> 'TimeInfo':
        raise NotImplementedError()

    def normalized_string(self) -> str:
        raise NotImplementedError()


@dataclasses.dataclass
class DT:
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int

    @classmethod
    def create_from_env(cls) -> 'DT':
        now = datetime.now()
        return cls(
            year=now.year,
            month=now.month,
            day=now.day,
            hour=now.hour,
            minute=now.minute,
            second=now.second,
        )


@dataclasses.dataclass
class PosixTimeInfo(TimeInfo):
    datetime: DT
    timezone_offset: int
    timezone_name: str

    @classmethod
    def create_from_env(cls) -> 'PosixTimeInfo':
        local_tz = tz.tzlocal()
        utc_offset = int(local_tz.utcoffset(datetime.now()).total_seconds() / 3600)
        # here are some formatting examples:
        # utc_offset_str = f"UTC{utc_offset:+03d}:00"
        # UTC-06:00
        # or
        # UTC{utc_offset}
        # UTC-6
        return cls(
            datetime=DT.create_from_env(),
            timezone_offset=utc_offset,
            timezone_name=tzlocal.get_localzone_name(),
        )

    def normalized_string(self) -> str:
        return f'{self.datetime.year:04d}-{self.datetime.month:02d}-{self.datetime.day:02d}_' \
               f'{self.datetime.hour:02d}-{self.datetime.minute:02d}-{self.datetime.second:02d}_' \
               f'UTC{self.timezone_offset:+03d}'


def from_dict(d: dict[str: typing.Any]) -> TimeInfo:
    if d['type'] == 'posix':
        return PosixTimeInfo(
            datetime=DT(**d['datetime']),
            timezone_offset=d['timezone_offset'],
            timezone_name=d['timezone_name'],
        )
    raise NotImplementedError(f'unknown time info type: {d["type"]}')


def to_dict(time_info: TimeInfo) -> dict[str: typing.Any]:
    if isinstance(time_info, PosixTimeInfo):
        return {
            'type': 'posix',
            'datetime': {
                'year': time_info.datetime.year,
                'month': time_info.datetime.month,
                'day': time_info.datetime.day,
                'hour': time_info.datetime.hour,
                'minute': time_info.datetime.minute,
                'second': time_info.datetime.second,
            },
            'timezone_offset': time_info.timezone_offset,
            'timezone_name': time_info.timezone_name,
        }
    raise NotImplementedError(f'unknown time info type: {type(time_info)}')
