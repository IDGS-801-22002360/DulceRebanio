-- MySQL dump 10.13  Distrib 8.0.33, for Win64 (x86_64)
--
-- Host: localhost    Database: dongalleto
-- ------------------------------------------------------
-- Server version	8.0.33

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `comprasinsumos`
--

DROP TABLE IF EXISTS `comprasinsumos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `comprasinsumos` (
  `idCompra` int NOT NULL AUTO_INCREMENT,
  `idProveedor` int DEFAULT NULL,
  `idMateriaPrima` int DEFAULT NULL,
  `cantidad` decimal(10,2) DEFAULT NULL,
  `fecha` date DEFAULT NULL,
  `totalCompra` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`idCompra`),
  KEY `idProveedor` (`idProveedor`),
  KEY `idMateriaPrima` (`idMateriaPrima`),
  CONSTRAINT `comprasinsumos_ibfk_1` FOREIGN KEY (`idProveedor`) REFERENCES `proveedores` (`idProveedor`),
  CONSTRAINT `comprasinsumos_ibfk_2` FOREIGN KEY (`idMateriaPrima`) REFERENCES `materiasprimas` (`idMateriaPrima`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comprasinsumos`
--

LOCK TABLES `comprasinsumos` WRITE;
/*!40000 ALTER TABLE `comprasinsumos` DISABLE KEYS */;
/*!40000 ALTER TABLE `comprasinsumos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detallespedido`
--

DROP TABLE IF EXISTS `detallespedido`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detallespedido` (
  `idDetallePedido` int NOT NULL AUTO_INCREMENT,
  `idPedido` int DEFAULT NULL,
  `idProducto` int DEFAULT NULL,
  `cantidad` int DEFAULT NULL,
  PRIMARY KEY (`idDetallePedido`),
  KEY `idPedido` (`idPedido`),
  KEY `idProducto` (`idProducto`),
  CONSTRAINT `detallespedido_ibfk_1` FOREIGN KEY (`idPedido`) REFERENCES `pedidos` (`idPedido`),
  CONSTRAINT `detallespedido_ibfk_2` FOREIGN KEY (`idProducto`) REFERENCES `productosterminados` (`idProducto`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detallespedido`
--

LOCK TABLES `detallespedido` WRITE;
/*!40000 ALTER TABLE `detallespedido` DISABLE KEYS */;
/*!40000 ALTER TABLE `detallespedido` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detallesproducto`
--

DROP TABLE IF EXISTS `detallesproducto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detallesproducto` (
  `idDetalle` int NOT NULL AUTO_INCREMENT,
  `tipoProducto` varchar(30) NOT NULL,
  `precio` decimal(10,2) NOT NULL,
  PRIMARY KEY (`idDetalle`),
  UNIQUE KEY `tipoProducto` (`tipoProducto`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detallesproducto`
--

LOCK TABLES `detallesproducto` WRITE;
/*!40000 ALTER TABLE `detallesproducto` DISABLE KEYS */;
INSERT INTO `detallesproducto` VALUES (1,'Granel',7.00),(2,'Kilo',50.00),(3,'Med. Kilo',35.00);
/*!40000 ALTER TABLE `detallesproducto` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detallesventa`
--

DROP TABLE IF EXISTS `detallesventa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detallesventa` (
  `idDetalle` int NOT NULL AUTO_INCREMENT,
  `idVenta` int DEFAULT NULL,
  `idProducto` int DEFAULT NULL,
  `cantidad` int DEFAULT NULL,
  `subtotal` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`idDetalle`),
  KEY `idVenta` (`idVenta`),
  KEY `idProducto` (`idProducto`),
  CONSTRAINT `detallesventa_ibfk_1` FOREIGN KEY (`idVenta`) REFERENCES `ventas` (`idVenta`),
  CONSTRAINT `detallesventa_ibfk_2` FOREIGN KEY (`idProducto`) REFERENCES `productosterminados` (`idProducto`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detallesventa`
--

LOCK TABLES `detallesventa` WRITE;
/*!40000 ALTER TABLE `detallesventa` DISABLE KEYS */;
/*!40000 ALTER TABLE `detallesventa` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ingredientesreceta`
--

DROP TABLE IF EXISTS `ingredientesreceta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ingredientesreceta` (
  `idIngrediente` int NOT NULL AUTO_INCREMENT,
  `idReceta` int DEFAULT NULL,
  `idMateriaPrima` int DEFAULT NULL,
  `cantidadNecesaria` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`idIngrediente`),
  KEY `idReceta` (`idReceta`),
  KEY `idMateriaPrima` (`idMateriaPrima`),
  CONSTRAINT `ingredientesreceta_ibfk_1` FOREIGN KEY (`idReceta`) REFERENCES `recetas` (`idReceta`),
  CONSTRAINT `ingredientesreceta_ibfk_2` FOREIGN KEY (`idMateriaPrima`) REFERENCES `materiasprimas` (`idMateriaPrima`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ingredientesreceta`
--

LOCK TABLES `ingredientesreceta` WRITE;
/*!40000 ALTER TABLE `ingredientesreceta` DISABLE KEYS */;
/*!40000 ALTER TABLE `ingredientesreceta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `materiasprimas`
--

DROP TABLE IF EXISTS `materiasprimas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `materiasprimas` (
  `idMateriaPrima` int NOT NULL AUTO_INCREMENT,
  `materiaPrima` varchar(100) DEFAULT NULL,
  `cantidadDisponible` decimal(10,2) DEFAULT NULL,
  `unidadMedida` varchar(100) DEFAULT NULL,
  `fechaCaducidad` date DEFAULT NULL,
  `estatus` int DEFAULT '1',
  `idProveedor` int DEFAULT NULL,
  `precioUnitario` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`idMateriaPrima`),
  KEY `idProveedor` (`idProveedor`),
  CONSTRAINT `materiasprimas_ibfk_1` FOREIGN KEY (`idProveedor`) REFERENCES `proveedores` (`idProveedor`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `materiasprimas`
--

LOCK TABLES `materiasprimas` WRITE;
/*!40000 ALTER TABLE `materiasprimas` DISABLE KEYS */;
INSERT INTO `materiasprimas` VALUES (1,'Leche',0.00,'Mililitros','2025-04-29',0,NULL,NULL),(2,'Harina',0.00,'Kilogramos',NULL,1,1,18.00);
/*!40000 ALTER TABLE `materiasprimas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pedidos`
--

DROP TABLE IF EXISTS `pedidos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pedidos` (
  `idPedido` int NOT NULL AUTO_INCREMENT,
  `idUsuario` int DEFAULT NULL,
  `fechaPedido` date DEFAULT NULL,
  `fechaEntrega` date DEFAULT NULL,
  `estatus` enum('Pendiente','En producción','Listo','Entregado') DEFAULT NULL,
  PRIMARY KEY (`idPedido`),
  KEY `idUsuario` (`idUsuario`),
  CONSTRAINT `pedidos_ibfk_1` FOREIGN KEY (`idUsuario`) REFERENCES `usuarios` (`idUsuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pedidos`
--

LOCK TABLES `pedidos` WRITE;
/*!40000 ALTER TABLE `pedidos` DISABLE KEYS */;
/*!40000 ALTER TABLE `pedidos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `productosterminados`
--

DROP TABLE IF EXISTS `productosterminados`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `productosterminados` (
  `idProducto` int NOT NULL AUTO_INCREMENT,
  `cantidadDisponible` int DEFAULT NULL,
  `fechaCaducidad` date DEFAULT NULL,
  `estatus` int DEFAULT '1',
  `idSabor` int NOT NULL,
  `idDetalle` int NOT NULL,
  PRIMARY KEY (`idProducto`),
  KEY `fk_sabor` (`idSabor`),
  KEY `fk_detalle` (`idDetalle`),
  CONSTRAINT `fk_detalle` FOREIGN KEY (`idDetalle`) REFERENCES `detallesproducto` (`idDetalle`) ON DELETE CASCADE,
  CONSTRAINT `fk_sabor` FOREIGN KEY (`idSabor`) REFERENCES `sabores` (`idSabor`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `productosterminados`
--

LOCK TABLES `productosterminados` WRITE;
/*!40000 ALTER TABLE `productosterminados` DISABLE KEYS */;
INSERT INTO `productosterminados` VALUES (1,150,'2025-03-30',1,2,2);
/*!40000 ALTER TABLE `productosterminados` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `proveedores`
--

DROP TABLE IF EXISTS `proveedores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `proveedores` (
  `idProveedor` int NOT NULL AUTO_INCREMENT,
  `nombreProveedor` varchar(100) DEFAULT NULL,
  `correo` varchar(100) DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `estatus` int DEFAULT '1',
  PRIMARY KEY (`idProveedor`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `proveedores`
--

LOCK TABLES `proveedores` WRITE;
/*!40000 ALTER TABLE `proveedores` DISABLE KEYS */;
INSERT INTO `proveedores` VALUES (1,'Mamá Coneja','mamaconeja@gmail.com','4777892020',1);
/*!40000 ALTER TABLE `proveedores` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `recetadetalle`
--

DROP TABLE IF EXISTS `recetadetalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recetadetalle` (
  `idRecetaDetalle` int NOT NULL AUTO_INCREMENT,
  `idReceta` int NOT NULL,
  `idMateriaPrima` int NOT NULL,
  `cantidad` decimal(10,2) NOT NULL,
  `unidadMedida` varchar(20) NOT NULL,
  PRIMARY KEY (`idRecetaDetalle`),
  KEY `idReceta` (`idReceta`),
  KEY `idMateriaPrima` (`idMateriaPrima`),
  CONSTRAINT `recetadetalle_ibfk_1` FOREIGN KEY (`idReceta`) REFERENCES `recetas` (`idReceta`) ON DELETE CASCADE,
  CONSTRAINT `recetadetalle_ibfk_2` FOREIGN KEY (`idMateriaPrima`) REFERENCES `materiasprimas` (`idMateriaPrima`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `recetadetalle`
--

LOCK TABLES `recetadetalle` WRITE;
/*!40000 ALTER TABLE `recetadetalle` DISABLE KEYS */;
/*!40000 ALTER TABLE `recetadetalle` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `recetas`
--

DROP TABLE IF EXISTS `recetas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recetas` (
  `idReceta` int NOT NULL AUTO_INCREMENT,
  `nombreReceta` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`idReceta`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `recetas`
--

LOCK TABLES `recetas` WRITE;
/*!40000 ALTER TABLE `recetas` DISABLE KEYS */;
/*!40000 ALTER TABLE `recetas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sabores`
--

DROP TABLE IF EXISTS `sabores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sabores` (
  `idSabor` int NOT NULL AUTO_INCREMENT,
  `nombreSabor` varchar(100) NOT NULL,
  PRIMARY KEY (`idSabor`),
  UNIQUE KEY `nombreSabor` (`nombreSabor`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sabores`
--

LOCK TABLES `sabores` WRITE;
/*!40000 ALTER TABLE `sabores` DISABLE KEYS */;
INSERT INTO `sabores` VALUES (9,'Avena'),(11,'Brownies'),(8,'C. Chispas'),(6,'C. Pasas'),(1,'Chocolate'),(4,'Coco'),(7,'Integrales'),(10,'Mantequilla'),(5,'Naranja'),(3,'Nuez'),(2,'Vainilla');
/*!40000 ALTER TABLE `sabores` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `idUsuario` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) DEFAULT NULL,
  `apaterno` varchar(100) DEFAULT NULL,
  `amaterno` varchar(100) DEFAULT NULL,
  `correo` varchar(100) DEFAULT NULL,
  `contrasena` varchar(255) DEFAULT NULL,
  `rol` enum('Admin','Ventas','Produccion','Cliente') DEFAULT NULL,
  `activo` tinyint DEFAULT '1',
  `ultimo_login` datetime DEFAULT NULL,
  `otp_secret` varchar(32) DEFAULT NULL,
  `otp_verified` tinyint(1) DEFAULT '0' COMMENT '0 = no verificado, 1 = verificado',
  `registration_data` text,
  PRIMARY KEY (`idUsuario`),
  UNIQUE KEY `correo` (`correo`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (1,'oscar','alvarado','cornejo','oscar@admin.com','eb61a8422ff38a595a19c9e163077fd7ebfb33799fae2135c633139940860fbd','Admin',1,'2025-04-10 18:57:11',NULL,0,NULL),(2,'Oscar','Alvarado','Cornejo','oscar@dongalleto.com','eb61a8422ff38a595a19c9e163077fd7ebfb33799fae2135c633139940860fbd','Cliente',1,'2025-03-23 15:28:09',NULL,0,NULL);
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ventas`
--

DROP TABLE IF EXISTS `ventas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ventas` (
  `idVenta` int NOT NULL AUTO_INCREMENT,
  `idUsuario` int DEFAULT NULL,
  `fecha` date DEFAULT NULL,
  `total` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`idVenta`),
  KEY `idUsuario` (`idUsuario`),
  CONSTRAINT `ventas_ibfk_1` FOREIGN KEY (`idUsuario`) REFERENCES `usuarios` (`idUsuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ventas`
--

LOCK TABLES `ventas` WRITE;
/*!40000 ALTER TABLE `ventas` DISABLE KEYS */;
/*!40000 ALTER TABLE `ventas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ventascliente`
--

DROP TABLE IF EXISTS `ventascliente`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ventascliente` (
  `idVentasCliente` int NOT NULL AUTO_INCREMENT,
  `nombreCliente` varchar(100) DEFAULT NULL,
  `nombreSabor` varchar(100) DEFAULT NULL,
  `cantidad` int DEFAULT NULL,
  `tipoProducto` varchar(100) DEFAULT NULL,
  `total` float DEFAULT NULL,
  `estatus` int DEFAULT NULL,
  PRIMARY KEY (`idVentasCliente`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ventascliente`
--

LOCK TABLES `ventascliente` WRITE;
/*!40000 ALTER TABLE `ventascliente` DISABLE KEYS */;
/*!40000 ALTER TABLE `ventascliente` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary view structure for view `vista_comprasinsumos`
--

DROP TABLE IF EXISTS `vista_comprasinsumos`;
/*!50001 DROP VIEW IF EXISTS `vista_comprasinsumos`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `vista_comprasinsumos` AS SELECT 
 1 AS `idCompra`,
 1 AS `idProveedor`,
 1 AS `idMateriaPrima`,
 1 AS `nombreProveedor`,
 1 AS `materiaPrima`,
 1 AS `cantidad`,
 1 AS `fecha`,
 1 AS `totalCompra`*/;
SET character_set_client = @saved_cs_client;

--
-- Final view structure for view `vista_comprasinsumos`
--

/*!50001 DROP VIEW IF EXISTS `vista_comprasinsumos`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vista_comprasinsumos` AS select `ci`.`idCompra` AS `idCompra`,`ci`.`idProveedor` AS `idProveedor`,`ci`.`idMateriaPrima` AS `idMateriaPrima`,`p`.`nombreProveedor` AS `nombreProveedor`,`mp`.`materiaPrima` AS `materiaPrima`,`ci`.`cantidad` AS `cantidad`,`ci`.`fecha` AS `fecha`,`ci`.`totalCompra` AS `totalCompra` from ((`comprasinsumos` `ci` join `proveedores` `p` on((`ci`.`idProveedor` = `p`.`idProveedor`))) join `materiasprimas` `mp` on((`ci`.`idMateriaPrima` = `mp`.`idMateriaPrima`))) order by `ci`.`fecha` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-04-10 22:54:50
