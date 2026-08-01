from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category

DEFAULT_CATEGORIES = [
    {"name": "Alimentação", "color": "#C45C26", "keywords": "ifood,rappi,uber eats,restaurante,padaria,supermercado,mercado,mcdonald,burger,pizza,cafe,starbucks"},
    {"name": "Assinaturas", "color": "#2F6F6A", "keywords": "netflix,spotify,disney,prime video,youtube,icloud,adobe,microsoft,openai,chatgpt,dropbox,github"},
    {"name": "Transporte", "color": "#3B6EA5", "keywords": "uber,99,cabify,shell,ipiranga,posto,combustivel,metro,onibus,estacionamento"},
    {"name": "Moradia", "color": "#6B4F3A", "keywords": "aluguel,condominio,enel,light,comgas,claro,vivo,tim,oi,agua,energia"},
    {"name": "Saúde", "color": "#B33A3A", "keywords": "farmacia,drogaria,hospital,clinica,laboratorio,unimed,amil,sulamerica,dental"},
    {"name": "Lazer", "color": "#7A5C9E", "keywords": "cinema,ingresso,steam,playstation,xbox,bar,show,teatro,viagem,hotel,airbnb"},
    {"name": "Compras", "color": "#D4A017", "keywords": "amazon,magalu,americanas,shopee,aliexpress,mercado livre,zara,renner,nike"},
    {"name": "Educação", "color": "#2E7D4F", "keywords": "udemy,coursera,alura,escola,faculdade,livro,livraria"},
    {"name": "Outros", "color": "#6B7280", "keywords": ""},
    {"name": "Não categorizado", "color": "#9CA3AF", "keywords": ""},
]


def seed_categories(db: Session) -> None:
    existing = {c.name for c in db.scalars(select(Category)).all()}
    for item in DEFAULT_CATEGORIES:
        if item["name"] in existing:
            continue
        db.add(
            Category(
                name=item["name"],
                color=item["color"],
                keywords=item["keywords"],
            )
        )
    db.commit()
