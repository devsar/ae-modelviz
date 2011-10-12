from google.appengine.ext import db
from google.appengine.ext.db import polymodel

class Owner(db.Model):
  first_name = db.StringProperty()
  last_name = db.StringProperty()

  def get_full_name(self):
    return u"%s %s" % (self.first_name, self.last_name)
  

class Vehicle(polymodel.PolyModel):
  model = db.StringProperty()

class Car(Vehicle):
  owner = db.ReferenceProperty(Owner)
  doors = db.IntegerProperty()


class Truck(Vehicle):
  tare = db.IntegerProperty()

class Ship(Vehicle):
  hulls = db.IntegerProperty()
  

