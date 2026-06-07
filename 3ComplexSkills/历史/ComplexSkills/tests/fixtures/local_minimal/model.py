from sqlalchemy import Column, Integer, String
class Project:
    id = Column(Integer)
    tenant_id = Column(String)
    owner_id = Column(Integer)
