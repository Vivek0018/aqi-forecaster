import js2py
import requests
from sseclient import SSEClient
import pandas

from typing import Any, Dict, List, Tuple, Union
import json
from datetime import datetime


JS_FUNCS: str = """
function checkValidDigitNumber(t) {
    return !isNaN(t) && parseInt(Number(t)) == t && !isNaN(parseInt(t, 10))
}

function a(backendData, n) {
    var e = 0,
        i = 0,
        r = 0,
        o = 1,
        resultArray = [];

    function s(t, r) {
        /* Variable r seems to uselessly bounce from 0 to 1 to 0 for no reason
           other than to obfuscate

           If r is 0 the code executes, otherwise it won't */

        for (0 == r && (r = 1); r > 0; r--) e++, i += t, resultArray.push({
            t: n(e), /** n seems to be a method to determine "which day of month" */
            v: i * o /** appears to be "value"? */
        })
    }

    function charInPositionIsDigit(t) {
        /* ASCII 48-57 is for 0-9 (digits) */
        return backendData.charCodeAt(t) >= 48 && backendData.charCodeAt(t) <= 57
    }
    for (var idx = 0; idx < backendData.length; idx++) {
        var u = function() {
                var t = 0,
                    n = 1;
                    /** 45 is ASCII for - and 46 is ASCII for . */
                for (45 == backendData.charCodeAt(idx + 1) && (n = -1, idx++); charInPositionIsDigit(idx + 1);) t = 10 * t + (backendData.charCodeAt(idx + 1) - 48), idx++;
                return 46 == backendData.charCodeAt(idx + 1) && idx++, n * t
            },
            h = backendData.charCodeAt(idx);
        if (0 == idx && 42 == h) o = 1 / u(), idx++;    /* 42 is ASCII for * */
        else if (36 == h) e += 1;           /* 36 is ASCII for $ */
        else if (37 == h) e += 2;           /* 37 is ASCII for % */
        else if (39 == h) e += 3;           /* 39 is ASCII for ' */
        else if (47 == h) o = u(), idx++;     /* 47 is ASCII for / */
        else if (33 == h) s(u(), r), r = 0; /* 33 is ASCII for ! */
        else if (124 == h) e += u() - 1;    /* 124 is ASCII for | */
        else if (h >= 65 && h <= 90) s(h - 65, r), r = 0;           /* This conditional is true when given ASCII for uppercase A-Z */
        else if (h >= 97 && h <= 122) s(-(h - 97) - 1, r), r = 0;   /* This conditional is true when given ASCII for lowercase a-z */
        else {
            if (!(h >= 48 && h <= 57)) throw "decode: invalid character " + h + " (" + backendData.charAt(idx) + ") at " + idx;
            r = 10 * r + h - 48
        }
    }
    return resultArray
}

function s(t) {
    /* NOTE: Appears to be the "main gun" since here's a try catch block */
    if (!t) return null;
    try {
        var n, e, i = [],
            r = {
                pm25: "PM<sub>2.5</sub>",
                pm10: "PM<sub>10</sub>",
                o3: "O<sub>3</sub>",
                no2: "NO<sub>2</sub>",
                so2: "SO<sub>2</sub>",
                co: "CO"
            },
            o = function() {
                try {
                    n = [];
                    var o = t.ps[s]; /* Long string backend data is o */
                    if ("1" == o[0]) n = a(o.substr(1), function(n) {
                        return {
                            d: c(new Date(3600 * (n * t.dh + t.st) * 1e3)), /** This expression results in 'seconds after Unix epoch' style value. st is an "hour after Unix epoch" value. */
                            t: n
                        }
                    });
                    else if ("2" == o[0]) {
                        e = {};
                        var d = "w" == o[1];
                        for (var l in o.substr(3).split("/").forEach(function(n) {
                                a(n, function(n) {
                                    if (d) {
                                        var e = n + t.st,
                                            i = e % 53;
                                        return {
                                            d: c(function(t, n, e) {
                                                var i = 2 + e + 7 * (n - 1) - new Date(t, 0, 1).getDay();
                                                return new Date(t, 0, i)
                                            }(a = (e - i) / 53, i, 0)),
                                            t: n
                                        }
                                    }
                                    var r = n + t.st,
                                        o = r % 12,
                                        a = (r - o) / 12;
                                    return {
                                        d: c(new Date(a, o)),
                                        t: n
                                    }
                                }).forEach(function(t) {
                                    var n = t.t.t;
                                    e[n] = e[n] || {
                                        v: [],
                                        t: t.t
                                    }, e[n].v.push(t.v)
                                })
                            }), e) n.push(e[l])
                    }
                    n.forEach(function(t, e) {
                        n[e].t.dh = e ? (t.t.d.getTime() - n[e - 1].t.d.getTime()) / 36e5 : 0
                    }), i.push({
                        name: r[s] || s,
                        values: n,
                        pol: s
                    })
                } catch (t) {
                    console.error("decode: Oopps...", t)
                }
            };
        for (var s in t.ps) o(); /* For each variable? do o()*/
        return i.sort(function(t, n) {
            var e = ["pm25", "pm10", "o3", "no2", "so2", "co"],
                i = e.indexOf(t.pol),
                r = e.indexOf(n.pol);
            return r < 0 ? 1 : i < 0 ? -1 : i - r
        }), {
            species: i,
            dailyhours: t.dh,
            source: t.meta.si,
            period: t.period
        }
    } catch (t) {
        return console.error("decode:", t), null
    }
}

function c(t) {
    return new Date(t.getUTCFullYear(), t.getUTCMonth(), t.getUTCDate(), t.getUTCHours(), t.getUTCMinutes(), t.getUTCSeconds())
}

function gatekeep_convert_date_object_to_unix_seconds(t) {
    /** Wrapper function:
        Perform decoding using s() function above, and afterwards convert all Date objects within
        the result into Unix timestamps, i.e. 'seconds since 1970/1/1'.
        This is necessary so that the Python context can convert that Unix timestamps back into datetime objects.
        js2py is unable to (at the time of writing, to my limited knowledge) convert JS Date objects into Python-understandable objects.
     */
    var RES = s(t)
    for(var i = 0; i < RES.species.length; i++){
    var values = RES.species[i].values
        for(var j = 0; j < values.length; j++){
            values[j].t.d = values[j].t.d.getTime()/1000
        }
    RES.species[i].values = values
    }
    return RES
}
"""


