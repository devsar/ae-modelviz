from google.appengine.ext import db
from google.appengine.ext.db import polymodel

class Owner(db.Model):
  first_name = db.StringProperty()
  last_name = db.StringProperty()

  def get_full_name(self):
    return u"%s %s" % (self.first_name, self.last_name)
  

class Vehicle(polymodel.PolyModel):
  owner = db.ReferenceProperty(Owner)
  model = db.StringProperty()

class Car(Vehicle):
  doors = db.StringProperty()

  

