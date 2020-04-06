import datetime
import logging
import os

import freezegun
import pytest
import vcr

from litresapi import LitresApi

logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def litres():
    return LitresApi(secret_key=os.environ.get('LITRES_SECRET_KEY', ''),
                     partner_id=os.environ.get('LITRES_PARTNER_ID', ''))


@pytest.fixture
def litres_xml():
    return LitresApi(secret_key=os.environ.get('LITRES_SECRET_KEY', ''),
                     partner_id=os.environ.get('LITRES_PARTNER_ID', ''), xml=True)


@vcr.use_cassette('tests/cassettes/freshbook.yaml', filter_query_parameters=['sha', 'place'])
@freezegun.freeze_time('2015-08-01 07:51:00 UTC')
def test_get_freshbook(litres):
    book_data = list(litres.get_fresh_book(start_date=datetime.datetime(2015, 7, 19, 12, 5),
                                           end_date=datetime.datetime(2015, 7, 19, 12, 10)))
    assert len(book_data) == 2

    book1 = book_data[0]
    assert book1['@id'] == '10315207'
    assert book1['@file_id'] == '13373969'
    assert book1['@cover'] == 'jpg'
    assert book1['@external_id'] == '37828892-1a76-11e5-ad6a-002590591dd6'
    assert book1['title-info']['book-title'] == 'Бросок на выстрел'

    book2 = book_data[1]
    assert book2['@id'] == '10316290'
    assert book2['title-info']['book-title'] == 'Конек-Горбунок'


@vcr.use_cassette('tests/cassettes/freshbook.yaml', filter_query_parameters=['sha', 'place'])
@freezegun.freeze_time('2015-08-01 07:51:00 UTC')
def test_get_freshbook_xml(litres_xml):
    book_data_generator = litres_xml.get_fresh_book(start_date=datetime.datetime(2015, 7, 19, 12, 5),
                                                    end_date=datetime.datetime(2015, 7, 19, 12, 10))
    book1 = next(book_data_generator)
    assert book1.attrib['external_id'] == '37828892-1a76-11e5-ad6a-002590591dd6'
    assert book1.xpath('title-info/book-title')[0].text == 'Бросок на выстрел'

    book2 = next(book_data_generator)
    assert book2.attrib['id'] == '10316290'

    with pytest.raises(StopIteration):
        next(book_data_generator)


def scrub_body(response):
    response['body']['string'] = ''.encode('utf-8')
    return response


my_vcr = vcr.VCR(before_record_response=scrub_body)


@my_vcr.use_cassette('tests/cassettes/thebook.yaml', filter_query_parameters=['md5', 'place'])
def test_get_the_book(litres):
    response = litres.get_the_book('37828892-1a76-11e5-ad6a-002590591dd6')

    assert response.status_code == 200
    content_disposition = 'attachment; filename="Suhov_E._Rassledovaniya._Brosok_Na_Vyistrel.fb2.zip"'
    assert response.headers['Content-Disposition'] == content_disposition
    assert response.headers['Content-Length'] == '452166'


@my_vcr.use_cassette('tests/cassettes/cover.yaml')
def test_get_cover(litres):
    response = litres.get_cover(book_id='32544407', file_ext='jpg')

    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'image/jpeg'


@my_vcr.use_cassette('tests/cassettes/cover.yaml')
def test_get_cover_from_book(litres):
    response = litres.get_cover(book={'@id': '32544407', '@cover': 'jpg'})

    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'image/jpeg'


def test_not_cover_for_book(litres):
    response = litres.get_cover(book={'@id': '32544407', '@cover': ''})

    assert response is None


@vcr.use_cassette('tests/cassettes/genres.yaml')
def test_get_genres(litres):
    genres_list = litres.get_genres()

    assert len(genres_list) > 15

    genre = genres_list[0]

    assert genre['@id'] == '5003'
    assert genre['@title'] == 'Бизнес-книги'
    assert genre['@type'] == 'root'
    assert len(genre['genre']) == 25


@vcr.use_cassette('tests/cassettes/genres.yaml')
def test_get_genres_xml(litres_xml):
    xml_doc = litres_xml.get_genres()
    assert xml_doc.xpath("//genre[@token='kompyuternaya_literatura_zarubezhnaya']")[0].attrib['id'] == '5221'
