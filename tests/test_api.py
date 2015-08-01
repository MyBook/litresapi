# coding: utf-8
import os
import datetime
import logging

import freezegun
import pytest
import vcr

from litresapi import LitresApi


logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def litres():
    return LitresApi(secret_key=os.environ.get('LITRES_SECRET_KEY', ''),
                     partner_id=os.environ.get('LITRES_PARTNER_ID', ''))


@vcr.use_cassette('tests/cassettes/freshbook.yaml', filter_query_parameters=['sha', 'place'])
@freezegun.freeze_time('2015-08-01 07:51:00 UTC')
def test_get_freshbook(litres):
    book_data = list(litres.get_fresh_book(start_date=datetime.datetime(2015, 7, 19, 12, 5),
                                           end_date=datetime.datetime(2015, 7, 19, 12, 10)))
    assert len(book_data) == 2

    book1 = book_data[0]
    assert book1['@id'] == '10315207'
    assert book1['@external_id'] == '37828892-1a76-11e5-ad6a-002590591dd6'
    assert book1['title-info']['book-title'] == u'Бросок на выстрел'

    book2 = book_data[1]
    assert book2['@id'] == '10316290'
    assert book2['title-info']['book-title'] == u'Конек-Горбунок'


@vcr.use_cassette('tests/cassettes/freshbook.yaml', filter_query_parameters=['sha', 'place'])
@freezegun.freeze_time('2015-08-01 07:51:00 UTC')
def test_get_freshbook_xml(litres):
    litres.response_as_dict = False
    book_data_generator = litres.get_fresh_book(start_date=datetime.datetime(2015, 7, 19, 12, 5),
                                                end_date=datetime.datetime(2015, 7, 19, 12, 10))
    book1 = next(book_data_generator)
    assert book1.attrib['external_id'] == '37828892-1a76-11e5-ad6a-002590591dd6'
    assert book1.xpath('title-info/book-title')[0].text == u'Бросок на выстрел'

    book2 = next(book_data_generator)
    assert book2.attrib['id'] == '10316290'

    with pytest.raises(StopIteration):
        next(book_data_generator)


def scrub_body(response):
    response['body']['string'] = u''.encode('utf-8')
    return response

my_vcr = vcr.VCR(before_record_response=scrub_body)


@my_vcr.use_cassette('tests/cassettes/thebook.yaml', filter_query_parameters=['md5', 'place'])
def test_get_the_book(litres):
    response = litres.get_the_book('37828892-1a76-11e5-ad6a-002590591dd6')

    assert response.status_code == 200
    assert response.headers['Content-Disposition'] == 'attachment; filename="Suhov_E._Rassledovaniya._Brosok_Na_Vyistrel.fb2.zip"'  # noqa
    assert response.headers['Content-Length'] == '452166'
