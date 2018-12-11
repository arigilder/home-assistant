"""The tests for the Jewish calendar sensor platform."""
from collections import namedtuple
from datetime import time
from datetime import datetime as dt
from unittest.mock import patch

import pytest

from homeassistant.util.async_ import run_coroutine_threadsafe
from homeassistant.util.dt import get_time_zone, set_default_time_zone
from homeassistant.setup import setup_component
from homeassistant.components.sensor.jewish_calendar import (
    JewishCalSensor, CANDLE_LIGHT_DEFAULT)
from tests.common import get_test_home_assistant


_LatLng = namedtuple('_LatLng', ['lat', 'lng'])

NYC_LATLNG = _LatLng(40.7128, -74.0060)
JERUSALEM_LATLNG = _LatLng(31.778, 35.235)


def make_nyc_test_params(dtime, results):
    """Make test params for NYC."""
    return (dtime, CANDLE_LIGHT_DEFAULT, True,
            'America/New_York', NYC_LATLNG.lat, NYC_LATLNG.lng, results)


def make_jerusalem_test_params(dtime, results):
    """Make test params for Jerusalem."""
    return (dtime, CANDLE_LIGHT_DEFAULT, False,
            'Asia/Jerusalem', JERUSALEM_LATLNG.lat, JERUSALEM_LATLNG.lng,
            results)


