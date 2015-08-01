Litres API
==========

python-обёртка вокруг API ЛитРес на базе requests и xmltodict

.. image:: https://img.shields.io/badge/python-2.7,%203.4-blue.svg
    :alt: python 2.7, python 3.4

Примеры
~~~~~~~

Получить обновления книг
------------------------

::

    from litresapi import LitresApi

    api = LitresApi(secret_key='your-secret-key', partner_id='ZZZZ')
    lazy_books = api.get_fresh_book(start_date=datetime.datetime(2015, 7, 19, 12, 5))

    >>> first_book = next(lazy_books)
    >>> print json.dumps(first_book, indent=4, ensure_ascii=False)
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

Вместо словарей можно работать с xml напрямую (lxml)::

    api = LitresApi(secret_key='your-secret-key, partner_id='ZZZZ', xml=True)
    lazy_books = api.get_fresh_book(start_date=datetime.datetime(2015, 7, 19, 12, 5))

    >>> book = next(lazy_books)
    <Element updated-book at 0x1067186c8>
    >> book.attrib['external_id']
    '37828892-1a76-11e5-ad6a-002590591dd6'
    >> book.getchildren()
    [<Element files at 0x10a77cd88>, <Element title-info at 0x10a77c488>, ...]

Ограничения
+++++++++++

- `api.get_fresh_book` нельзя вызывать чаще одного раза в секунду
- время на сервере должно быть установлено верно, иначе `timestamp` запроса будет отвергнут

Скачать книгу
-------------
::

    response = api.get_the_book(external_id='37828892-1a76-11e5-ad6a-002590591dd6')
    >> response
    <Response [200]>
    >> response.headers['Content-Disposition']
    'attachment; filename="Suhov_E._Rassledovaniya._Brosok_Na_Vyistrel.fb2.zip"'
    >> len(response.content)
    452166
