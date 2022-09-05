from decouple import config
from vk_api import VkApi, VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from random import randint
from database import Base, engine, session
from models import UserState, Category, Goods, StateMessage


bot_id = config('bot_uid')
vk_bot = VkApi(token=bot_id)
upload_method = VkUpload(vk_bot)
msg_poll = VkLongPoll(vk_bot)


def check_user_state(user_id: int) -> int:
    """
    Функция получения состояния (номера шага) чата с пользователем.
    Данные о состоянии чата с пользователем хранятся в БД
    :param user_id: int - Идентификатор пользователя из чата в ВК
    :return: sate: int - Состояние (номер шага) чата с пользователем
    """
    user_state = session.query(UserState).filter_by(user_id=user_id).first()
    if not user_state:
        user_state = UserState(user_id=user_id, state=0)
        session.add(user_state)
        session.commit()
        return 0
    return user_state.state


def user_next_state(user_id: int, category_name: str =None) -> None:
    """
    Функция перевода состояния чата с пользователем на следующий шаг. При переходе на шаг с выбором категории товара
    также происходит сохранение идентификатора выбранной категории, чтобы обеспечить корректную работу чата при его
    возобновлении
    :param user_id: int - Идентификатор пользователя, с которым ведется чат
    :param category_name: str - Наименование выбранной категории, которое предобразуетс я в id, чтобы в дальнейшем
                                обеспечить корркетное возобновление работы чата.
    """
    user_state = session.query(UserState).filter_by(user_id=user_id).first()
    if user_state:
        user_state.state += 1
        print(category_name)
        if category_name:
            category = session.query(Category).filter_by(name=category_name).first()
            user_state.category_id = category.id
    session.commit()


def user_prev_state(user_id: int) -> None:
    """
    Функция перевода чата с пользователем на предыдущий шаг
    :param user_id:
    :return:
    """
    user_state = session.query(UserState).filter_by(user_id=user_id).first()
    if user_state:
        user_state.state -= 1
    session.commit()


def get_categories() -> list:
    """
    Функция получения перечня всех категорий товаров, которые есть в БД
    :return: list - список названий категорий товаров, которые есть в БД
    """
    categories = session.query(Category).all()
    if categories:
        return list(category.name for category in categories)


def get_category_by_id(cat_id: int) -> any:
    """
    Функция получения названия категории по идентификатору
    :param cat_id: int - идентификатор категории
    :return: Category object - категорию из БД или None, если данных в БД нет
    """
    category = session.query(Category).filter_by(id=cat_id).first()
    if not category:
        return None
    return category


def get_all_goods() -> list:
    """
    Функция получения полного списка наименования товаров из БД
    :return: list - полный список наименований товаров из БД
    """
    goods = session.query(Goods).all()
    if goods:
        return list(item.name for item in goods)


def get_goods_by_category(user_id: int) -> tuple[list, str]:
    """
    Функция получения перечня товаров, выбранной категории и ее наименивания
    :param user_id: int - идентификатор пользователя, с которым ведется чат
    :return: tuple [list - список товаров выбранной категории, str - наименование категории]
    """
    user = session.query(UserState).filter_by(user_id=user_id).first()
    if user:
        category_id = user.category_id
        goods = session.query(Goods).filter_by(category_id=category_id).all()
        return goods, get_category_by_id(category_id)


def get_goods_by_name(goods_name: str) -> Goods:
    """
    Получение товара по наименованию
    :param goods_name: str - наименование товара
    :return: Goods - экземпляр модели Goods, содержащая всю информацию о товаре
    """
    goods = session.query(Goods).filter_by(name=goods_name).first()
    return goods


def get_message_step(step_id: int) -> any:
    """
    Получение текста сообщения для отображения на определенном шаге работы чата.
    :param step_id: int - номер шага чата
    :return: str - сообщение для чата или None, если запись не найдена
    """
    message = session.query(StateMessage).filter_by(state_id=step_id).first()
    if not message:
        return None
    return message.message


