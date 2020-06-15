#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime

import sys

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
migrate = Migrate(app, db)
db.create_all()

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
#show= db.Table('show', db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True),db.Column('artist', db.Integer, db.ForeignKey('Artist.id'), primary_key=True))

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, nullable=True)
    seeking_description = db.Column(db.String(500), nullable=True)
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    shows = db.relationship('Show', backref='venue', lazy=True)


class Artist(db.Model):
      __tablename__ = 'Artist'

      id = db.Column(db.Integer, primary_key=True)
      name = db.Column(db.String)
      city = db.Column(db.String(120))
      state = db.Column(db.String(120))
      phone = db.Column(db.String(120))
      image_link = db.Column(db.String(500))
      facebook_link = db.Column(db.String(120))

      # TODO: implement any missing fields, as a database migration using Flask-Migrate
      seeking_venue = db.Column(db.Boolean, nullable=True)
      genres = db.Column(db.ARRAY(db.String), nullable=False)
      website = db.Column(db.String(120))
      seeking_description = db.Column(db.String(500), nullable=True)
      shows = db.relationship('Show', backref='artist', lazy=True)


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'),
                          nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'),
                         nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

db.session.commit()
# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  # num_shows should be aggregated based on number of upcoming shows per venue.

  # retrive the data
    venues = Venue.query.all()
  #create list to store the venues 
    data = []
  # to save the location, render and compine the same venue under the same location
    location = ''
    length = len(data) - 1
   # loop through the Venue model 
    for v in venues:
        num_upcoming_shows = db.session.query(Venue).join(Show).filter(Venue.id == v.id, Show.start_time > datetime.now()).count()
       # check if the new venue's location alread known so we can postion it below it 
        if location == v.city + v.state:
            data[length]['venues'].append({
                'id': v.id,
                'name': v.name,
                'num_upcoming_shows': num_upcoming_shows
            })
        # new location new city and state are assigend    
        else:
            data.append({
                'city': v.city,
                'state': v.state,
                'venues': [{
                    'id': v.id,
                    'name': v.name,
                    'num_upcoming_shows': num_upcoming_shows
                }]
            })
            location = v.city + v.state

    return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  #venues = Venue.query.all()

  #take the user's input 
  search_term=request.form.get('search_term', '')
  # assing if there's any match and use the all 
  # function to retreve all the matches strings
  venues = Venue.query.filter(Venue.name.like('%{}%'.format(search_term))).all()
  
  response = {
    "count": len(venues),
    "data" : []
  }

    # loop throgh the possible strings, append the data
  for v in venues:
    
    #  and count the shows via joining the show and venuee 
      num_upcoming_shows = db.session.query(Venue).join(Show)\
      .filter(Venue.id == v.id, Show.start_time > datetime.now()).count()


      response['data'].append(
              {  "id": v.id,
                "name": v.name,
                "num_upcoming_shows": num_upcoming_shows}
      )

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # v = db.session.query(Venue).filter_by(id=venue_id)


  # to retrive the data for specifc venue we need to do a transaction with the db
    v= db.session.query(Venue).filter_by(id=venue_id).first()
  # we want the show model info so we can count the upcoming\past shows that intersect with a specific venue  
  # so when cline click for specifc venue and lets say its id is venue_id=4
  # in shows model we should receive all the venue_id that are assignd and same as what the cline asked for
    shows = Show.query.filter_by(venue_id=venue_id).all()
  # define array so we can append the information  
    data = []

    # render the upcoming shows 
    def upcoming_shows():
      # create empty arr
      upcoming_shows = []
      # loop through each show that we have recieved  
      for show in shows:
        # now compare the time of a specifc show if it's more than our current time 
          if show.start_time >= datetime.now():
            # if it is true and more than our current time then 
            # append the artist info in this venue because its still up coming
                upcoming_shows.append({
                  "artist_id": show.artist_id,
                  "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
                  "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
                  "start_time": str(show.start_time)
                  })
      return upcoming_shows

  #render past shows
    def past_shows():
 # create empty arr
        past_showsl = []
        # loop through each show that we have recieved 
        for show in shows:
          # now compare the time of a specifc show if it's less than our current time
            if show.start_time < datetime.now():
               # if it is true and less than our current time then 
               # append the artist info in this venue because its still up coming
                  past_showsl.append({
                        "artist_id": show.artist_id,
                        "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
                        "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
                        "start_time": str(show.start_time)
                    })
        return past_showsl

# assign the values we have recieved from the transction so the view can render it 
    data={
      "id": v.id,
      "name": v.name,
      "genres": v.genres,
      "address": v.address,
      "city": v.city,
      "state": v.state,
      "phone": v.phone,
      "website": v.website,
      "facebook_link": v.facebook_link,
      "seeking_talent": v.seeking_talent,
      "seeking_description": v.seeking_description,
      "image_link": v.image_link,

      "past_shows": past_shows(),
      "upcoming_shows": upcoming_shows(),
      "past_shows_count": len(past_shows()),
      "upcoming_shows_count": len(upcoming_shows())
    }

  
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id


  # data = list(filter(lambda d: d['id'] == 1, [data]))
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

      form = VenueForm()

      try:
       # Based on the data that assigned from the user in the VenueForm 
       # we going to collect it and add it to the db
        new_venue= Venue(
            name =request.form['name'],
            city= request.form['city'],
            state= request.form['state'],
            address= request.form['address'],
            phone=  request.form['phone'],
            genres= request.form['genres'],
            facebook_link= request.form['facebook_link'],
          )

        db.session.add(new_venue)
        db.session.commit()
        flash('Venue ' + form['name'].data + ' was successfully added!')

      except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be listed. ')
      finally:
        db.session.close()

    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion

      return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:     
    
    # Venue.query.get(venue_id).delete()
    # query = Venue.query.get(id=venue_id)
    # query.delete()
    #

    #take the request with the id from the View and execute it 
    Venue.query.filter(Venue.id == venue_id).delete()
    db.session.commit()
    print("del")
  except:
    db.session.rollback()
    print("No del")
  finally:
    db.session.close()
  
  # return jsonify({ 'success': True })
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database


