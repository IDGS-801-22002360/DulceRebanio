from app import create_app
from app.extensions import csrf, db

from app.models import Usuarios

app = create_app()

with app.app_context():
    print("Contexto de la aplicacion activo")
    usuario = Usuarios.query.first()
    print(usuario)

if __name__ == '__main__':
    csrf.init_app(app)
    
    with app.app_context():
        db.create_all()
    app.run()