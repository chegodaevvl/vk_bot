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


def get_user(user_id: int) -> UserState:
    """
    Функция получения экземпляра объекта UserState со всей необходимой информацией о текущем пользователе.
    Данные о состоянии чата с пользователем хранятся в БД
    :param user_id: int - Идентификатор пользователя из чата в ВК
    :return: экземпляр объекта UserState - Полное описание пользователя и его характеристик
    """
    user_state = session.query(UserState).filter_by(user_id=user_id).first()
    if not user_state:
        user_state = UserState(user_id=user_id, state=0)
        session.add(user_state)
        session.commit()
    return user_state


def user_next_state(user_state: UserState, category_name: str = None) -> None:
    """
    Функция перевода состояния чата с пользователем на следующий шаг. При переходе на шаг с выбором категории товара
    также происходит сохранение идентификатора выбранной категории, чтобы обеспечить корректную работу чата при его
    возобновлении
    :param user_state: UserState - Экземпляр объекта UserState
    :param category_name: str - Наименование выбранной категории, которое предобразуетс я в id, чтобы в дальнейшем
                                обеспечить корркетное возобновление работы чата.
    """
    user_state.state += 1
    if category_name:
        category = session.query(Category).filter_by(name=category_name).first()
        user_state.category_id = category.id
    session.commit()


def user_prev_state(user_state: UserState) -> None:
    """
    Функция перевода чата с пользователем на предыдущий шаг
    :param user_state: UserState - Объект UserState, описывающий текущего пользователя
    """
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


def get_goods_by_category(category_id: int) -> tuple[list, str]:
    """
    Функция получения перечня товаров, выбранной категории и ее наименивания
    :param category_id: int - идентификатор активной категории
    :return: tuple [list - список товаров выбранной категории, str - наименование категории]
    """
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


def first_step(user_state: UserState) -> None:
    """
    Отрпавка приветственного сообщения на первом шаге работы мастера. Отображение клавиатуры для показа ассортимента
    пекарни (переченя категорий товаров)
    :param user_state: UserState - экземпляр объекта UserState, описывающий текущего пользователя
    """
    user_next_state(user_state)
    main_keyboard = VkKeyboard(one_time=False)
    main_keyboard.add_button('Ознакомиться с ассортиментом', color=VkKeyboardColor.PRIMARY)
    vk_bot.method('messages.send', {'peer_id': user_state.user_id,
                                    'message': get_message_step(0),
                                    'keyboard': main_keyboard.get_keyboard(),
                                    'random_id': randint(0, 2048)})


def second_step(user_state: UserState) -> None:
    """
    Отображение перечня категорий товаров в виде меню из кнопок с названиями категорий. Также отображается кнопка
    возврата к описанию сообщества.
    :param user_state: UserState - Объект UserState, описывающий текущего пользователя
    """
    category_keyboard = VkKeyboard(one_time=False)
    for category in categories:
        category_keyboard.add_button(category.capitalize(), color=VkKeyboardColor.PRIMARY)
        category_keyboard.add_line()
    category_keyboard.add_button('Назад к описанию сообщества', color=VkKeyboardColor.SECONDARY)
    vk_bot.method('messages.send', {'peer_id': user_state.user_id,
                                    'message': get_message_step(1),
                                    'keyboard': category_keyboard.get_keyboard(),
                                    'random_id': randint(0, 2048)})


def third_step(user_state: UserState) -> None:
    """
    Отображение меню выбора товара из выбранной категории в виде кнопок и кнопки возврата в предыдущее меню.
    :param user_state: UserState - Объект UserState, описывающий текущего пользователя
    """
    goods_keyboard = VkKeyboard(one_time=False)
    goods, category = get_goods_by_category(user_state.category_id)
    for item in goods:
        goods_keyboard.add_button(item.name.capitalize(), color=VkKeyboardColor.PRIMARY)
        goods_keyboard.add_line()
    goods_keyboard.add_button('Назад к выбору категорий', color=VkKeyboardColor.SECONDARY)
    vk_bot.method('messages.send', {'peer_id': user_state.user_id,
                                    'keyboard': goods_keyboard.get_keyboard(),
                                    'message': category.description,
                                    'random_id': randint(0, 2048)})


def forth_step(user_state: UserState, goods_name: str) -> None:
    """
    Отображение информации о товаре: наименование товара, описание товара, изображение товара
    :param user_state: UserState - Объект UserState, описывающий текущего пользователя
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
    vk_bot.method('messages.send', {'peer_id': user_state.user_id,
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
                current_user = get_user(event.user_id)
                msg_text = event.text
                if 'назад' in msg_text.lower():
                    user_prev_state(current_user)
                if msg_text in categories:
                    user_next_state(current_user, category_name=msg_text)
                if msg_text in goods_list:
                    user_next_state(current_user)
                if current_user.state == 0:
                    first_step(current_user)
                elif current_user.state == 1:
                    second_step(current_user)
                elif current_user.state == 2:
                    third_step(current_user)
                else:
                    forth_step(current_user, msg_text)


categories = get_categories()
goods_list = get_all_goods()


if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)
    main()