# retrieve all the artists we have in the db
  artist = Artist.query.all()
  data = []

# loop throgh each one and append it to the array so the view can render it
  for a in artist:
    data.append({
       "id": a.id,
       "name": a.name
    })


  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".


  #take the user's input 
  search_term=request.form.get('search_term', '')
   # assing if there's any match and use the all 
  # function to retreve all the matches strings
  artists = Artist.query.filter(Artist.name.like('%{}%'.format(search_term))).all()
  response = {
    "count": len(artists),
    "data" : []
  }

# loop throgh the possible strings, append the data
  for a in artists:

    #  and count the shows via joining the show and venuee 
      num_upcoming_shows = db.session.query(Artist).join(Show)\
      .filter(Artist.id == a.id, Show.start_time > datetime.now()).count()

      
      response['data'].append(
              {  "id": a.id,
                "name": a.name,
                "num_upcoming_shows": num_upcoming_shows}
      )
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

##########################################################################################
  # FOR MORE EXPLNATION ABOUT THE CODE CHECK THE show_venue(venue_id)
##########################################################################################


  artist = db.session.query(Artist).filter_by(id=artist_id).first()

  shows = Show.query.filter_by(artist_id=artist_id).all()

  def upcoming_shows():
      upcoming_shows = []
      for show in shows:
          if show.start_time >= datetime.now():
                upcoming_shows.append({
                    "venue_id": show.venue_id,
                    "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
                    "venue_image_link": Venue.query.filter_by(id=show.venue_id).first().image_link,
                    "start_time": str(show.start_time)
                })
      return upcoming_shows


  def past_shows():
      past_shows = []
      for show in shows:
          if show.start_time < datetime.now():
                past_shows.append({
                     "venue_id": show.venue_id,
                     "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
                     "venue_image_link": Venue.query.filter_by(id=show.venue_id).first().image_link,
                     "start_time": str(show.start_time)
                  })
      return past_shows


  data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows(),
        "upcoming_shows": upcoming_shows(),
        "past_shows_count": len(past_shows()),
        "upcoming_shows_count": len(upcoming_shows())
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  form = ArtistForm()
  
  #send the specifc atrist record to the view 
  artist = Artist.query.filter(Artist.id == artist_id).one()

  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes


    update= ArtistForm(request.form)
    try:
        #retrive the record for specidfec artist 
        artist = Artist.query.filter(Artist.id == artist_id).one()
          #replace the old values with the new ones for each feild 
        artist.name = update.name.data,
        artist.genres = ','.join(update.genres.data),
        artist.city = update.city.data,
        artist.state = update.state.data,
        artist.phone = update.phone.data,
        artist.facebook_link = update.facebook_link.data,
        artist.image_link = update.image_link.data,
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully updated!')
    except:
        db.session.rollback()
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be updated.')
    finally:
        db.session.close()
    
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  #venue = Venue.query.filter(Venue.id == venue_id)
  venue=Venue.query.filter(Venue.id == venue_id).one()
  
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
    update= VenueForm(request.form)
    try:
        venue = Venue.query.filter(Venue.id == venue_id).one()
        venue.name = update.name.data,
        venue.address = update.address.data,
        venue.genres = ','.join(update.genres.data),
        venue.city = update.city.data,
        venue.state = update.state.data,
        venue.phone = update.phone.data,
        venue.facebook_link = update.facebook_link.data,
        venue.image_link = update.image_link.data,
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully updated!')
    except:
        db.session.rollback()
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be updated.')
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion


      form = ArtistForm()

      try:
        new_artist= Artist(
            name =request.form['name'],
            city= request.form['city'],
            state= request.form['state'],
            phone=  request.form['phone'],
            genres= request.form['genres'],
            facebook_link= request.form['facebook_link'],
          )

        db.session.add(new_artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')

      except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Artist ' + data.name + ' could not be listed.')
      finally:
        db.session.close()
  # on successful db insert, flash success
  
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., 
      return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

#create empty array 
    data = []
# retrive all the info from the forigen models so the vies can render the shows
    shows = db.session.query(Show, Venue.name, Artist).join(Venue, Artist)

# loop throgh each show and render its infr
# and in each show loop into each forigen model to catch the data and append it 
    for sh, v_name, artist in shows:
        data.append({
            'venue_id': sh.venue_id,
            'venue_name': v_name,
            'artist_id': sh.artist_id,
            'artist_name': artist.name,
            'artist_image_link': artist.image_link,
            'start_time': str(sh.start_time)
        })


    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

      form = ShowForm()

      try:
        #creates new shows 
        new_show= Show(
            artist_id =request.form['artist_id'],
            venue_id= request.form['venue_id'],
            start_time = request.form['start_time']

          )

        db.session.add(new_show)
        db.session.commit()
        flash('Show was successfully listed!')

      except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Show could not be listed.')
      finally:
        db.session.close()
  # on successful db insert, f
  # on successful db insert, flash success
 
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., 
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