class TestJewishCalenderSensor():
    """Test the Jewish Calendar sensor."""

    def setup_method(self, method):
        """Set up things to run when tests begin."""
        self.hass = get_test_home_assistant()

    def teardown_method(self, method):
        """Stop everything that was started."""
        self.hass.stop()
        # Reset the default timezone, so we don't affect other tests
        set_default_time_zone(get_time_zone('UTC'))

    def test_jewish_calendar_min_config(self):
        """Test minimum jewish calendar configuration."""
        config = {
            'sensor': {
                'platform': 'jewish_calendar'
            }
        }
        assert setup_component(self.hass, 'sensor', config)

    def test_jewish_calendar_hebrew(self):
        """Test jewish calendar sensor with language set to hebrew."""
        config = {
            'sensor': {
                'platform': 'jewish_calendar',
                'language': 'hebrew',
            }
        }

        assert setup_component(self.hass, 'sensor', config)

    def test_jewish_calendar_multiple_sensors(self):
        """Test jewish calendar sensor with multiple sensors setup."""
        config = {
            'sensor': {
                'platform': 'jewish_calendar',
                'sensors': [
                    'date', 'weekly_portion', 'holiday_name',
                    'holyness', 'first_light', 'gra_end_shma',
                    'mga_end_shma', 'plag_mincha', 'first_stars'
                ]
            }
        }

        assert setup_component(self.hass, 'sensor', config)

    test_params = [
        (dt(2018, 9, 3), 'UTC', 31.778, 35.235, "english", "date",
         False, "23 Elul 5778"),
        (dt(2018, 9, 3), 'UTC', 31.778, 35.235, "hebrew", "date",
         False, "כ\"ג אלול ה\' תשע\"ח"),
        (dt(2018, 9, 10), 'UTC', 31.778, 35.235, "hebrew", "holiday_name",
         False, "א\' ראש השנה"),
        (dt(2018, 9, 10), 'UTC', 31.778, 35.235, "english", "holiday_name",
         False, "Rosh Hashana I"),
        (dt(2018, 9, 10), 'UTC', 31.778, 35.235, "english", "holyness",
         False, 1),
        (dt(2018, 9, 8), 'UTC', 31.778, 35.235, "hebrew", "weekly_portion",
         False, "נצבים"),
        (dt(2018, 9, 8), 'America/New_York', 40.7128, -74.0060, "hebrew",
         "first_stars", True, time(19, 48)),
        (dt(2018, 9, 8), "Asia/Jerusalem", 31.778, 35.235, "hebrew",
         "first_stars", False, time(19, 21)),
        (dt(2018, 10, 14), "Asia/Jerusalem", 31.778, 35.235, "hebrew",
         "weekly_portion", False, "לך לך"),
        (dt(2018, 10, 14, 17, 0, 0), "Asia/Jerusalem", 31.778, 35.235,
         "hebrew", "date", False, "ה\' מרחשוון ה\' תשע\"ט"),
        (dt(2018, 10, 14, 19, 0, 0), "Asia/Jerusalem", 31.778, 35.235,
         "hebrew", "date", False, "ו\' מרחשוון ה\' תשע\"ט")
    ]

    test_ids = [
        "date_output",
        "date_output_hebrew",
        "holiday_name",
        "holiday_name_english",
        "holyness",
        "torah_reading",
        "first_stars_ny",
        "first_stars_jerusalem",
        "torah_reading_weekday",
        "date_before_sunset",
        "date_after_sunset"
    ]

    @pytest.mark.parametrize(["time", "tzname", "latitude", "longitude",
                              "language", "sensor", "diaspora", "result"],
                             test_params, ids=test_ids)
    def test_jewish_calendar_sensor(self, time, tzname, latitude, longitude,
                                    language, sensor, diaspora, result):
        """Test Jewish calendar sensor output."""
        tz = get_time_zone(tzname)
        set_default_time_zone(tz)
        test_time = tz.localize(time)
        self.hass.config.latitude = latitude
        self.hass.config.longitude = longitude
        sensor = JewishCalSensor(
            name='test', language=language, sensor_type=sensor,
            latitude=latitude, longitude=longitude,
            timezone=tz, diaspora=diaspora)
        sensor.hass = self.hass
        with patch('homeassistant.util.dt.now', return_value=test_time):
            run_coroutine_threadsafe(
                sensor.async_update(),
                self.hass.loop).result()
            assert sensor.state == result

    shabbat_params = [
        make_nyc_test_params(
            dt(2018, 9, 1, 16, 0),
            {'upcoming_shabbat_candle_lighting': dt(2018, 8, 31, 19, 15),
             'upcoming_shabbat_havdalah': dt(2018, 9, 1, 20, 14),
             'weekly_portion': 'Ki Tavo',
             'hebrew_weekly_portion': 'כי תבוא'}),
        make_nyc_test_params(
            dt(2018, 9, 1, 20, 21),
            {'upcoming_shabbat_candle_lighting': dt(2018, 9, 7, 19, 4),
             'upcoming_shabbat_havdalah': dt(2018, 9, 8, 20, 2),
             'weekly_portion': 'Nitzavim',
             'hebrew_weekly_portion': 'נצבים'}),
        make_nyc_test_params(
            dt(2018, 9, 7, 13, 1),
            {'upcoming_shabbat_candle_lighting': dt(2018, 9, 7, 19, 4),
             'upcoming_shabbat_havdalah': dt(2018, 9, 8, 20, 2),
             'weekly_portion': 'Nitzavim',
             'hebrew_weekly_portion': 'נצבים'}),
        make_nyc_test_params(
            dt(2018, 9, 8, 21, 25),
            {'upcoming_candle_lighting': dt(2018, 9, 9, 19, 1),
             'upcoming_havdalah': dt(2018, 9, 11, 19, 57),
             'upcoming_shabbat_candle_lighting': dt(2018, 9, 14, 18, 52),
             'upcoming_shabbat_havdalah': dt(2018, 9, 15, 19, 50),
             'weekly_portion': 'Vayeilech',
             'hebrew_weekly_portion': 'וילך',
             'holiday_name': 'Erev Rosh Hashana',
             'hebrew_holiday_name': 'ערב ראש השנה'}),
        make_nyc_test_params(
            dt(2018, 9, 9, 21, 25),
            {'upcoming_candle_lighting': dt(2018, 9, 9, 19, 1),
             'upcoming_havdalah': dt(2018, 9, 11, 19, 57),
             'upcoming_shabbat_candle_lighting': dt(2018, 9, 14, 18, 52),
             'upcoming_shabbat_havdalah': dt(2018, 9, 15, 19, 50),
             'weekly_portion': 'Vayeilech',
             'hebrew_weekly_portion': 'וילך',
             'holiday_name': 'Rosh Hashana I',
             'hebrew_holiday_name': "א' ראש השנה"}),
        make_nyc_test_params(
            dt(2018, 9, 10, 21, 25),
            {'upcoming_candle_lighting': dt(2018, 9, 10, 18, 59),
             'upcoming_havdalah': dt(2018, 9, 11, 19, 57),
             'upcoming_shabbat_candle_lighting': dt(2018, 9, 14, 18, 52),
             'upcoming_shabbat_havdalah': dt(2018, 9, 15, 19, 50),
             'weekly_portion': 'Vayeilech',
             'hebrew_weekly_portion': 'וילך',
             'holiday_name': 'Rosh Hashana II',
             'hebrew_holiday_name': "ב' ראש השנה"}),
        make_nyc_test_params(
            dt(2018, 9, 28, 21, 25),
            {'upcoming_shabbat_candle_lighting': dt(2018, 9, 28, 18, 28),
             'upcoming_shabbat_havdalah': dt(2018, 9, 29, 19, 25),
             'weekly_portion': 'none',
             'hebrew_weekly_portion': 'none'}),
        make_nyc_test_params(
            dt(2018, 9, 29, 21, 25),
            {'upcoming_candle_lighting': dt(2018, 9, 30, 18, 25),
             'upcoming_havdalah': dt(2018, 10, 2, 19, 20),
             # TODO add shabbat sensor
             'holiday_name': 'Hoshana Raba',
             'hebrew_holiday_name': 'הושענא רבה'}),
        make_nyc_test_params(
            dt(2018, 9, 30, 21, 25),
            {'upcoming_candle_lighting': dt(2018, 9, 30, 18, 25),
             'upcoming_havdalah': dt(2018, 10, 2, 19, 20),
             'holiday_name': 'Shmini Atzeret',
             'hebrew_holiday_name': 'שמיני עצרת'}),
        make_nyc_test_params(
            dt(2018, 10, 1, 21, 25),
            {'upcoming_candle_lighting': dt(2018, 10, 1, 18, 23),
             'upcoming_havdalah': dt(2018, 10, 2, 19, 20),
             'holiday_name': 'Simchat Torah',
             'hebrew_holiday_name': 'שמחת תורה'}),
        make_jerusalem_test_params(
            dt(2018, 9, 29, 21, 25),
            {'upcoming_candle_lighting': dt(2018, 9, 30, 18, 10),
             'upcoming_havdalah': dt(2018, 10, 1, 19, 2),
             'holiday_name': 'Hoshana Raba',
             'hebrew_holiday_name': 'הושענא רבה'}),
        make_jerusalem_test_params(
            dt(2018, 9, 30, 21, 25),
            {'upcoming_candle_lighting': dt(2018, 9, 30, 18, 10),
             'upcoming_havdalah': dt(2018, 10, 1, 19, 2),
             'holiday_name': 'Shmini Atzeret',
             'hebrew_holiday_name': 'שמיני עצרת'}),
        make_jerusalem_test_params(
            dt(2018, 10, 1, 21, 25),
            {'upcoming_shabbat_candle_lighting': dt(2018, 10, 5, 18, 3),
             'upcoming_shabbat_havdalah': dt(2018, 10, 6, 18, 56),
             'weekly_portion': 'Bereshit',
             'hebrew_weekly_portion': 'בראשית'}),
    ]

    shabbat_test_ids = [
        "currently_first_shabbat",
        "after_first_shabbat",
        "friday_upcoming_shabbat",
        "upcoming_rosh_hashana",
        "currently_rosh_hashana",
        "second_day_rosh_hashana",
        "currently_shabbat_chol_hamoed",
        "upcoming_two_day_yomtov_in_diaspora",
        "currently_first_day_of_two_day_yomtov_in_diaspora",
        "currently_second_day_of_two_day_yomtov_in_diaspora",
        "upcoming_one_day_yom_tov_in_israel",
        "currently_one_day_yom_tov_in_israel",
        "after_one_day_yom_tov_in_israel",
    ]
    @pytest.mark.parametrize(["now", "candle_lighting", "diaspora",
                              "tzname", "latitude", "longitude", "result"],
                             shabbat_params, ids=shabbat_test_ids)
    def test_shabbat_times_sensor(self, now, candle_lighting, 
                                  diaspora, tzname, latitude, longitude,
                                  result):
        """Test Shabbat Times sensor output."""
        
        tz = get_time_zone(tzname)
        set_default_time_zone(tz)
        test_time = tz.localize(now)
        for sensor_type, value in result.items():
            if isinstance(value, dt):
                result[sensor_type] = tz.localize(value)
        self.hass.config.latitude = latitude
        self.hass.config.longitude = longitude
        
        if ('upcoming_shabbat_candle_lighting' in result 
            and not 'upcoming_candle_lighting' in result):
            result['upcoming_candle_lighting'] = result['upcoming_shabbat_candle_lighting']
        if ('upcoming_shabbat_havdalah' in result 
            and not 'upcoming_havdalah' in result):
            result['upcoming_havdalah'] = result['upcoming_shabbat_havdalah']

        for sensor_type, result_value in result.items():
            language = 'english'
            if sensor_type.startswith('hebrew_'):
                language = 'hebrew'
                sensor_type = sensor_type.replace('hebrew_', '')
            sensor = JewishCalSensor(
                name='test', language=language, sensor_type=sensor_type,
                latitude=latitude, longitude=longitude,
                timezone=tz, diaspora=diaspora, 
                candle_lighting_offset=candle_lighting)
            sensor.hass = self.hass
            with patch('homeassistant.util.dt.now', return_value=test_time):
                run_coroutine_threadsafe(
                    sensor.async_update(),
                    self.hass.loop).result()
                assert sensor.state == result_value, "Value for {}".format(sensor_type)
