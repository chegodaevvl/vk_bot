from database import Base, engine, session
from models import Category, Goods


def read_as_blob(file_name: str) -> bytes:
    """
    Функция преобразования файла с изображением в байтовый объект для сохранения в БД
    :param file_name: str - имя сохраняемого файла
    :return: bytes - набор байтов, содержимого файла
    """
    with open(file_name, 'rb') as img_file:
        blob_data = img_file.read()
    return blob_data


if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)
    category_exist = session.query(Category).all()
    if not category_exist:
        categories = [Category(name='Торты', description='Торты на любой, даже самый изысканный вкус'),
                      Category(name='Печенье', description='Мы можем сделать любое печенье, даже имбирное'),
                      Category(name='Макаруны', description='Макаруни любого цвета, но только естественного')]
        categories[0].Goods.extend([Goods(name='Мудрый еврей',
                                      description="""Торт 'Мудрый еврей' - вкусный и богатый на ингредиенты.
                                                  Собирается он из бисквита, орехов, мака, изюма.""",
                                      image=read_as_blob('img/cake1.jpg')),
                                    Goods(name='Птичье молоко',
                                          description="""Торт суфле 'Птичье молоко' отличается особой нежностью,
                                                       даже воздушностью.""",
                                          image=read_as_blob('img/cake2.jpeg'))])
        categories[1].Goods.extend([Goods(name='Печенье курабье',
                                      description="""ТДжевизли ун курабьеси. Очень нежное печенье, 
                                      которое можно встретить часто в турецких кондитерских.""",
                                      image=read_as_blob('img/cookie1.jpg')),
                                    Goods(name='Имбирное печенье',
                                          description="""Имбирное печенье – изысканная пряная ароматная выпечка. """,
                                          image=read_as_blob('img/cookie2.jpg'))])
        categories[2].Goods.extend([Goods(name='Красные макаруны',
                                      description="""Макарун - самые популярные французские печеньки, склеенные 
                                      между собой кремом.""",
                                      image=read_as_blob('img/macaruny1.jpg')),
                                    Goods(name='Черные макаруны',
                                          description="""Макарун - самые популярные французские печеньки, 
                                          склеенные между собой кремом.""",
                                          image=read_as_blob('img/macaruny2.jpg'))])
        session.add_all(categories)
        session.commit()