# NOTE(lahdjirayhan):
# The JS_FUNCS variable is a long string, a source JS code that
# is excerpted from one of aqicn.org frontend's scripts.
# See relevant_funcs.py for more information.


# Make js context where js code can be executed
_context = js2py.EvalJs()
_context.execute(JS_FUNCS)


def get_results_from_backend(city_id: int) -> List[Dict[str, Any]]:
    event_data_url = f"https://api.waqi.info/api/attsse/{city_id}/yd.json"

    r = requests.get(event_data_url)

    # Catch cases where the returned response is not a server-sent events,
    # i.e. an error.
    if "text/event-stream" not in r.headers["Content-Type"]:
        raise Exception(
            "Server does not return data stream. "
            f'It is likely that city ID "{city_id}" does not exist.'
        )

    client = SSEClient(event_data_url)
    result = []

    for event in client:
        if event.event == "done":
            break

        try:
            if "msg" in event.data:
                result.append(json.loads(event.data))
        except json.JSONDecodeError:
            pass

    return result


def parse_incoming_result(json_object: dict) -> pandas.DataFrame:
    # Run JS code
    # Function is defined within JS code above
    # Convert result to Python dict afterwards
    OUTPUT = _context.gatekeep_convert_date_object_to_unix_seconds(
        json_object["msg"]
    ).to_dict()

    result_dict = {}
    for spec in OUTPUT["species"]:
        pollutant_name: str = spec["pol"]

        dates, values = [], []
        for step in spec["values"]:
            # Change unix timestamp back to datetime
            date = datetime.fromtimestamp(step["t"]["d"])
            value: int = step["v"]

            dates.append(date)
            values.append(value)

        series = pandas.Series(values, index=dates)
        result_dict[pollutant_name] = series

    FRAME = pandas.DataFrame(result_dict)
    return FRAME


def get_data_from_id(city_id: int) -> pandas.DataFrame:
    backend_data = get_results_from_backend(city_id)
    result = pandas.concat([parse_incoming_result(data) for data in backend_data])
    # result = parse_incoming_result(backend_data[0])

    # Arrange to make most recent appear on top of DataFrame
    result = result.sort_index(ascending=False, na_position="last")

    # Deduplicate because sometimes the backend sends duplicates
    result = result[~result.index.duplicated()]

    # Reindex to make missing dates appear with value nan
    # Conditional is necessary to avoid error when trying to
    # reindex empty dataframe i.e. just in case the returned
    # response AQI data was empty.
    if len(result) > 1:
        complete_days = pandas.date_range(
            result.index.min(), result.index.max(), freq="D"
        )
        result = result.reindex(complete_days, fill_value=None)

        # Arrange to make most recent appear on top of DataFrame
        result = result.sort_index(ascending=False, na_position="last")

    return result