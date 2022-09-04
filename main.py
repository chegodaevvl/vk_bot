from decouple import config
from vk_api import VkApi, VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from random import randint
from database import Base, engine, session
from model import UserState, Category, Goods


keyboard = {'inline': True,
            'buttons': []}

button = {'action': {'type': 'text',
                     'label': 'Назад'},
          'color': 'default'}


bot_id = config('bot_uid')
vk_bot = VkApi(token=bot_id)
upload_method = VkUpload(vk_bot)
msg_poll = VkLongPoll(vk_bot)


def check_user_state(user_id):
    user_state = session.query(UserState).filter_by(user_id=user_id).first()
    if not user_state:
        user_state = UserState(user_id=user_id, state=0)
        session.add(user_state)
        session.commit()
        return 0
    return user_state.state


def user_next_state(user_id, category_name=None):
    user_state = session.query(UserState).filter_by(user_id=user_id).first()
    if user_state:
        user_state.state += 1
        print(category_name)
        if category_name:
            category = session.query(Category).filter_by(name=category_name).first()
            user_state.category_id = category.id
    session.commit()


def user_prev_state(user_id):
    user_state = session.query(UserState).filter_by(user_id=user_id).first()
    if user_state:
        user_state.state -= 1
    session.commit()


def get_categories():
    categories = session.query(Category).all()
    if categories:
        return list(category.name for category in categories)


def get_category_name_by_id(cat_id):
    category = session.query(Category).filter_by(id=cat_id).first()
    if category:
        return category.name


def get_all_goods():
    goods = session.query(Goods).all()
    if goods:
        return list(item.name for item in goods)


def get_goods_by_category(user_id):
    user = session.query(UserState).filter_by(user_id=user_id).first()
    if user:
        category_id = user.category_id
        goods = session.query(Goods).filter_by(category_id=category_id).all()
        return goods, get_category_name_by_id(category_id)


def get_goods_by_name(goods_name):
    goods = session.query(Goods).filter_by(name=goods_name).first()
    return goods


def first_step(user_id):
    user_next_state(user_id)
    vk_bot.method('messages.send', {'peer_id': user_id,
                                    'message': 'Привет, дорогой\nКак дела?',
                                    'random_id': randint(0, 2048)})


def second_step(user_id):
    user_next_state(user_id)
    main_keyboard = VkKeyboard(one_time=False)
    main_keyboard.add_button('Посмотреть нашу витрину')
    vk_bot.method('messages.send', {'peer_id': user_id,
                                    'message': 'Вы можете ознакомиться с нашим ассортиментом',
                                    'keyboard': main_keyboard.get_keyboard(),
                                    'random_id': randint(0, 2048)})


def third_step(user_id):
    category_keyboard = VkKeyboard(one_time=False)
    for category in categories:
        category_keyboard.add_button(category)
    category_keyboard.add_button('Назад к описанию сообщества')
    vk_bot.method('messages.send', {'peer_id': user_id,
                                    'keyboard': category_keyboard.get_keyboard(),
                                    'message': 'Вот что мы могем:',
                                    'random_id': randint(0, 2048)})


def forth_step(user_id):
    goods_keyboard = VkKeyboard(one_time=False)
    goods, category_name = get_goods_by_category(user_id)
    for item in goods:
        goods_keyboard.add_button(item.name)
    goods_keyboard.add_button('Назад к выбору категорий')
    vk_bot.method('messages.send', {'peer_id': user_id,
                                    'keyboard': goods_keyboard.get_keyboard(),
                                    'message': f'Вот наши {category_name}:',
                                    'random_id': randint(0, 2048)})


def fifth_step(user_id, goods_name):
    goods = get_goods_by_name(goods_name)
    back_keyboard = VkKeyboard(one_time=False)
    back_keyboard.add_button('Назад к выбору товаров')
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


def main():
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
                elif current_step == 3:
                    forth_step(user_id)
                else:
                    fifth_step(user_id, msg_text)


categories = get_categories()
goods_list = get_all_goods()


if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)

    main()
