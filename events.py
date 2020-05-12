from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy 
from flask_marshmallow import Marshmallow 
import os
from datetime import datetime, timedelta


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'events.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)


class Event(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(100), unique=True)
  end_date = db.Column(db.Date)
  start_date = db.Column(db.Date)
  thumbnail = db.Column(db.Integer)

  def __init__(self, title, thumbnail, start_date, end_date):
    self.title = title
    self.thumbnail = thumbnail
    self.start_date = datetime.strptime(start_date, '%m-%d-%Y').date()
    self.end_date = datetime.strptime(end_date, '%m-%d-%Y').date()


class Reservation(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  reservation_code = db.Column(db.String(80))
  client_id = db.Column(db.Integer)
  
  def __init__(self, reservation_code, client_id):
    self.reservation_code = reservation_code
    self.client_id = client_id


class Client(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  reservation_code = db.Column(db.String(80))
  manager = db.Column(db.Boolean)
    
  def __init__(self, reservation_code, manager):
    self.reservation_code = reservation_code
    self.manager = manager


class EventSchema(ma.Schema):
  class Meta:
    fields = ('id', 'title', 'thumbnail', 'start_date', 'end_date')


class ReservationSchema(ma.Schema):
  class Meta:
    fields = ('id', 'reservation_code', 'client_id')


class ClientSchema(ma.Schema):
  class Meta:
    fields = ('id', 'reservation_code', 'manager')



event_schema = EventSchema()
events_schema = EventSchema(many=True)
client_schema = ClientSchema()
clients_schema = ClientSchema(many=True)
reservation_schema = ReservationSchema()
reservations_schema = ReservationSchema(many=True)


@app.route('/event', methods=['GET'])
def get_events():
  all_events = Event.query.all()
  result = events_schema.dump(all_events)
  
  return jsonify(result)


@app.route('/event', methods=['POST'])
def add_event():
  title = request.json['title']
  thumbnail = request.json['thumbnail']
  start_date = request.json['start_date']
  end_date = request.json['end_date']
  new_event = Event(title, thumbnail, start_date, end_date)
  db.session.add(new_event)
  db.session.commit()

  return event_schema.jsonify(new_event)


@app.route('/client', methods=['GET'])
def get_clients():
  all_clients = Client.query.all()
  result = clients_schema.dump(all_clients)
  return jsonify(result)


@app.route('/client', methods=['POST'])
def add_client():
  reservation_code = request.json['reservation_code']
  manager = request.json['manager']
  
  new_client = Client(reservation_code, manager)
  db.session.add(new_client)
  db.session.commit()

  return client_schema.jsonify(new_client)


@app.route('/reservation', methods=['GET'])
def get_reservation():
  all_reservations = Reservation.query.all()
  result = reservations_schema.dump(all_reservations)
  return jsonify(result)


@app.route('/reservation', methods=['POST'])
def post_reservation():
  reservation_code = request.json['reservation_code']
  client_id = request.json['client_id']
  new_reservation = Reservation(reservation_code, client_id)
  db.session.add(new_reservation)
  db.session.commit()

  return client_schema.jsonify(new_reservation)

@app.route('/reservation', methods=['DELETE'])
def delete_product():
  auth = request.authorization
  if Client.query.filter_by(id=auth.username).first().manager or \
  (Reservation.query.filter_by(client_id=auth.username).first() and \
    auth.password == Reservation.query.filter_by(client_id=auth.username).first().reservation_code):
  
    diff = str(Event.query.filter_by(id=2).first().end_date - \
      Event.query.filter_by(id=2).first().start_date)
    if str(diff)[0] != '0':
      reservation = Reservation.query.get(reservation_code)
      db.session.delete(reservation)
      db.session.commit() 
      return reservation_schema.jsonify(reservation)

  return jsonify({"message":"you don't have permission to delete"})

@app.route('/login')
def login():
  auth = request.authorization
  if auth.password == Reservation.query.filter_by(client_id=auth.username).first().reservation_code: 
    client = Client.query.filter_by(reservation_code=auth.password).first()
    return client_schema.jsonify(client)
  return jsonify({"message":"no reservations for your id"})

if __name__ == '__main__':
  app.run(debug=True)
