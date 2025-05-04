# supermag
A small python package for reading and handling SuperMAG files.

## Web API
The submodule `supermag_api` is a testbed for a interfacing with Supermag's
web API. It serves as a replacement for the API provided by JHU APL.
Rather than rely on Pandas, it places the resulting data into Spacepy
datamodels.

This submodule is experimental. It will eventually be moved to Spacepy. It is
still under active development so expect behavior change in the future.

**NOTE: Fetching from SuperMAG is SLOW. It is recommended that you fetch data
ONCE and then save it to your local machine.**

You will need a SuperMAG log in name to use this module.

### Example: Fetching Geomagnetic Indexes

Start by setting a start and end time for the period of interest.
In this example, we examine the Gannon Storm from May, 2024.

```
import datetime as dt
t_start = dt.datetime(2024, 5, 10, 0, 0)
t_end = dt.datetime(2024, 5, 15, 0, 0)
```

Next, fetch the geomagnetic index data:

```
from supermag_api import fetch_index
# ...or run the module as a script.

data = fetch_index(t_start, t_end, 'YOUR LOGIN NAME HERE')
```

The data is returned as a spacepy DataModel object, so the normal rules
apply: access data by key (e.g., `data['smr']`, `data['time']`, etc.); use
the `attrs` attribute to find and set data attributes, etc.
`data.keys()` will show all keys available in the data structure.
You may also use the built-in data storage methods to convert the data to
JSON-headed ASCII, HDF5, or CDF file formats.

Finally, plot, manipulate, or save the data.

```
import matplotlib.pyplot as plt

# Let's make a plot of SMU and SML:
plt.plot(data['time'], data['SMU'], label='SMU')
plt.plot(data['time'], data['SML'], label='SML')
plt.legend()

# Drop the data to JSON-headed ASCII for future use:
data.toJSONheadedASCII('supermag_indexes.txt')

# ...and reload the data thusly:
from spacepy.datamodel import readJSONheadedASCII
data2 = readJSONheadedASCII('./supermag_indexes.txt')
```

### Values returned by `fetch_index`

| Variable(s) | Description |
|-------------|-------------|
| tval, time  |
tval,SME,SML,SMLmlat,SMLmlt,SMLglat,SMLglon'.split(',') + \
    'SMU,SMUmlat,SMUmlt,SMUglat,SMUglon,smr