from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
import datetime as dt
import numpy as np

# Create an engine and reflect the existing database
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect=True)

# Set up the Flask app
app = Flask(__name__)

# Create route(s)
@app.route("/")
def home():
    return (
        f"Welcome to the Climate App API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start_date<br/>"
        f"/api/v1.0/start_date/end_date"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    # Query to retrieve the last 12 months of precipitation data
    one_year_ago = dt.date.today() - dt.timedelta(days=365)
    precipitation_data = session.query(Base.classes.measurement.date, Base.classes.measurement.prcp).\
        filter(Base.classes.measurement.date >= one_year_ago).all()
    session.close()
    
    # Convert the query results to a dictionary with date as the key and prcp as the value
    precipitation_dict = {date: prcp for date, prcp in precipitation_data}

    return jsonify(precipitation_dict)

@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    # Query to retrieve the list of stations
    station_list = session.query(Base.classes.station.station).all()
    session.close()

    stations = list(np.ravel(station_list))

    return jsonify(stations)

@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    # Query to retrieve the temperature observations for the most active station in the last 12 months
    one_year_ago = dt.date.today() - dt.timedelta(days=365)
    most_active_station = session.query(Base.classes.measurement.station).\
        group_by(Base.classes.measurement.station).\
        order_by(func.count().desc()).first()[0]
    temperature_data = session.query(Base.classes.measurement.date, Base.classes.measurement.tobs).\
        filter(Base.classes.measurement.station == most_active_station).\
        filter(Base.classes.measurement.date >= one_year_ago).all()
    session.close()

    return jsonify(temperature_data)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_stats(start, end=None):
    session = Session(engine)
    # Query to calculate temperature statistics based on the specified start and end dates
    if end:
        temperature_stats = session.query(func.min(Base.classes.measurement.tobs), 
                                          func.avg(Base.classes.measurement.tobs), 
                                          func.max(Base.classes.measurement.tobs)).\
            filter(Base.classes.measurement.date >= start).\
            filter(Base.classes.measurement.date <= end).all()
    else:
        temperature_stats = session.query(func.min(Base.classes.measurement.tobs), 
                                          func.avg(Base.classes.measurement.tobs), 
                                          func.max(Base.classes.measurement.tobs)).\
            filter(Base.classes.measurement.date >= start).all()
    session.close()

    # Create a dictionary to store the temperature statistics
    stats_dict = {
        "start_date": start,
        "end_date": end,
        "min_temperature": temperature_stats[0][0],
        "avg_temperature": temperature_stats[0][1],
        "max_temperature": temperature_stats[0][2]
    }

    return jsonify(stats_dict)

if __name__ == '__main__':
    app.run(debug=True)