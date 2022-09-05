from database import Base, engine, session
from models import Category, Goods, StateMessage


def read_as_blob(file_name: str) -> bytes:
    """
    Функция преобразования файла с изображением в байтовый объект для сохранения в БД
    :param file_name: str - имя сохраняемого файла
    :return: bytes - набор байтов, содержимого файла
    """
    with open(file_name, 'rb') as img_file:
        blob_data = img_file.read()
    return blob_data


def read_file_content(file_name: str) -> str:
    """
    Функция считывания содержимого текстового файла для записи в БД
    :param file_name: str - имя обрабатываемого файла
    :return: str - содержание файла
    """
    with open(file_name, 'r') as text_file:
        file_content = text_file.read()
    return file_content


if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)
    category_exist = session.query(Category).all()
    if not category_exist:
        categories = [Category(name='Торты', description=read_file_content('test_data/cake.txt')),
                      Category(name='Печенье', description=read_file_content('test_data/cookie.txt')),
                      Category(name='Макаруны', description=read_file_content('test_data/macaruny.txt'))]
        categories[0].Goods.extend([Goods(name='Мудрый еврей',
                                          description=read_file_content('test_data/cake1.txt'),
                                          image=read_as_blob('test_data/cake1.jpg')),
                                    Goods(name='Птичье молоко',
                                          description=read_file_content('test_data/cake2.txt'),
                                          image=read_as_blob('test_data/cake2.jpeg'))])
        categories[1].Goods.extend([Goods(name='Печенье курабье',
                                          description=read_file_content('test_data/cookie1.txt'),
                                          image=read_as_blob('test_data/cookie1.jpg')),
                                    Goods(name='Имбирное печенье',
                                          description=read_file_content('test_data/cookie2.txt'),
                                          image=read_as_blob('test_data/cookie2.jpg'))])
        categories[2].Goods.extend([Goods(name='Красные макаруны',
                                          description=read_file_content('test_data/macaruny1.txt'),
                                          image=read_as_blob('test_data/macaruny1.jpg')),
                                    Goods(name='Черные макаруны',
                                          description=read_file_content('test_data/macaruny2.txt'),
                                          image=read_as_blob('test_data/macaruny2.jpg'))])
        state_messages = [StateMessage(state_id=0,
                                       message=read_file_content('test_data/message1.txt')),
                          StateMessage(state_id=1,
                                       message=read_file_content('test_data/message2.txt'))
                          ]
        session.add_all(categories)
        session.add_all(state_messages)
        session.commit()