def first_step(user_id: int) -> None:
    """
    Отрпавка приветственного сообщения на первом шаге работы мастера. Отображение клавиатуры для показа ассортимента
    пекарни (переченя категорий товаров)
    :param user_id: int - Идентификатор пользователя из чата
    """
    user_next_state(user_id)
    main_keyboard = VkKeyboard(one_time=False)
    main_keyboard.add_button('Ознакомиться с ассортиментом', color=VkKeyboardColor.PRIMARY)
    vk_bot.method('messages.send', {'peer_id': user_id,
                                    'message': get_message_step(0),
                                    'keyboard': main_keyboard.get_keyboard(),
                                    'random_id': randint(0, 2048)})


def second_step(user_id: int) -> None:
    """
    Отображение перечня категорий товаров в виде меню из кнопок с названиями категорий. Также отображается кнопка
    возврата к описанию сообщества.
    :param user_id: int - Идентификатор пользователя, с которым инициирован чат
    """
    category_keyboard = VkKeyboard(one_time=False)
    for category in categories:
        category_keyboard.add_button(category.capitalize(), color=VkKeyboardColor.PRIMARY)
    category_keyboard.add_button('Назад к описанию сообщества', color=VkKeyboardColor.SECONDARY)
    vk_bot.method('messages.send', {'peer_id': user_id,
                                    'message': get_message_step(1),
                                    'keyboard': category_keyboard.get_keyboard(),
                                    'random_id': randint(0, 2048)})


def third_step(user_id: int) -> None:
    """
    Отображение меню выбора товара из выбранной категории в виде кнопок и кнопки возврата в предыдущее меню.
    :param user_id:
    :return:
    """
    goods_keyboard = VkKeyboard(one_time=False)
    goods, category = get_goods_by_category(user_id)
    for item in goods:
        goods_keyboard.add_button(item.name.capitalize(), color=VkKeyboardColor.PRIMARY)
    goods_keyboard.add_button('Назад к выбору категорий', color=VkKeyboardColor.SECONDARY)
    vk_bot.method('messages.send', {'peer_id': user_id,
                                    'keyboard': goods_keyboard.get_keyboard(),
                                    'message': category.description,
                                    'random_id': randint(0, 2048)})


def forth_step(user_id: int, goods_name: str) -> None:
    """
    Отображение информации о товаре: наименование товара, описание товара, изображение товара
    :param user_id: int - Идентификатор пользоателя из чата
    :param goods_name: str - Наименование товара
    """
    goods = get_goods_by_name(goods_name)
    back_keyboard = VkKeyboard(one_time=False)
    back_keyboard.add_button('Назад к выбору товаров', color=VkKeyboardColor.SECONDARY)
    with open('image.jpg', 'wb') as img_file:
        img_file.write(goods.image)
        photo = upload_method.photo_messages('image.jpg')
        owner_id = photo[0]['owner_id']
        photo_id = photo[0]['id']
        access_key = photo[0]['access_key']
        attachment = f'photo{owner_id}_{photo_id}_{access_key}'
    vk_bot.method('messages.send', {'peer_id': user_id,
                                    'message': f'{goods.name}\n{goods.description}',
                                    'attachment': attachment,
                                    'keyboard': back_keyboard.get_keyboard(),
                                    'random_id': randint(0, 2048)})


def main() -> None:
    """
    Основная функция обработки сообщений пользователя из чата ВК
    """
    for event in msg_poll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                user_id = event.user_id
                msg_text = event.text
                if 'назад' in msg_text.lower():
                    user_prev_state(user_id)
                if msg_text in categories:
                    user_next_state(user_id, category_name=msg_text)
                if msg_text in goods_list:
                    user_next_state(user_id)
                current_step = check_user_state(user_id)
                print(current_step)
                if current_step == 0:
                    first_step(user_id)
                elif current_step == 1:
                    second_step(user_id)
                elif current_step == 2:
                    third_step(user_id)
                else:
                    forth_step(user_id, msg_text)


categories = get_categories()
goods_list = get_all_goods()


if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)
    main()
