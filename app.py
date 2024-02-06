from flask import Flask, jsonify, abort
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.automap import automap_base
import datetime as dt

# Create an engine and reflect the existing database
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, autoload_with=engine)

# Create a scoped session to ensure thread safety in a web app context
Session = scoped_session(sessionmaker(bind=engine))

app = Flask(__name__)

def get_date_one_year_ago():
    return dt.date.today() - dt.timedelta(days=365)

@app.route("/")
def home():
    return (
        f"Welcome to the Climate App API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    with Session() as session:
        one_year_ago = get_date_one_year_ago()
        precipitation_data = session.query(Base.classes.measurement.date, Base.classes.measurement.prcp).\
            filter(Base.classes.measurement.date >= one_year_ago).all()

        if not precipitation_data:
            abort(404, description="No precipitation data found.")

        precipitation_dict = {date: prcp for date, prcp in precipitation_data}

    return jsonify(precipitation_dict)

@app.route("/api/v1.0/stations")
def stations():
    with Session() as session:
        station_list = session.query(Base.classes.station.station).all()

        if not station_list:
            abort(404, description="No stations found.")

    return jsonify([station for station, in station_list])

@app.route("/api/v1.0/tobs")
def tobs():
    with Session() as session:
        one_year_ago = get_date_one_year_ago()
        most_active_station = session.query(Base.classes.measurement.station).\
            group_by(Base.classes.measurement.station).\
            order_by(func.count().desc()).first()

        if not most_active_station:
            abort(404, description="No active station found.")

        temperature_data = session.query(Base.classes.measurement.date, Base.classes.measurement.tobs).\
            filter(Base.classes.measurement.station == most_active_station[0]).\
            filter(Base.classes.measurement.date >= one_year_ago).all()

    return jsonify(temperature_data)

@app.route("/api/v1.0/<start>", defaults={'end': None})
@app.route("/api/v1.0/<start>/<end>")
def temperature_stats(start, end):
    with Session() as session:
        query = session.query(func.min(Base.classes.measurement.tobs), 
                              func.avg(Base.classes.measurement.tobs), 
                              func.max(Base.classes.measurement.tobs)).\
            filter(Base.classes.measurement.date >= start)
        
        if end:
            query = query.filter(Base.classes.measurement.date <= end)
        
        temperature_stats = query.all()

        if not temperature_stats:
            abort(404, description="No temperature data found.")

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
