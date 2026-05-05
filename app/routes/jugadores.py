from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required
from app import db
from app.models import Jugador, Serie, Equipo
from werkzeug.utils import secure_filename
from PIL import Image
import os
import uuid

jugadores_bp = Blueprint('jugadores', __name__)

POSICIONES = ['Portero', 'Defensa', 'Mediocampista', 'Delantero']


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def save_foto(file):
    """Guarda y redimensiona la foto del jugador. Retorna el nombre del archivo."""
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

    # Redimensionar con Pillow
    img = Image.open(file)
    img = img.convert('RGB')
    img.thumbnail((400, 400), Image.LANCZOS)
    img.save(path, optimize=True, quality=85)
    return filename


@jugadores_bp.route('/')
@login_required
def index():
    serie_id = request.args.get('serie_id', type=int)
    equipo_id = request.args.get('equipo_id', type=int)
    buscar = request.args.get('q', '').strip()

    query = Jugador.query.filter_by(activo=True)

    if serie_id:
        query = query.filter_by(serie_id=serie_id)
    if equipo_id:
        query = query.filter_by(equipo_id=equipo_id)
    if buscar:
        query = query.filter(
            db.or_(Jugador.nombre.ilike(f'%{buscar}%'), Jugador.rut.ilike(f'%{buscar}%'))
        )

    jugadores = query.order_by(Jugador.nombre).all()
    series = Serie.query.filter_by(activa=True).order_by(Serie.nombre).all()
    equipos = Equipo.query.filter_by(activo=True).order_by(Equipo.nombre).all()

    return render_template('jugadores/index.html',
        jugadores=jugadores, series=series, equipos=equipos,
        serie_id=serie_id, equipo_id=equipo_id, buscar=buscar)


@jugadores_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    series = Serie.query.filter_by(activa=True).order_by(Serie.nombre).all()
    equipos = Equipo.query.filter_by(activo=True).order_by(Equipo.nombre).all()

    if request.method == 'POST':
        rut = request.form.get('rut', '').strip()
        nombre = request.form.get('nombre', '').strip()
        fecha_nac_str = request.form.get('fecha_nac', '')
        posicion = request.form.get('posicion', '')
        serie_id = request.form.get('serie_id') or None
        equipo_id = request.form.get('equipo_id') or None

        if not rut or not nombre:
            flash('RUT y nombre son obligatorios.', 'danger')
        elif Jugador.query.filter_by(rut=rut).first():
            flash('Ya existe un jugador con ese RUT.', 'danger')
        else:
            from datetime import date
            fecha_nac = None
            if fecha_nac_str:
                try:
                    fecha_nac = date.fromisoformat(fecha_nac_str)
                except ValueError:
                    flash('Fecha de nacimiento inválida.', 'warning')

            foto_filename = None
            if 'foto' in request.files:
                foto = request.files['foto']
                if foto and foto.filename and allowed_file(foto.filename):
                    try:
                        foto_filename = save_foto(foto)
                    except Exception as e:
                        flash(f'Error al procesar la foto: {e}', 'warning')

            jugador = Jugador(
                rut=rut, nombre=nombre, fecha_nac=fecha_nac,
                posicion=posicion, foto=foto_filename,
                serie_id=serie_id, equipo_id=equipo_id
            )
            db.session.add(jugador)
            db.session.commit()
            flash(f'Jugador {nombre} registrado correctamente.', 'success')
            return redirect(url_for('jugadores.index'))

    return render_template('jugadores/form.html', series=series, equipos=equipos,
                           posiciones=POSICIONES, jugador=None)


@jugadores_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    jugador = Jugador.query.get_or_404(id)
    series = Serie.query.filter_by(activa=True).order_by(Serie.nombre).all()
    equipos = Equipo.query.filter_by(activo=True).order_by(Equipo.nombre).all()

    if request.method == 'POST':
        rut = request.form.get('rut', '').strip()
        nombre = request.form.get('nombre', '').strip()

        existente = Jugador.query.filter_by(rut=rut).first()
        if existente and existente.id != jugador.id:
            flash('Ese RUT ya pertenece a otro jugador.', 'danger')
        else:
            from datetime import date
            fecha_nac_str = request.form.get('fecha_nac', '')
            jugador.rut = rut
            jugador.nombre = nombre
            jugador.posicion = request.form.get('posicion', '')
            jugador.serie_id = request.form.get('serie_id') or None
            jugador.equipo_id = request.form.get('equipo_id') or None

            if fecha_nac_str:
                try:
                    jugador.fecha_nac = date.fromisoformat(fecha_nac_str)
                except ValueError:
                    pass

            if 'foto' in request.files:
                foto = request.files['foto']
                if foto and foto.filename and allowed_file(foto.filename):
                    try:
                        # Borrar foto anterior
                        if jugador.foto:
                            old = os.path.join(current_app.config['UPLOAD_FOLDER'], jugador.foto)
                            if os.path.exists(old):
                                os.remove(old)
                        jugador.foto = save_foto(foto)
                    except Exception as e:
                        flash(f'Error al procesar la foto: {e}', 'warning')

            db.session.commit()
            flash('Jugador actualizado correctamente.', 'success')
            return redirect(url_for('jugadores.index'))

    return render_template('jugadores/form.html', series=series, equipos=equipos,
                           posiciones=POSICIONES, jugador=jugador)


@jugadores_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar(id):
    jugador = Jugador.query.get_or_404(id)
    jugador.activo = False  # Soft delete
    db.session.commit()
    flash(f'Jugador {jugador.nombre} eliminado.', 'info')
    return redirect(url_for('jugadores.index'))


@jugadores_bp.route('/<int:id>')
@login_required
def detalle(id):
    jugador = Jugador.query.get_or_404(id)
    from app.models import Actividad
    actividades = Actividad.query.filter_by(jugador_id=id)\
        .order_by(Actividad.creado_en.desc()).all()
    return render_template('jugadores/detalle.html', jugador=jugador, actividades=actividades)
