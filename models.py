from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()

class Usuarios(db.Model):
    __tablename__ = 'usuarios'
    idUsuario = db.Column(db.Integer, primary_key=True)
    nombreUsuario = db.Column(db.String(100))
    correo = db.Column(db.String(100), unique=True)
    contrasena = db.Column(db.String(255))
    rol = db.Column(db.Enum('Admin', 'Ventas', 'Produccion', 'Cliente'))

class MateriasPrimas(db.Model):
    __tablename__ = 'materiasprimas'
    idMateriaPrima = db.Column(db.Integer, primary_key=True)
    materiaPrima = db.Column(db.String(100))
    cantidadDisponible = db.Column(db.Numeric(10, 2))
    unidadMedida = db.Column(db.String(100))
    fechaCaducidad = db.Column(db.Date)

class Proveedores(db.Model):
    __tablename__ = 'proveedores'
    idProveedor = db.Column(db.Integer, primary_key=True)
    nombreProveedor = db.Column(db.String(100))
    correo = db.Column(db.String(100))
    telefono = db.Column(db.String(20))

class ComprasInsumos(db.Model):
    __tablename__ = 'comprasinsumos'
    idCompra = db.Column(db.Integer, primary_key=True)
    idProveedor = db.Column(db.Integer, db.ForeignKey('proveedores.idProveedor'))
    idMateriaPrima = db.Column(db.Integer, db.ForeignKey('materiasprimas.idMateriaPrima'))
    cantidad = db.Column(db.Numeric(10, 2))
    fecha = db.Column(db.Date)

class Recetas(db.Model):
    __tablename__ = 'recetas'
    idReceta = db.Column(db.Integer, primary_key=True)
    nombreReceta = db.Column(db.String(100))

class IngredientesReceta(db.Model):
    __tablename__ = 'ingredientesreceta'
    idIngrediente = db.Column(db.Integer, primary_key=True)
    idReceta = db.Column(db.Integer, db.ForeignKey('recetas.idReceta'))
    idMateriaPrima = db.Column(db.Integer, db.ForeignKey('materiasprimas.idMateriaPrima'))
    cantidadNecesaria = db.Column(db.Numeric(10, 2))

class ProductosTerminados(db.Model):
    __tablename__ = 'productosterminados'
    idProducto = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    cantidadDisponible = db.Column(db.Integer)
    fechaCaducidad = db.Column(db.Date)
    tipoProducto = db.Column(db.String(30))
    estatus = db.Column(db.Integer, default=1)

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
    
    