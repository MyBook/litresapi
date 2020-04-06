Litres API
==========

python-обёртка вокруг API ЛитРес на базе requests и xmltodict

.. image:: https://img.shields.io/badge/python-3.5,%203.6,%203.7-blue.svg
    :target: https://pypi.python.org/pypi/litresapi/
.. image:: https://travis-ci.org/MyBook/litresapi.svg?branch=master
    :target: https://travis-ci.org/MyBook/litresapi
.. image:: https://codecov.io/gh/MyBook/litresapi/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/MyBook/litresapi
.. image:: https://img.shields.io/badge/docs-1.83-orange.svg
    :alt: Docs version
    :target: http://www.litres.ru/static/get_fresh_book.zip

`Официальная документация XML API <http://www.litres.ru/static/get_fresh_book.zip>`__

Примеры
~~~~~~~

Получить обновления книг
------------------------

.. code:: python

    from litresapi import LitresApi

    api = LitresApi(secret_key='your-secret-key', partner_id='ZZZZ')
    lazy_books = api.get_fresh_book(start_date=datetime.datetime(2015, 7, 19, 12, 5))

    >>> first_book = next(lazy_books)
    >>> print(json.dumps(first_book, indent=4, ensure_ascii=False))
    {
        "title-info": {
            "genre": "detective",
            "author": {
                "first-name": "Евгений",
                "middle-name": "Евгеньевич",
                "last-name": "Сухов",
                "id": "1212f327-2a83-102a-9ae1-2dfe723fe7c7"
            },
            ...
        }
        ...
        "@external_id": "37828892-1a76-11e5-ad6a-002590591dd6",
        "@tag": "updated-book"
        ...
    }

Вместо словарей можно работать с xml напрямую (lxml):

.. code:: python

    api = LitresApi(secret_key='your-secret-key, partner_id='ZZZZ', xml=True)
    lazy_books = api.get_fresh_book(start_date=datetime.datetime(2015, 7, 19, 12, 5))

    >>> book = next(lazy_books)
    <Element updated-book at 0x1067186c8>
    >>> book.attrib['external_id']
    '37828892-1a76-11e5-ad6a-002590591dd6'
    >>> book.getchildren()
    [<Element files at 0x10a77cd88>, <Element title-info at 0x10a77c488>, ...]

Можно предавать аргументы для трансформации ответа на базе requests hooks:

.. code:: python

    def save_xml_to_file(response, *args, **kwargs):
        with open('litres_response.xml', 'wb') as fl:
            fl.write(response.content)

    >> api.get_fresh_book(start_date=datetime.datetime(2015, 7, 19, 12, 5),
                          hooks={'response': save_xml_to_file})


Ограничения
+++++++++++

- ``api.get_fresh_book`` нельзя вызывать чаще одного раза в секунду
- время на сервере должно быть установлено верно, иначе ``timestamp`` запроса будет отвергнут

Скачать книгу
-------------
.. code:: python

    response = api.get_the_book(external_id='37828892-1a76-11e5-ad6a-002590591dd6')
    >>> response
    <Response [200]>
    >>> response.headers['Content-Disposition']
    'attachment; filename="Suhov_E._Rassledovaniya._Brosok_Na_Vyistrel.fb2.zip"'
    >>> len(response.content)
    452166

Скачать обложку
---------------

.. code:: python

    response = api.get_cover(file_id='13299029', file_ext='jpg')
    >>> response
    <Response [200]>
    >>> response.headers['Content-Type']
    'image/jpeg'
    >>> len(response.content)
    51405

Вместо ``file_id`` можно передать словарь книги из результатов генератора ``get_fresh_book``

.. code:: python

    book = next(api.get_fresh_book(start_date=datetime.datetime(2015, 7, 19, 12, 5)))
    >>> api.get_cover(book=book).headers['Content-Type']
    'image/jpeg'

Если обложки у книги нет, функция вернёт ``None``

.. code:: python

    book = next(api.get_fresh_book(uuid='ead79f60-4471-4952-aa81-5f126fb6da82'))
    >>> api.get_cover(book=book)
    None

Жанры
-----

.. code:: python

    genres = api.get_genres()
    >>> print(json.dumps(genres, indent=4, ensure_ascii=False))
    [
        {
            "@id": "5003",
            "@title": "Бизнес-книги",
            "@type": "root",
            "genre": [
                {
                    "@id": "5049",
                    "@title": "Банковское дело",
                    "@token": "bankovskoe_delo",
                    "@type": "genre"
                },
                {
                    "@id": "5047",
                    "@title": "Кадровый менеджмент",
                    "@token": "kadrovyj_menedzhment",
                    "@type": "container",
                    "genre": [
                        {
                            "@id": "5334",
                            "@title": "Аттестация персонала",
                            "@token": "attestaciya_personala",
                            "@type": "genre"
                        },
        ...
    ]

Для получения xml:

.. code:: python

    api = LitresApi(xml=True)
    genres = api.get_genres()
    >>> genres.xpath("//genre[@token='sport_fitnes']")[0].attrib['title']
    'Спорт, фитнес'

Разработка
~~~~~~~~~~

Запустить тесты
---------------

::

  tox -e py37


Публикация релиза в PyPi
------------------------

Для публикации релиза понадобится `twine <https://pypi.org/project/twine/>`_.
Для удобства его можно установить глобально::

  pip install twine

1. Поднимаем версию пакета::

    __version__ = '1.1.1'

2. Собираем пакет::

    python setup.py sdist

3. Загружаем собранный пакет в PyPi::

    twine upload dist/litresapi-1.1.1.tar.gz
