from sqlalchemy import Column, BigInteger, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class WidgetCustomization(Base):
    """Widget customization model - stores color and styling preferences"""
    
    __tablename__ = "widget_customizations"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    widget_id = Column(BigInteger, ForeignKey("widgets.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Branding
    chatbot_name = Column(String(100), nullable=False, default='Chat Support')
    
    # Color customizations
    chat_header_color = Column(String(7), nullable=False, default='#007bff')  # Hex color
    close_icon_color = Column(String(7), nullable=False, default='#ffffff')
    chat_bg_color = Column(String(7), nullable=False, default='#f8f9fa')
    ai_bubble_color = Column(String(7), nullable=False, default='#ffffff')
    human_bubble_color = Column(String(7), nullable=False, default='#007bff')
    text_box_color = Column(String(7), nullable=False, default='#ffffff')
    send_button_color = Column(String(7), nullable=False, default='#007bff')
    
    # Relationships
    widget = relationship("Widget", back_populates="customization")

