from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Noticia

noticias_bp = Blueprint('noticias_admin', __name__)


@noticias_bp.route('/')
@login_required
def index():
    noticias = Noticia.query.order_by(Noticia.creado_en.desc()).all()
    return render_template('noticias/index.html', noticias=noticias)


@noticias_bp.route('/nueva', methods=['GET', 'POST'])
@noticias_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def form(id=None):
    noticia = Noticia.query.get_or_404(id) if id else None

    if request.method == 'POST':
        titulo   = request.form.get('titulo', '').strip()
        resumen  = request.form.get('resumen', '').strip()
        cuerpo   = request.form.get('cuerpo', '').strip()
        categoria = request.form.get('categoria', 'general')
        publicada = bool(request.form.get('publicada'))
        imagen   = request.form.get('imagen_url', '').strip()

        if not titulo or not cuerpo:
            flash('Título y contenido son obligatorios.', 'danger')
        else:
            if noticia:
                noticia.titulo    = titulo
                noticia.resumen   = resumen
                noticia.cuerpo    = cuerpo
                noticia.categoria = categoria
                noticia.publicada = publicada
                noticia.imagen_url = imagen
                flash('Noticia actualizada.', 'success')
            else:
                noticia = Noticia(
                    titulo=titulo, resumen=resumen, cuerpo=cuerpo,
                    categoria=categoria, publicada=publicada,
                    imagen_url=imagen, autor_id=current_user.id
                )
                db.session.add(noticia)
                flash('Noticia creada.', 'success')
            db.session.commit()
            return redirect(url_for('noticias_admin.index'))

    categorias = ['general', 'resultado', 'fixture', 'disciplina', 'transferencia', 'institucional']
    return render_template('noticias/form.html', noticia=noticia, categorias=categorias)


@noticias_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar(id):
    noticia = Noticia.query.get_or_404(id)
    db.session.delete(noticia)
    db.session.commit()
    flash('Noticia eliminada.', 'info')
    return redirect(url_for('noticias_admin.index'))


@noticias_bp.route('/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_publicar(id):
    noticia = Noticia.query.get_or_404(id)
    noticia.publicada = not noticia.publicada
    db.session.commit()
    estado = 'publicada' if noticia.publicada else 'despublicada'
    flash(f'Noticia {estado}.', 'success')
    return redirect(url_for('noticias_admin.index'))
