from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, UlazRobeForm, IzlazRobeForm, UnosDobavljacaForm, UnosKupcaForm, UnosProizvodaForm, SearchForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Proizvod, Dobavljac, Kupac, EvidencijaUnosa, EvidencijaIzdavanja
from werkzeug.urls import url_parse
from datetime import datetime



@app.route('/index')
def index():
	return render_template('index.html', title='Home')

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user is None or not user.check_password(form.password.data):
			flash('Netočno korisničko ime ili lozinka!')
			return redirect(url_for('login'))
		login_user(user, remember=form.remember_me.data)
		next_page = request.args.get('next')
		if not next_page or url_parse(next_page).netloc != '':
			next_page = url_for('index')
		return redirect(next_page)
	return render_template('login.html', title='Prijavi se', form=form)

@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(username=form.username.data, email=form.email.data)
		user.set_password(form.password.data)
		db.session.add(user)
		db.session.commit()
		flash('Sada ste registrirani korisnik!')
		return redirect(url_for('login'))
	return render_template('register.html', title='Registriraj se', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
	user = User.query.filter_by(username=username).first_or_404()
	return render_template('user.html', user=user)

@app.before_request
def before_request():
	if current_user.is_authenticated:
		current_user.last_seen = datetime.utcnow()
		db.session.commit()

@app.route('/unos_proizvoda', methods=['GET', 'POST'])
@login_required
def unos_proizvoda():
	form = UnosProizvodaForm()
	if form.validate_on_submit():
		proizvod = Proizvod(name=form.name.data, zemlja_podrijetla=form.zemlja_podrijetla.data, kolicina=form.kolicina.data)
		db.session.add(proizvod)
		db.session.commit()
		flash('Dodali ste proizvod!')
		proizvod = Proizvod.query.filter_by(name=form.name.data).first()
		dobavljac = Dobavljac.query.filter_by(oib=form.oib.data).first()
		evidencija = EvidencijaUnosa(proizvod_id=proizvod.id, promijenjena_kolicina=proizvod.kolicina, dobavljac_id=dobavljac.id, user_id=current_user.id)
		db.session.add(evidencija)
		db.session.commit()
		dobavljac = Dobavljac.query.all()
		return redirect(url_for('unos_proizvoda'))
	return render_template('unos_proizvoda.html', title='Dodaj proizvod', form=form)

@app.route('/proizvod/<name>', methods=['GET', 'POST'])
@login_required
def proizvod(name):
	proizvod = Proizvod.query.filter_by(name=name).first_or_404()
	evidencija_unosa = EvidencijaUnosa.query.filter_by(proizvod_id=proizvod.id).order_by(EvidencijaUnosa.datum_unosa.desc()).all()
	evidencija_izdavanja = EvidencijaIzdavanja.query.filter_by(proizvod_id=proizvod.id).order_by(EvidencijaIzdavanja.datum_unosa.desc()).all()
	form_ulaz = UlazRobeForm()
	form_izlaz = IzlazRobeForm()
	if form_ulaz.submit1.data and form_ulaz.validate():
			dobavljac = Dobavljac.query.filter_by(oib=form_ulaz.oib.data).first_or_404()
			proizvod.kolicina += form_ulaz.promijenjena_kolicina.data
			evidencija = EvidencijaUnosa(proizvod_id=proizvod.id, dobavljac_id=dobavljac.id, promijenjena_kolicina=form_ulaz.promijenjena_kolicina.data, user_id=current_user.id)
			db.session.add(evidencija)
			db.session.commit()
			flash('Dodali ste kolicinu na stanje!')
			return redirect(url_for('proizvod', name=proizvod.name))
	if form_izlaz.submit2.data and form_izlaz.validate():
			kupac = Kupac.query.filter_by(oib=form_izlaz.oib.data).first_or_404()
			proizvod.kolicina -= form_izlaz.promijenjena_kolicina.data
			evidencija = EvidencijaIzdavanja(proizvod_id=proizvod.id, kupac_id=kupac.id, promijenjena_kolicina=form_izlaz.promijenjena_kolicina.data, user_id=current_user.id)
			db.session.add(evidencija)
			db.session.commit()
			flash('Oduzeli ste kolicinu sa stanja!')
			return redirect(url_for('proizvod', name=proizvod.name))
	return render_template('proizvod.html', title=proizvod.name, proizvod=proizvod, evidencija_unosa=evidencija_unosa, evidencija_izdavanja=evidencija_izdavanja, form_ulaz=form_ulaz, form_izlaz=form_izlaz)

@app.route('/stanje_skladista')
@login_required
def stanje_skladista():
	proizvodi = Proizvod.query.all()
	return render_template('stanje_skladista.html', title='Stanje skladista', proizvodi=proizvodi)

@app.route('/dobavljaci', methods=['GET', 'POST'])
@login_required
def dobavljaci():
	form = UnosDobavljacaForm()
	#dob = Dobavljac.query.all()
	if form.validate_on_submit():
		dobavljac = Dobavljac(name=form.name.data, oib=form.oib.data, grad=form.grad.data, 
			p_broj=form.p_broj.data, drzava=form.drzava.data)
		db.session.add(dobavljac)
		db.session.commit()
		flash('Uspješno ste unijeli dobavljača!')
		return redirect(url_for('dobavljaci'))
	else:
		dobavljaci = Dobavljac.query.all()
	return render_template('dobavljaci.html', title='Dodaj tvrtku dobavljača', form=form, dobavljaci=dobavljaci)

@app.route('/kupci', methods=['GET', 'POST'])
@login_required
def kupci():
	form = UnosKupcaForm()
	#dob = Dobavljac.query.all()
	if form.validate_on_submit():
		kupac = Kupac(name=form.name.data, oib=form.oib.data, grad=form.grad.data, 
			p_broj=form.p_broj.data, drzava=form.drzava.data)
		db.session.add(kupac)
		db.session.commit()
		flash('Uspješno ste unijeli kupca!')
		return redirect(url_for('kupci'))
	else:
		kupci = Kupac.query.all()
	return render_template('kupci.html', title='Dodaj tvrtku kupca', form=form, kupci=kupci)

@app.route('/evidencija_unosa')
@login_required
def evidencija_unosa():
	evidencija = EvidencijaUnosa.query.order_by(EvidencijaUnosa.datum_unosa.desc()).all()
	return render_template('evidencija_unosa.html', title='Evidencija unosa', evidencija=evidencija)

@app.route('/evidencija_izdavanja')
@login_required
def evidencija_izdavanja():
	evidencija = EvidencijaIzdavanja.query.order_by(EvidencijaIzdavanja.datum_unosa.desc()).all()
	return render_template('evidencija_izdavanja.html', title='Evidencija izdavanja', evidencija=evidencija)

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
	proizvodi = Proizvod.query.all()
	form = SearchForm()
	if form.validate_on_submit():
		search = form.search.data
		proizvodi = Proizvod.query.filter(Proizvod.name.like("%" + search + "%")).all()
		return render_template("search.html", form=form, proizvodi=proizvodi)
	
	return render_template("search.html", form=form, proizvodi=proizvodi)

