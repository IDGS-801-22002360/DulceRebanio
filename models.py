from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import hashlib
import datetime

db = SQLAlchemy()

class Usuarios(db.Model, UserMixin): 
    __tablename__ = 'usuarios'
    idUsuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100)) 
    apaterno = db.Column(db.String(100))
    amaterno = db.Column(db.String(100)) 
    correo = db.Column(db.String(100), unique=True)
    contrasena = db.Column(db.String(64))
    rol = db.Column(db.Enum('Admin', 'Ventas', 'Produccion', 'Cliente'))
    activo = db.Column(db.Integer, default=1)
    ultimo_login = db.Column(db.DateTime)
    otp_secret = db.Column(db.String(16)) 
    otp_verified = db.Column(db.Boolean, default=False) 
    registration_data = db.Column(db.JSON)  
    

    def set_contrasena(self, contrasena):
        self.contrasena = hashlib.sha256(contrasena.encode('utf-8')).hexdigest()

    def check_contrasena(self, contrasena):
        return self.contrasena == hashlib.sha256(contrasena.encode('utf-8')).hexdigest()

    def get_id(self):
        return str(self.idUsuario)


class MateriasPrimas(db.Model):
    __tablename__ = 'materiasprimas'
    idMateriaPrima = db.Column(db.Integer, primary_key=True)
    materiaPrima = db.Column(db.String(100))
    cantidadDisponible = db.Column(db.Numeric(10, 2))
    unidadMedida = db.Column(db.String(100))
    fechaCaducidad = db.Column(db.Date)
    estatus = db.Column(db.Integer, default=1)

class Proveedores(db.Model):
    __tablename__ = 'proveedores'
    idProveedor = db.Column(db.Integer, primary_key=True)
    nombreProveedor = db.Column(db.String(100))
    correo = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    estatus = db.Column(db.Integer, default=1)

class ComprasInsumos(db.Model):
    __tablename__ = 'comprasinsumos'
    idCompra = db.Column(db.Integer, primary_key=True)
    idProveedor = db.Column(db.Integer, db.ForeignKey('proveedores.idProveedor'))
    idMateriaPrima = db.Column(db.Integer, db.ForeignKey('materiasprimas.idMateriaPrima'))
    cantidad = db.Column(db.Numeric(10, 2))
    fecha = db.Column(db.Date)
    totalCompra = db.Column(db.Numeric(10,2))

#!==================================================================================

class Receta(db.Model):
    __tablename__ = 'recetas'
    idReceta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombreReceta = db.Column(db.String(100), unique=True, nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False, default=7)
    imagen = db.Column(db.Text)
    estatus = db.Column(db.Integer, default=1)

    detalles = db.relationship('RecetaDetalle', backref='receta', cascade='all, delete-orphan')

class RecetaDetalle(db.Model):
    __tablename__ = 'recetadetalle'
    idRecetaDetalle = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idReceta = db.Column(db.Integer, db.ForeignKey('recetas.idReceta', ondelete='CASCADE'), nullable=False)
    idMateriaPrima = db.Column(db.Integer, db.ForeignKey('materiasprimas.idMateriaPrima', ondelete='CASCADE'), nullable=False)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False)
    unidadMedida = db.Column(db.String(20), nullable=False)

class ProductosTerminados(db.Model):
    __tablename__ = 'productosterminados'
    idProducto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idReceta = db.Column(db.Integer, db.ForeignKey('recetas.idReceta', ondelete='CASCADE'), nullable=False)
    cantidadDisponible = db.Column(db.Integer)
    fechaCaducidad = db.Column(db.Date)
    estatus = db.Column(db.Integer, default=1)

#!==================================================================================

class Ventas(db.Model):
    __tablename__ = 'ventas'
    idVenta = db.Column(db.Integer, primary_key=True)
    idUsuario = db.Column(db.Integer, db.ForeignKey('usuarios.idUsuario'))
    fecha = db.Column(db.Date)
    total = db.Column(db.Numeric(10, 2))

class DetallesVenta(db.Model):
    __tablename__ = 'detallesventa'
    idDetalle = db.Column(db.Integer, primary_key=True)
    idVenta = db.Column(db.Integer, db.ForeignKey('ventas.idVenta'))
    idProducto = db.Column(db.Integer, db.ForeignKey('productosterminados.idProducto'))
    cantidad = db.Column(db.Integer)
    subtotal = db.Column(db.Numeric(10, 2))

class Pedidos(db.Model):
    __tablename__ = 'pedidos'
    idPedido = db.Column(db.Integer, primary_key=True)
    idUsuario = db.Column(db.Integer, db.ForeignKey('usuarios.idUsuario'))
    fechaPedido = db.Column(db.Date)
    fechaEntrega = db.Column(db.Date)
    estatus = db.Column(db.Enum('Pendiente', 'En produccion', 'Listo', 'Entregado'))

class DetallesPedido(db.Model):
    __tablename__ = 'detallespedido'
    idDetallePedido = db.Column(db.Integer, primary_key=True)
    idPedido = db.Column(db.Integer, db.ForeignKey('pedidos.idPedido'))
    idProducto = db.Column(db.Integer, db.ForeignKey('productosterminados.idProducto'))
    cantidad = db.Column(db.Integer)

    

class VentasCliente(db.Model):
    __tablename__ = 'ventascliente'
    idVentasCliente = db.Column(db.Integer, primary_key=True)
    nombreCliente = db.Column(db.String(100))
    nombreSabor = db.Column(db.String(100))
    cantidad = db.Column(db.Integer)
    tipoProducto = db.Column(db.String(100))
    total = db.Column(db.Float)
    estatus=db.Column(db.Integer, default=1) 
