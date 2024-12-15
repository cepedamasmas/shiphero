from sqlalchemy import (
    Column,
    BigInteger,
    DateTime,
    Text,
    ForeignKey,
    Integer,
    Boolean
)
from sqlalchemy.orm import relationship
from utils.database import Base
from datetime import datetime

class SphVersion(Base):
    """
    Modelo para la tabla sph_version.
    """
    __tablename__ = "sph_version"

    sph_version_id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.now)

    # Relación con SphSnapshotInventario
    snapshots = relationship(
        "SphSnapshotInventario",
        back_populates="version",
        cascade="all, delete-orphan"
    )


class SphSnapshotInventario(Base):
    """
    Modelo para la tabla sph_snapshot_inventario.
    """
    __tablename__ = "sph_snapshot_inventario"

    sph_snapshot_inventario_id = Column(BigInteger, primary_key=True, autoincrement=True)
    sph_version_id = Column(BigInteger, ForeignKey("sph_version.sph_version_id"), nullable=False)
    snapshot_id = Column(Text, nullable=True)
    job_user_id = Column(Text, nullable=True)
    job_account_id = Column(Text, nullable=True)
    warehouse_name = Column(Text, nullable=True)
    warehouse_id = Column(Text, nullable=True)
    customer_account_id = Column(Text, nullable=True)
    notification_email = Column(Text, nullable=True)
    email_error = Column(Text, nullable=True)
    post_url = Column(Text, nullable=True)
    post_error = Column(Text, nullable=True)
    post_url_pre_check = Column(Boolean, nullable=True, default=None)
    status = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    enqueued_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    snapshot_url = Column(Text, nullable=True)
    snapshot_expiration = Column(Text, nullable=True)

    # Relación con SphVersion
    version = relationship("SphVersion", back_populates="snapshots")

    # Relación con SphInventarioDetalle
    inventario_detalle = relationship("SphInventarioDetalle", back_populates="snapshot")


class SphInventarioDetalle(Base):
    """
    Modelo para la tabla sph_inventario_detalle.
    """
    __tablename__ = "sph_inventario_detalle"

    # Cambié sph_snapshot_inventario_id a clave primaria y lo convertí en una clave foránea
    sph_inventario_detalle_id = Column(BigInteger, primary_key=True, autoincrement=True)
    sph_snapshot_inventario_id = Column(BigInteger, ForeignKey("sph_snapshot_inventario.sph_snapshot_inventario_id"))
    snapshot_id = Column(Text, nullable=True)
    warehouse_id = Column(Text, nullable=True)
    snapshot_started_at = Column(DateTime, nullable=True)
    snapshot_finished_at = Column(DateTime, nullable=True)
    sku = Column(Text, nullable=True)
    account_id = Column(Text, nullable=True)
    vendor_id = Column(Text, nullable=True)
    vendor_name = Column(Text, nullable=True)
    on_hand = Column(BigInteger, nullable=True, default=None)
    allocated = Column(BigInteger, nullable=True, default=None)
    backorder = Column(BigInteger, nullable=True, default=None)
    available = Column(BigInteger, nullable=True, default=None)
    reserve = Column(BigInteger, nullable=True, default=None)
    non_sellable = Column(BigInteger, nullable=True, default=None)

    # Relación con SphSnapshotInventario
    snapshot = relationship("SphSnapshotInventario", back_populates="inventario_detalle")


    
class SphProducto(Base):
    """
    Modelo para la tabla sph_producto.
    """
    __tablename__ = "sph_producto"

    sph_producto_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=True)
    sku = Column(Text, nullable=True)
    barcode = Column(Text, nullable=True)
    kit = Column(Boolean, default=None) 
    active = Column(Boolean, default=None)
    kit_components = Column(Text, nullable=True)



class SphTransacciones(Base):
    """
    Modelo para la tabla sph_transacciones.
    """
    __tablename__ = "sph_transacciones"

    id = Column(BigInteger, primary_key=True, autoincrement=True)  # Clave primaria opcional
    warehouse_id = Column(Text, nullable=True)
    sku = Column(Text, nullable=True)
    previous_on_hand = Column(BigInteger, nullable=True, default=None)
    change_in_on_hand = Column(BigInteger, nullable=True, default=None)
    current_on_hand = Column(BigInteger, nullable=True, default=None)
    reason = Column(Text, nullable=True)
    cycle_counted = Column(Boolean, nullable=True, default=None)
    location_id = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    location_name = Column(Text, nullable=True)
    location_zone = Column(Text, nullable=True)